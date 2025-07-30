from contextlib import asynccontextmanager
from typing import AsyncIterator, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.endpoints import receipt
from db.base import create_db_and_tables


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # Changed return type
    print("server is starting")
    create_db_and_tables()
    yield  # This is crucial - yields control to FastAPI
    print("server is shutting down")





# CORS origins configuration
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://yourdomain.com",  # Replace with your actual domain
]

# Create FastAPI application
app = FastAPI(
    title="Receipt Management API",
    description="A comprehensive API for managing receipts and transactions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type", 
        "Authorization", 
        "Accept", 
        "Origin", 
        "X-Requested-With"
    ],
    expose_headers=["X-Total-Count"],  # If you need to expose custom headers
)






app.include_router(receipt.router, tags=["receipt"])


