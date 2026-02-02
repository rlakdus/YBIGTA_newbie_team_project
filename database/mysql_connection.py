from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import os
from dotenv import load_dotenv

load_dotenv()

import os

user = os.getenv("MYSQL_USER")
passwd = os.getenv("MYSQL_PASSWORD")
host = os.getenv("MYSQL_HOST")
port = os.getenv("MYSQL_PORT")
db = os.getenv("MYSQL_DATABASE")

DB_URL = f'mysql+pymysql://{user}:{passwd}@{host}:{port}/{db}?charset=utf8'

engine = create_engine(DB_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
