import asyncio
import redis
import datetime
import httpx
import json
import os
import uvicorn
import uuid
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

from typing import Dict, List
from fastapi import FastAPI, HTTPException

from utils import data_dict
from currency import convert_currency, get_exchange_rates, update_currency_rates

from dotenv import load_dotenv


load_dotenv()

app = FastAPI()


PROVIDER_A_URL = os.getenv('PROVIDER_A_URL')
PROVIDER_B_URL = os.getenv('PROVIDER_B_URL')


exchange_rates = {}
    

@app.on_event("startup")
async def startup_event():
    await get_exchange_rates()
    asyncio.create_task(update_currency_rates())

async def fetch_response(provider_url: str) -> Dict:
    """Helper function to fetch response from provider service"""
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(provider_url)
    return response.json()

async def get_search(search_id: str) -> Dict:
    if search_id in data_dict:
        if data_dict[search_id]["status"] == "COMPLETED":
            return
        elif data_dict[search_id]["status"] == "PENDING":
            return {"search_id": search_id, "status": "PENDING", "items": data_dict[search_id]["items"]}
    data_dict[search_id] = {"search_id": search_id , "status": "PENDING", "items": []}
    results = []
    tasks = [
        asyncio.create_task(fetch_response(PROVIDER_A_URL)),
        asyncio.create_task(fetch_response(PROVIDER_B_URL))
    ]
    for task in tasks:
        task_result = await task
        if task_result:
            results.extend(task_result)
            if len(results) > 0:
                data_dict[search_id] = {"search_id": search_id, "status": "PENDING", "items": results}
    if len(results) == 0:
        raise HTTPException(status_code=404, detail="No results found")
    elif len(results) == len(tasks):
        data_dict[search_id] = {"search_id": search_id, "status": "COMPLETED", "items": results}
    return {"search_id": search_id, "status": "PENDING", "items": data_dict[search_id]["items"]}

@app.get("/results/{search_id}/{currency}")
async def get_results(search_id: str, currency: str) -> Dict:
    """Function to retrieve and return search results from Redis"""
    if search_id not in data_dict:
        return {"search_id": search_id, "status": "PENDING", "items": []}
    search_results = data_dict[search_id]
    if search_results['items'] == []:
        return search_results
    if not search_results:
        raise HTTPException(status_code=404, detail="No results found")
    status = "COMPLETED"
    results = []
    for result in search_results['items']:
        #item = json.loads(result)
        converted_item = await convert_currency(result, currency)
        results.append(converted_item)
        if "error" in converted_item:
            status = "ERROR"
    sorted_results = sorted(results, key=lambda x: x["price"]["amount"])

    return {"search_id": search_id, "status": status, "items": sorted_results}

@app.post("/search")
async def search() -> Dict[str, str]:
    """Function to initiate a search and return a unique search ID"""
    search_id = str(uuid.uuid4())
    asyncio.create_task(get_search(search_id))
    #await get_search(search_id)
    return {"search_id": search_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=9000, reload=True)