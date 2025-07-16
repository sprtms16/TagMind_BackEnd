from fastapi import FastAPI, Depends, Request, BackgroundTasks
from sqlalchemy.orm import Session

from .database import SessionLocal, engine, Base
from . import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency to get DB session
def get_db(request: Request):
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def read_root(db: Session = Depends(get_db)):
    return {"message": "Welcome to TagMind Backend!"}
