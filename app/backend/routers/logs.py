from fastapi import APIRouter, Request, BackgroundTasks
import logging
from pydantic import BaseModel
from typing import Dict, Any, Optional

router = APIRouter(prefix="/logs", tags=["logs"])

class LogPayload(BaseModel):
    level: str
    message: str
    context: Optional[Dict[str, Any]] = None

logger = logging.getLogger("React-Frontend")

def process_log(payload: LogPayload):
    level = payload.level.lower()
    msg = f"{payload.message} | Context: {payload.context or {}}"
    if level == "error":
        logger.error(msg)
    elif level in ("warn", "warning"):
        logger.warning(msg)
    else:
        logger.info(msg)

@router.post("")
async def receive_log(payload: LogPayload, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_log, payload)
    return {"success": True, "data": "Log scheduled for processing"}
