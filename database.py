from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Retrieve database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# Create a SQLAlchemy engine to connect to the database
# The engine is the starting point for any SQLAlchemy application.
engine = create_engine(DATABASE_URL)

# Configure a SessionLocal class for database interactions
# sessionmaker creates a factory for Session objects.
# autocommit=False: Ensures that changes are not committed automatically.
# autoflush=False: Prevents the session from flushing changes to the database automatically.
# bind=engine: Binds the session to the created engine.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
# This is used by SQLAlchemy to define database tables as Python classes.
Base = declarative_base()
