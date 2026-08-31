from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.connection import Base, engine

# Models
from app.models import User, ChatHistory

# Routers
from app.routers.chat import router as chat_router
from app.routers import chat_history
from app.auth.router import router as auth_router
from app.routers.user import router as user_router

# NEW - Upload Router
from app.routers.upload import router as upload_router

# Services
from app.services.csv_service import csv_service
from app.services.data_analysis_service import analysis_service
from app.services.csv_ai_service import csv_ai_service


# ==========================================
# Create database tables
# ==========================================

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="ESS AI Web Assistant",
    description="AI-powered assistant for Ethiopia Statistical Service",
    version="1.0.0"
)


# ==========================================
# CORS Configuration
# ==========================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ==========================================
# Routers
# ==========================================

# Authentication
app.include_router(auth_router)

# Users
app.include_router(user_router)

# AI Chat
app.include_router(chat_router)

# Chat History
app.include_router(chat_history.router)

# NEW - Upload
app.include_router(upload_router)


# ==========================================
# Root
# ==========================================

@app.get("/")
def root():

    return {
        "message": "Welcome to ESS AI Web Assistant"
    }


# ==========================================
# CSV Endpoints
# ==========================================

@app.get("/csv/info/{name}")
def csv_info(name: str):

    return csv_service.get_info(name)


@app.get("/csv/list")
def csv_list():

    return csv_service.list_datasets()


@app.get("/csv/unique/{dataset}/{column}")
def unique_values(
    dataset: str,
    column: str
):

    df = csv_service.get_dataset(dataset)

    if df is None:
        return {
            "error": "Dataset not found"
        }

    return analysis_service.unique_values(
        df,
        column
    )


@app.get("/csv/count/{dataset}")
def count_dataset(dataset: str):

    df = csv_service.get_dataset(dataset)

    if df is None:
        return {
            "error": "Dataset not found"
        }

    return analysis_service.count_rows(df)


@app.get("/csv/max/{dataset}/{column}")
def maximum(
    dataset: str,
    column: str
):

    df = csv_service.get_dataset(dataset)

    if df is None:
        return {
            "error": "Dataset not found"
        }

    return analysis_service.max_value(
        df,
        column
    )


@app.get("/csv/min/{dataset}/{column}")
def minimum(
    dataset: str,
    column: str
):

    df = csv_service.get_dataset(dataset)

    if df is None:
        return {
            "error": "Dataset not found"
        }

    return analysis_service.min_value(
        df,
        column
    )


@app.get("/csv/ask")
def ask_csv(question: str):

    return csv_ai_service.answer(question)