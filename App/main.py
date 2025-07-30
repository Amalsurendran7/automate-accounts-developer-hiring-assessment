from contextlib import asynccontextmanager
from typing import AsyncIterator, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.endpoints import receipt
from db.base import create_db_and_tables


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[dict[str, Any]]:
    print("server is starting")
 
    create_db_and_tables()
   
    print("server is shutting down")


app = FastAPI(lifespan=lifespan)

origins = ["*"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(receipt.router, tags=["receipt"])


