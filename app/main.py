"""App entrypoint: REST history endpoint, live WebSocket feed, and the
ingestion service that bridges MQTT to both.
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.ingestion import IngestionService
from app.models import ReadingRecord
from app.schemas import ReadingOut
from app.ws_manager import ConnectionManager

Base.metadata.create_all(bind=engine)

manager = ConnectionManager()
_ingestion_service: IngestionService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _ingestion_service
    loop = asyncio.get_event_loop()
    _ingestion_service = IngestionService(manager, loop)
    _ingestion_service.start()
    yield
    _ingestion_service.stop()


app = FastAPI(title="EmbedWatch", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def dashboard():
    return FileResponse("static/index.html")


@app.get("/health")
def health_check():
    return JSONResponse({"status": "ok"})


@app.get("/readings", response_model=list[ReadingOut])
def list_readings(sensor_id: str | None = None, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(ReadingRecord)
    if sensor_id:
        query = query.filter(ReadingRecord.sensor_id == sensor_id)
    return query.order_by(desc(ReadingRecord.received_at)).limit(min(limit, 500)).all()


@app.websocket("/ws/live")
async def live_feed(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
