from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json, os
from redis_om import get_redis_connection, HashModel
import consumers

app = FastAPI()
host = os.getenv("HOST")
port = os.getenv("PORT", 14405)
password = os.getenv("PASSWORD")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

redis = get_redis_connection(
    host=host,
    port=port,
    password=password,
    decode_responses=True,
)


class Delivery(HashModel):
    budget: int = 0
    notes: str = ""

    class Meta:
        database = redis


class Event(HashModel):
    delivery_id: str = None
    type: str
    data: str

    class Meta:
        database = redis


@app.get("/delivery/{pk}/state")
async def get_state(pk: str):
    state = redis.get(f"delivery:{pk}")

    if state is not None:
        return json.loads(state)

    return {}


@app.post("/delivery/create")
async def create(req: Request):
    body = await req.json()
    delivery = Delivery(
        budget=body["data"]["budget"], notes=body["data"]["notes"]
    ).save()
    event = Event(
        delivery_id=delivery.pk, type=body["type"], data=json.dumps(body["data"])
    ).save()

    state = consumers.create_delivery({}, event)

    # set the redis cache
    redis.set(f"delivery: {delivery.pk}", json.dumps(state))

    return state


async def dispatch(req: Request):
    pass
