import grpc
from concurrent import futures
import time

import agent_comm_pb2_grpc

class AgentCommServicer(agent_comm_pb2_grpc.AgentCommServicer):
    def StreamMessages(self, request_iterator, context):
        for message in request_iterator:
            print(f"Received message from {message.sender_id}")
            yield message

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    agent_comm_pb2_grpc.add_AgentCommServicer_to_server(AgentCommServicer(), server)
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

