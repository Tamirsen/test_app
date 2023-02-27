import asyncio
import json
import os
from dotenv import load_dotenv

from fastapi import FastAPI

load_dotenv()

app = FastAPI()

path_to_file = os.getenv('PATH')

async def fetch_response(file_path: str, delay: int) -> dict:
    await asyncio.sleep(delay)
    with open(file_path) as f:
        response = json.load(f)
    return response

@app.post("/search")
async def search(file_path: str = path_to_file):
    delay = 60
    response = await fetch_response(file_path, delay)
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001)