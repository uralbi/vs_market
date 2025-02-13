from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()
pgpass = os.getenv("POSTGRES_PASSWORD")
pguser = os.getenv("POSTGRES_USER")
docker = os.getenv("DOCKER")

SQLALCHEMY_DATABASE_URL = f'postgresql://{pguser}:{pgpass}@127.0.0.1:5433/Market'

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()