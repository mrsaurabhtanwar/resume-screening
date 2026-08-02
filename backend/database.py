import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    raise RuntimeError("DATABASE_URL must be configured before starting the application.")

engine = create_engine(
    DB_URL,
    pool_pre_ping=True,
    pool_recycle=300
)

sessionLocal = sessionmaker(autoflush=True, bind=engine)
Base = declarative_base()

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()
