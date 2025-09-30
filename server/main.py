import asyncio
import uuid
import asyncpg
from server import agent_comm_pb2, agent_comm_pb2_grpc
import grpc
import jwt
import datetime

# JWT secret and algorithm - replace secret with environment variable in production
JWT_SECRET = "your_very_secret_key"
JWT_ALGORITHM = "HS256"

class AgentRegistryServicer(agent_comm_pb2_grpc.AgentRegistryServicer):
    def RegisterAgent(self, request, context):
        agent_id = str(uuid.uuid4())
        # Create JWT payload with expiration (1 hour)
        payload = {
            "agent_id": agent_id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        print(f"Registered agent: {request.agent_name} (type: {request.agent_type}) -> {agent_id}")
        return agent_comm_pb2.RegisterAgentResponse(
            agent_id=agent_id,
            token=token,
            message="Registration successful"
        )

class AgentCommServicer(agent_comm_pb2_grpc.AgentCommServicer):
    def __init__(self, db_pool):
        self.agent_queues = {}
        self.lock = asyncio.Lock()
        self.db_pool = db_pool

    async def save_message(self, msg):
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO agent_messages(message_id, sender_id, recipient_id, message_type, payload, timestamp, correlation_id)
                VALUES($1, $2, $3, $4, $5, to_timestamp($6), $7)
                """,
                uuid.uuid4(),               # message_id
                msg.sender_id,
                msg.recipient_id if msg.recipient_id else None,
                msg.message_type,
                msg.payload,
                msg.timestamp,             # timestamp as epoch seconds
                msg.correlation_id if msg.correlation_id else None
            )

    async def message_sender(self, agent_id, context):
        queue = self.agent_queues[agent_id]
        while True:
            msg = await queue.get()
            if msg is None:
                return
            await context.write(msg)

    async def StreamMessages(self, request_iterator, context):
        metadata = dict(context.invocation_metadata())
        print(f"Metadata received: {metadata}")

        # Extract token from 'authorization' metadata header (format: "Bearer <token>")
        auth_header = metadata.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Missing or invalid authorization token")

        token = auth_header[len("Bearer "):]

        # Verify JWT token
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            agent_id_from_token = payload.get("agent_id")
        except jwt.ExpiredSignatureError:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Token expired")
        except jwt.InvalidTokenError:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid token")

        print(f"Authenticated agent ID from token: {agent_id_from_token}")

        try:
            first_msg = await request_iterator.__anext__()
        except StopAsyncIteration:
            print("No messages received; closing stream.")
            return
        except Exception as e:
            print(f"Failed to read first message: {e}")
            return

        # Verify sender_id in message matches token's agent_id
        if first_msg.sender_id != agent_id_from_token:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Sender ID does not match token agent ID")

        agent_id = agent_id_from_token
        print(f"Agent connected: {agent_id}")

        async with self.lock:
            if agent_id not in self.agent_queues:
                self.agent_queues[agent_id] = asyncio.Queue()
            send_task = asyncio.create_task(self.message_sender(agent_id, context))

        incoming_messages = self._message_generator(first_msg, request_iterator)

        try:
            async for incoming_msg in incoming_messages:
                print(f"Received message from {agent_id}: type={incoming_msg.message_type} payload={incoming_msg.payload[:30]!r}")
                await self.save_message(incoming_msg)  # Save message to DB
                await self.route_message(incoming_msg)
        except Exception as e:
            print(f"Error during message streaming for {agent_id}: {e}")
        finally:
            send_task.cancel()
            async with self.lock:
                self.agent_queues.pop(agent_id, None)
            print(f"Agent disconnected: {agent_id}")

    async def _message_generator(self, first_msg, request_iterator):
        yield first_msg
        async for msg in request_iterator:
            yield msg

    async def route_message(self, msg):
        sender = msg.sender_id
        if msg.message_type == agent_comm_pb2.AgentMessage.DIRECT:
            recipient = msg.recipient_id
            if recipient and recipient in self.agent_queues:
                await self.agent_queues[recipient].put(msg)
        elif msg.message_type in (agent_comm_pb2.AgentMessage.BROADCAST, agent_comm_pb2.AgentMessage.EVENT):
            async with self.lock:
                for agent_id, queue in self.agent_queues.items():
                    if agent_id != sender:
                        await queue.put(msg)
        elif msg.message_type == agent_comm_pb2.AgentMessage.HEARTBEAT:
            # Ignore heartbeat messages without warnings
            pass
        else:
            print(f"Unknown message type {msg.message_type} received. Ignored.")

async def serve():
    db_pool = await asyncpg.create_pool(user='prateekganigi', password='43121158312115',
                                        database='agent_comm_db', host='localhost')

    server = grpc.aio.server()
    agent_comm_pb2_grpc.add_AgentRegistryServicer_to_server(AgentRegistryServicer(), server)
    agent_comm_pb2_grpc.add_AgentCommServicer_to_server(AgentCommServicer(db_pool), server)
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    print(f"Starting server on {listen_addr}...")
    await server.start()
    print("Server started.")
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve())
