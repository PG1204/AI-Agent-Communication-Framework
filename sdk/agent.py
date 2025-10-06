import grpc
import asyncio
import time
import uuid

from server import agent_comm_pb2, agent_comm_pb2_grpc

import sys


class AgentClient:
    def __init__(self, agent_id, server_address='localhost:50051'):
        self.agent_id = agent_id
        self.server_address = server_address
        self.token = None
        self.send_queue = asyncio.Queue()  # Queue for outgoing messages

    async def message_generator(self):
        """Async generator to send messages from the queue."""
        # Send initial connection message immediately
        initial_msg = agent_comm_pb2.AgentMessage(
            sender_id=self.agent_id,
            recipient_id="",
            message_type=agent_comm_pb2.AgentMessage.EVENT,
            payload=b"initial_connection",
            timestamp=int(time.time()),
            correlation_id=str(uuid.uuid4())
        )
        yield initial_msg

        # Send heartbeat every 10 seconds to keep stream alive
        while True:
            try:
                # Yield message from queue if available without waiting
                msg = self.send_queue.get_nowait()
                yield msg
            except asyncio.QueueEmpty:
                # No message queued, send heartbeat
                heartbeat_msg = agent_comm_pb2.AgentMessage(
                    sender_id=self.agent_id,
                    recipient_id="",
                    message_type=agent_comm_pb2.AgentMessage.EVENT,
                    payload=b"heartbeat",
                    timestamp=int(time.time()),
                    correlation_id=str(uuid.uuid4())
                )
                yield heartbeat_msg
                await asyncio.sleep(10)

    async def receive_messages(self, call):
        """Task to receive messages from server."""
        try:
            async for response in call:
                print(f"Received from server: {response.payload.decode()}")
        except asyncio.CancelledError:
            print("Receive messages task was cancelled (stream closed).")
        except grpc.aio.AioRpcError as e:
            print(f"gRPC error received: {e}")

    async def run(self):
        async with grpc.aio.insecure_channel(self.server_address) as channel:
            stub = agent_comm_pb2_grpc.AgentCommStub(channel)
            metadata = [("authorization", f"Bearer {self.token}")]
            call = stub.StreamMessages(self.message_generator(), metadata=metadata)

            receive_task = asyncio.create_task(self.receive_messages(call))

            # Send initial messages
            await self.send_direct_message(self.agent_id, "Hello direct message")
            await self.send_broadcast_message("Hello broadcast message")
            await self.send_event_message("Event triggered")

            print("Client is connected and running. Press Ctrl+C to exit.")

            try:
                await asyncio.Event().wait()  # wait indefinitely
            except asyncio.CancelledError:
                pass
            finally:
                receive_task.cancel()
                try:
                    await receive_task
                except asyncio.CancelledError:
                    pass

    async def register_agent(self):
        async with grpc.aio.insecure_channel(self.server_address) as channel:
            stub = agent_comm_pb2_grpc.AgentRegistryStub(channel)
            request = agent_comm_pb2.RegisterAgentRequest(
                agent_name=self.agent_id,
                agent_type="basic"
            )
            response = await stub.RegisterAgent(request)
            print(f"Registered with ID: {response.agent_id}, token: {response.token}")
            self.token = response.token
            self.agent_id = response.agent_id

    async def send_direct_message(self, recipient_id, text):
        msg = agent_comm_pb2.AgentMessage(
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            message_type=agent_comm_pb2.AgentMessage.DIRECT,
            payload=text.encode(),
            timestamp=int(time.time()),
            correlation_id=str(uuid.uuid4())
        )
        print(f"Sending direct message: {text}")
        await self.send_queue.put(msg)

    async def send_broadcast_message(self, text):
        msg = agent_comm_pb2.AgentMessage(
            sender_id=self.agent_id,
            recipient_id="",  # empty for broadcast
            message_type=agent_comm_pb2.AgentMessage.BROADCAST,
            payload=text.encode(),
            timestamp=int(time.time()),
            correlation_id=str(uuid.uuid4())
        )
        print(f"Sending broadcast message: {text}")
        await self.send_queue.put(msg)

    async def send_event_message(self, event_data):
        msg = agent_comm_pb2.AgentMessage(
            sender_id=self.agent_id,
            recipient_id="",  # no specific recipient
            message_type=agent_comm_pb2.AgentMessage.EVENT,
            payload=event_data.encode(),
            timestamp=int(time.time()),
            correlation_id=str(uuid.uuid4())
        )
        print(f"Sending event message: {event_data}")
        await self.send_queue.put(msg)


async def main(agent):
    await agent.register_agent()
    await agent.run()


if __name__ == "__main__":
    agent_id = sys.argv[1] if len(sys.argv) > 1 else "agent-1"
    agent = AgentClient(agent_id=agent_id)

    try:
        asyncio.run(main(agent))
    except KeyboardInterrupt:
        print("Client stopped by user.")
