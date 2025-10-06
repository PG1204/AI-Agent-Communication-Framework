from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.responses import StreamingResponse
import asyncpg
from typing import Optional
import datetime
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from server.auth import verify_jwt, create_access_token
from jose import JWTError, jwt
import asyncio
import json

# JWT Configuration - should match your server/auth.py
JWT_SECRET = "your_very_secret_key"
JWT_ALGORITHM = "HS256"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_pool = None

# Token request model
class TokenRequest(BaseModel):
    agent_id: str

# Message sending model
class SendMessageRequest(BaseModel):
    sender_id: str
    recipient_id: Optional[str] = None
    message_type: int
    payload: str
    correlation_id: Optional[str] = None

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

# Token endpoint for login
@app.post("/token")
async def get_token(request: TokenRequest):
    """
    Issue a JWT token for the given agent_id.
    In production, verify agent credentials here.
    """
    if not request.agent_id:
        raise HTTPException(status_code=400, detail="Missing agent_id")
    
    # Create JWT token
    token = create_access_token(data={"agent_id": request.agent_id})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/messages/send")
async def send_message(
    request: SendMessageRequest,
    token_payload: dict = Depends(verify_jwt),
):
    """
    Send a message from one agent to another (or broadcast to all)
    """
    # Verify the sender matches the authenticated agent
    if token_payload.get("agent_id") != request.sender_id:
        raise HTTPException(status_code=403, detail="Cannot send messages as another agent")
    
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database connection not initialized")
    
    # Validate message_type range
    if request.message_type < 0 or request.message_type > 127:
        raise HTTPException(status_code=400, detail="message_type must be between 0 and 127")
    
    # Insert message into database
    query = """
        INSERT INTO agent_messages (sender_id, recipient_id, message_type, payload, timestamp, correlation_id)
        VALUES ($1, $2, $3, $4, NOW(), $5)
        RETURNING message_id, timestamp
    """
    
    try:
        row = await db_pool.fetchrow(
            query,
            request.sender_id,
            request.recipient_id,
            request.message_type,
            request.payload.encode('utf-8'),
            request.correlation_id
        )
        
        return {
            "status": "success",
            "message_id": str(row["message_id"]),
            "timestamp": row["timestamp"].isoformat(),
            "sender_id": request.sender_id,
            "recipient_id": request.recipient_id,
        }
    except Exception as e:
        print(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")

@app.get("/agents")
async def get_agents(
    agent_id: str = Query(..., description="Current agent ID"),
    token_payload: dict = Depends(verify_jwt),
):
    """
    Get list of all agents that have communicated with or sent messages
    """
    if token_payload.get("agent_id") != agent_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database connection not initialized")
    
    # Get unique agents with their most recent message time
    query = """
        WITH all_agents AS (
            SELECT 
                CASE 
                    WHEN sender_id = $1 THEN recipient_id
                    WHEN recipient_id = $1 THEN sender_id
                END AS agent_id,
                timestamp
            FROM agent_messages
            WHERE (sender_id = $1 OR recipient_id = $1)
              AND recipient_id IS NOT NULL
              AND sender_id != recipient_id
        )
        SELECT 
            agent_id,
            MAX(timestamp) as last_message_time
        FROM all_agents
        WHERE agent_id IS NOT NULL AND agent_id != $1
        GROUP BY agent_id
        ORDER BY last_message_time DESC
    """
    
    try:
        rows = await db_pool.fetch(query, agent_id)
        return [
            {
                "agent_id": row["agent_id"],
                "last_message_time": row["last_message_time"].isoformat() if row["last_message_time"] else None,
            }
            for row in rows
        ]
    except Exception as e:
        print(f"Error fetching agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch agents")

@app.get("/conversations/{other_agent_id}")
async def get_conversation(
    other_agent_id: str,
    agent_id: str = Query(..., description="Current agent ID"),
    limit: int = Query(50, description="Maximum number of messages"),
    offset: int = Query(0, description="Offset for pagination"),
    token_payload: dict = Depends(verify_jwt),
):
    """
    Get conversation between current agent and another agent
    """
    if token_payload.get("agent_id") != agent_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database connection not initialized")
    
    # Get messages between these two agents
    query = """
        SELECT message_id, sender_id, recipient_id, message_type, payload, 
               extract(epoch from timestamp) as ts, correlation_id
        FROM agent_messages
        WHERE (sender_id = $1 AND recipient_id = $2) 
           OR (sender_id = $2 AND recipient_id = $1)
        ORDER BY timestamp DESC
        LIMIT $3 OFFSET $4
    """
    
    try:
        rows = await db_pool.fetch(query, agent_id, other_agent_id, limit, offset)
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
    except Exception as e:
        print(f"Error fetching conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch conversation")

@app.get("/messages")
async def get_messages(
    agent_id: str = Query(..., description="Agent ID to filter messages"),
    start_time: Optional[datetime.datetime] = Query(None, description="Start time in ISO format"),
    end_time: Optional[datetime.datetime] = Query(None, description="End time in ISO format"),
    message_type: Optional[int] = Query(None, description="Filter by message type"),
    limit: int = Query(100, description="Maximum number of messages to return, default 100"),
    offset: int = Query(0, description="Number of messages to skip, default 0"),
    token_payload: dict = Depends(verify_jwt),
):
    if token_payload.get("agent_id") != agent_id:
        raise HTTPException(status_code=403, detail="Forbidden to access other agent's messages")
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database connection not initialized")
    
    # Query to get messages sent BY this agent OR sent TO this agent OR broadcast messages
    query = """
        SELECT message_id, sender_id, recipient_id, message_type, payload, extract(epoch from timestamp) as ts, correlation_id
        FROM agent_messages
        WHERE (sender_id = $1 OR recipient_id = $1 OR recipient_id IS NULL)
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
    
    query += f" ORDER BY timestamp DESC LIMIT ${index} OFFSET ${index + 1}"
    params.extend([limit, offset])
    
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

# SSE endpoint for real-time message streaming
@app.get("/messages/stream")
async def stream_messages(
    agent_id: str = Query(..., description="Agent ID to stream messages for"),
    token: str = Query(..., description="JWT token for authentication"),
):
    """
    Stream new messages in real-time using Server-Sent Events (SSE)
    Token is passed as query parameter since EventSource doesn't support headers
    """
    # Verify the JWT token manually
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        token_agent_id = payload.get("agent_id")
        if not token_agent_id or token_agent_id != agent_id:
            raise HTTPException(status_code=403, detail="Invalid token or agent_id mismatch")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    async def event_generator():
        try:
            # Get timezone-aware current time from the database
            async with db_pool.acquire() as conn:
                last_check = await conn.fetchval("SELECT NOW()")
            
            print(f"🎬 SSE Started for {agent_id} at {last_check}")
            
            while True:
                if db_pool:
                    print(f"🔍 Checking for messages after {last_check}")
                    
                    # Query to include messages sent BY this agent OR sent TO this agent OR broadcast
                    query = """
                        SELECT message_id, sender_id, recipient_id, message_type, 
                               payload, timestamp, correlation_id
                        FROM agent_messages
                        WHERE (sender_id = $1 OR recipient_id = $1 OR recipient_id IS NULL) 
                              AND timestamp > $2
                        ORDER BY timestamp ASC
                    """
                    rows = await db_pool.fetch(query, agent_id, last_check)
                    
                    if rows:
                        print(f"📤 Sending {len(rows)} messages via SSE to {agent_id}")
                        for row in rows:
                            message = {
                                "message_id": str(row["message_id"]),
                                "sender_id": row["sender_id"],
                                "recipient_id": row["recipient_id"],
                                "message_type": row["message_type"],
                                "payload": row["payload"].decode(errors="replace") if row["payload"] else None,
                                "timestamp": row["timestamp"].isoformat() if row["timestamp"] else None,
                                "correlation_id": row["correlation_id"],
                            }
                            message_json = json.dumps(message)
                            yield f"data: {message_json}\n\n"
                            print(f"   ✉️ Sent: {message['payload'][:30] if message['payload'] else 'None'}...")
                        
                        # Update last_check to the timestamp of the last message
                        last_check = rows[-1]["timestamp"]
                        print(f"   ✅ Updated last_check to {last_check}")
                    else:
                        print("   💤 No new messages")
                
                # Send heartbeat
                yield ":heartbeat\n\n"
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            print(f"❌ SSE connection closed by client: {agent_id}")
        except Exception as e:
            print(f"❌ SSE error for {agent_id}: {e}")
            import traceback
            traceback.print_exc()
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
