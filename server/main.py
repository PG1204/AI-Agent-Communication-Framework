import grpc
from concurrent import futures
import time

import agent_comm_pb2
import agent_comm_pb2_grpc

import uuid
from server import agent_comm_pb2, agent_comm_pb2_grpc

class AgentCommServicer(agent_comm_pb2_grpc.AgentCommServicer):
    def StreamMessages(self, request_iterator, context):
        for message in request_iterator:
            print(f"Received message from {message.sender_id}")
            yield message

class AgentRegistryServicer(agent_comm_pb2_grpc.AgentRegistryServicer):
    def RegisterAgent(self, request, context):
        agent_id = str(uuid.uuid4())
        token = str(uuid.uuid4())  # In a real app, use secure tokens/JWT
        print(f"Registered agent: {request.agent_name} (type: {request.agent_type}) -> {agent_id}")
        return agent_comm_pb2.RegisterAgentResponse(
            agent_id=agent_id,
            token=token,
            message="Registration successful"
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    agent_comm_pb2_grpc.add_AgentCommServicer_to_server(AgentCommServicer(), server)
    agent_comm_pb2_grpc.add_AgentRegistryServicer_to_server(AgentRegistryServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started on port 50051")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
    
