from fastapi import FastAPI
from sqlmodel import SQLModel

from database.connection import engine
import backend.models

from backend.routers import router


app = FastAPI()


@app.on_event("startup")
def startup():
    SQLModel.metadata.create_all(engine)


app.include_router(router)