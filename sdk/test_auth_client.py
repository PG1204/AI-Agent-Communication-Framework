import time
import grpc
from sdk import agent_comm_pb2, agent_comm_pb2_grpc


def run():
    # Connect to the gRPC server
    channel = grpc.insecure_channel('localhost:50051')
    registry_stub = agent_comm_pb2_grpc.AgentRegistryStub(channel)
    comm_stub = agent_comm_pb2_grpc.AgentCommStub(channel)

    # Step 1: Register agent to get agent_id and JWT token
    register_request = agent_comm_pb2.RegisterAgentRequest(agent_name="agent1", agent_type="typeA")
    register_response = registry_stub.RegisterAgent(register_request)
    agent_id = register_response.agent_id
    token = register_response.token

    print(f"Registered agent ID: {agent_id}")
    print(f"Received JWT token: {token}")

    # Step 2: Prepare message generator for StreamMessages with timestamps
    def message_generator(agent_id):
        # Send an initial event message with current timestamp
        yield agent_comm_pb2.AgentMessage(
            sender_id=agent_id,
            message_type=agent_comm_pb2.AgentMessage.EVENT,
            payload=b"Initial event",
            timestamp=int(time.time())
        )
        # Send heartbeat messages periodically (3 times max)
        for i in range(3):
            print(f"Sending heartbeat #{i+1}")
            time.sleep(1)
            yield agent_comm_pb2.AgentMessage(
                sender_id=agent_id,
                message_type=agent_comm_pb2.AgentMessage.HEARTBEAT,
                payload=b"heartbeat",
                timestamp=int(time.time())
            )

    # Step 3: Call StreamMessages with JWT token in authorization metadata
    metadata = [('authorization', f'Bearer {token}')]

    try:
        responses = comm_stub.StreamMessages(message_generator(agent_id), metadata=metadata)

        start_time = time.perf_counter()
        timeout = 10  # seconds
        message_count = 0
        max_messages = 10

        for response_msg in responses:
            elapsed = time.perf_counter() - start_time
            print(f"[{elapsed:.1f}s] Received message #{message_count + 1}: type={response_msg.message_type}, payload={response_msg.payload}")
            message_count += 1
            if elapsed > timeout or message_count >= max_messages:
                print("Reached timeout or max messages, stopping response loop.")
                break

    except grpc.RpcError as e:
        print(f"gRPC error: {e.code()} - {e.details()}")


if __name__ == "__main__":
    run()
