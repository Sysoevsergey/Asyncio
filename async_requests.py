import asyncio
import aiohttp
from more_itertools import chunked
from models import SwapiPeople, init_orm, close_orm, Session
from sqlalchemy import delete

MAX_REQUEST_SIZE = 5
BASE_URL = 'https://swapi.dev/api/people/'


async def get_people(person_id, session: aiohttp.ClientSession):
    http_response = await session.get(f'{BASE_URL}{person_id}/')
    json_data = await http_response.json()
    if json_data.get("detail") == "Not found":
        return None
    json_data["id"] = person_id
    return json_data

async def clear_database():
    async with Session() as session:
        await session.execute(delete(SwapiPeople))
        await session.commit()

async def main():
    await init_orm()
    await clear_database()
    async with aiohttp.ClientSession() as session:
        for ids_chunk in chunked(range(1, 101), MAX_REQUEST_SIZE):
            coros = [get_people(i, session) for i in ids_chunk]
            results = await asyncio.gather(*coros)
            validate_results = [result for result in results if result is not None]
            insert_coro = insert_results(validate_results)
            asyncio.create_task(insert_coro)
    tasks = asyncio.all_tasks()
    current_task = asyncio.current_task()
    tasks.remove(current_task)
    await asyncio.gather(*tasks)
    await close_orm()


async def insert_results(results: list[dict]):
    async with Session() as session:
        orm_objs = [
            SwapiPeople(
                **{
                    'id': result.get("id"),
                    'birth_year': result.get("birth_year"),
                    'eye_color': result.get("eye_color"),
                    'films': ", ".join(result.get("films", [])),
                    'gender': result.get("gender"),
                    'hair_color': result.get("hair_color"),
                    'height': result.get("height"),
                    'homeworld': result.get("homeworld"),
                    'mass': result.get("mass"),
                    'name': result.get("name"),
                    'skin_color': result.get("skin_color"),
                    'species': ", ".join(result.get("species", [])),
                    'starships': ", ".join(result.get("starships", [])),
                    'vehicles': ", ".join(result.get("vehicles", [])),
                }
            )
            for result in results
        ]
        session.add_all(orm_objs)
        await session.commit()
