from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from auth_utils import SECRET_KEY, ALGORITHM
from database import SessionLocal
import models
from websocket_manager import manager

router = APIRouter()


def _get_user_from_token(token: str):
    db = SessionLocal()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            return None
        return db.query(models.User).filter(models.User.username == username).first()
    except JWTError:
        return None
    finally:
        db.close()


@router.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket, token: str = Query(...)):
    user = _get_user_from_token(token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
