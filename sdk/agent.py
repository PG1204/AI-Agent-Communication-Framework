import grpc
import asyncio
import time

from server import agent_comm_pb2, agent_comm_pb2_grpc

class AgentClient:
    def __init__(self, agent_id, server_address='localhost:50051'):
        self.agent_id = agent_id
        self.server_address = server_address

    async def message_generator(self):
        """Async generator to send messages to the server."""
        for i in range(5):
            message = agent_comm_pb2.AgentMessage(
                sender_id=self.agent_id,
                recipient_id="",
                message_type=agent_comm_pb2.AgentMessage.DIRECT,
                payload=f"Hello {i} from {self.agent_id}".encode(),
                timestamp=int(time.time()),
                correlation_id=str(i)
            )
            print(f"Sending: {message.payload.decode()}")
            yield message
            await asyncio.sleep(1)

    async def receive_messages(self, call):
        """Task to receive messages from server."""
        async for response in call:
            print(f"Received from server: {response.payload.decode()}")

    async def run(self):
        async with grpc.aio.insecure_channel(self.server_address) as channel:
            stub = agent_comm_pb2_grpc.AgentCommStub(channel)
            call = stub.StreamMessages(self.message_generator())

            receive_task = asyncio.create_task(self.receive_messages(call))
            await receive_task

if __name__ == "__main__":
    agent = AgentClient(agent_id="agent-1")
    asyncio.run(agent.run())

