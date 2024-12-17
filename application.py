import config
from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

app = FastAPI()

client = MongoClient(config.MONGODB_CONNECTION_STRING)
db = client["svitlo"]
collection = db["schedules"]


class CityResponse(BaseModel):
    cities: List[str]


class QueuesResponse(BaseModel):
    city: str
    queues: List[str]


class ScheduleResponse(BaseModel):
    city: str
    queue: str
    date: str
    schedule: Dict[str, bool]


@app.get("/cities", response_model=CityResponse)
async def get_available_cities():
    try:
        cities = collection.distinct("City")
        if not cities:
            raise HTTPException(status_code=404, detail="No cities found")
        return {"cities": cities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/queues", response_model=QueuesResponse)
async def get_queues_by_city(city: str):
    try:
        datetime_now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        document = collection.find_one(
            {"City": city, "Date": datetime_now},
            {"_id": 0, "City": 1, "Queues": 1}
        )
        if not document:
            raise HTTPException(status_code=404, detail=f"No queues found for city: {city}")
        queue_names = list(document["Queues"].keys())
        return {"city": document["City"], "queues": queue_names}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/schedule", response_model=ScheduleResponse)
async def get_schedule(
        city: str,
        queue: str,
        date: Optional[str] = Query(default=None, description="Date in YYYY-MM-DD format")
):
    try:
        if date:
            try:
                query_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
        else:
            query_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        document = collection.find_one(
            {"City": city, "Date": query_date},
            {"_id": 0, "City": 1, "Queues": 1}
        )
        if not document:
            raise HTTPException(status_code=404, detail=f"No data found for city: {city} on date: {query_date.date()}")

        queues = document.get("Queues", {})
        if queue not in queues:
            raise HTTPException(status_code=404, detail=f"Queue '{queue}' not found in city: {city}")

        return {
            "city": document["City"],
            "queue": queue,
            "date": query_date.strftime("%Y-%m-%d"),
            "schedule": queues[queue]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
