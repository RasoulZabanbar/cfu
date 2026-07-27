from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from tortoise.contrib.fastapi import RegisterTortoise
from dispatchers import router
from boot.tortoise import TORTOISE_ORM

from proccesors.messages import message_proccesor
from proccesors.callbacks import handle_callback

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with RegisterTortoise(
        app,
        config=TORTOISE_ORM,
    ):

        yield



app = FastAPI(lifespan=lifespan)

app.include_router(router)

@app.post("/router")
async def webhook(request: Request):
    update = await request.json()
    print("Received update:", update)
 
    if "message" in update:
        message = update["message"]
 
        await message_proccesor(message)
    elif "callback_query" in update:
        callback = update["callback_query"]
        await handle_callback(callback)
    else:
        pass
