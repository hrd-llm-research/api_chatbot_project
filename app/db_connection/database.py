from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

import os

load_dotenv()

_HOST = os.environ.get('PGVECTOR_HOST')
_PORT = os.environ.get('PGVECTOR_PORT')
_DATABASE = os.environ.get('PGVECTOR_DATABASE')
_USER = os.environ.get('PGVECTOR_USER')
_PASSWORD = os.environ.get('PGVECTOR_PASSWORD')

# SQLALCHEMY_DATABASE_URL = f"postgresql://{_USER}:{_PASSWORD}@{_HOST}:{_PORT}/{_DATABASE}"
SQLALCHEMY_DATABASE_URL="postgresql://postgres:123@110.74.194.123:6000/chatbot_project_api2"

Base = declarative_base()

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)