from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Esta es la dirección que configuramos en el docker-compose
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Esta función abrirá y cerrará la conexión cada vez que hagamos algo
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()