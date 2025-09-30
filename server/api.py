from fastapi import FastAPI, Query, HTTPException, Depends
import asyncpg
import asyncio
from typing import Optional
import datetime
import jwt
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Security

app = FastAPI()
db_pool = None

JWT_SECRET = "your_very_secret_key"  # Keep this same as your gRPC server secret
JWT_ALGORITHM = "HS256"

security = HTTPBearer()

async def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.on_event("startup")
async def startup_event():
    global db_pool
    db_pool = await asyncpg.create_pool(
        user='prateekganigi',
        password='43121158312115',
        database='agent_comm_db',
        host='localhost',
    )

@app.on_event("shutdown")
async def shutdown_event():
    global db_pool
    if db_pool:
        await db_pool.close()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/messages")
async def get_messages(
    agent_id: str = Query(..., description="Agent ID to filter messages"),
    start_time: Optional[datetime.datetime] = Query(None, description="Start time in ISO format"),
    end_time: Optional[datetime.datetime] = Query(None, description="End time in ISO format"),
    message_type: Optional[int] = Query(None, description="Filter by message type"),
    limit: int = Query(100, description="Maximum number of messages to return, default 100"),
    token_payload: dict = Depends(verify_jwt),
):
    # Optional: restrict access to messages only for the authenticated agent ID
    if token_payload.get("agent_id") != agent_id:
        raise HTTPException(status_code=403, detail="Forbidden to access other agent's messages")

    if not db_pool:
        raise HTTPException(status_code=503, detail="Database connection not initialized")

    query = """
        SELECT message_id, sender_id, recipient_id, message_type, payload, extract(epoch from timestamp) as ts, correlation_id
        FROM agent_messages
        WHERE sender_id = $1
    """
    params = [agent_id]
    index = 2

    if start_time:
        query += f" AND timestamp >= to_timestamp(${index})"
        params.append(start_time.timestamp())
        index += 1

    if end_time:
        query += f" AND timestamp <= to_timestamp(${index})"
        params.append(end_time.timestamp())
        index += 1

    if message_type is not None:
        query += f" AND message_type = ${index}"
        params.append(message_type)
        index += 1

    query += f" ORDER BY timestamp DESC LIMIT ${index}"
    params.append(limit)

    rows = await db_pool.fetch(query, *params)

    return [
        {
            "message_id": str(row["message_id"]),
            "sender_id": row["sender_id"],
            "recipient_id": row["recipient_id"],
            "message_type": row["message_type"],
            "payload": row["payload"].decode(errors="replace") if row["payload"] else None,
            "timestamp": datetime.datetime.fromtimestamp(row["ts"]).isoformat() if row["ts"] else None,
            "correlation_id": row["correlation_id"],
        }
        for row in rows
    ]
