import aiohttp
import asyncio
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import httpx
from typing import Dict, List
from fastapi import HTTPException

from utils import data_dict
#from utils import redis_client

RATES_API_URL = "https://www.nationalbank.kz/rss/get_rates.cfm"
CURRENCY_DATE_FORMAT = "%d.%m.%Y"
CURRENCY_UPDATE_HOUR = 12


async def get_exchange_rates() -> Dict:
    today = datetime.now().date()
    rates_api_url = f"{RATES_API_URL}?fdate={today.strftime('%d.%m.%Y')}"
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(rates_api_url)
    root = ET.fromstring(response.content)

    for item in root.findall(".//item"):
        currency = item.find("title").text.strip()
        rate = item.find("description").text.strip()
        data_dict[currency] = float(rate)
    return data_dict

async def update_currency_rates():
    while True:
        now = datetime.utcnow()
        next_update = datetime(now.year, now.month, now.day, CURRENCY_UPDATE_HOUR)
        if now >= next_update:
            next_update += timedelta(days=1)
        time_to_wait = (next_update - now).seconds + 1

        await asyncio.sleep(time_to_wait)
        await get_exchange_rates()

async def convert_currency(item: Dict, currency: str) -> Dict:
    price = item["pricing"]["total"]
    item_currency = item["pricing"]["currency"]
    if item_currency == currency:
        return item
    if item_currency not in data_dict:
        raise HTTPException(status_code=400, detail="Invalid currency specified")
    item_rate = data_dict[item_currency]
    if currency == 'KZT':
        new_price = round((float(price) * item_rate), 2)
    else:
        currency_rate = data_dict[currency]
        mense_price = round((float(price) * item_rate), 2)
        new_price = round((float(mense_price)) / currency_rate, 2)
    item["price"] = {"amount": str(new_price), "currency": currency}
    return item



    