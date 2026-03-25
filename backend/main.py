from fastapi import FastAPI
from sqlmodel import SQLModel
from fastapi.middleware.cors import CORSMiddleware
from backend.mqtt.client import start


from database.connection import engine
import backend.models

from backend.routers import router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    print("FASTAPI STARTUP")
    SQLModel.metadata.create_all(engine)
    start()



app.include_router(router)