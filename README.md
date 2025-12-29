# AI Agent Communication Framework

A comprehensive framework for building, deploying, and orchestrating intelligent AI agents that can communicate with each other in real-time. Combines gRPC for high-performance agent-to-agent communication with a REST API layer and a modern Next.js dashboard for monitoring and interaction.

> **⚠️ Early Development Stage**  
> This project is currently in active development and is being run and tested locally. All services default to `localhost` with environment-specific configurations. **Production deployment documentation and guides (Docker, cloud platforms, remote hosts) will be added in upcoming releases.** For now, follow the local development setup below.

---

## 📋 Overview

This framework enables:
- **Multi-agent systems**: Deploy multiple AI agents that communicate autonomously
- **Real-time messaging**: Bi-directional gRPC streaming for low-latency message exchange
- **AI-powered agents**: Built-in support for LLM integration (Groq API)
- **Agent orchestration**: Coordinator agent that routes tasks between specialist agents
- **Web dashboard**: Next.js UI for monitoring agents and sending messages
- **Persistent storage**: PostgreSQL backend for message history and state
- **JWT authentication**: Secure agent-to-agent and client-to-server communication

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Dashboard (Web UI)                    │
│                    Next.js + React + TypeScript                  │
│  - Chat interface                                                │
│  - Agent monitoring                                              │
│  - Real-time message updates (SSE)                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API (axios)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI REST Server                           │
│  - JWT token generation & verification                          │
│  - Message routing & persistence                                │
│  - Agent registry queries                                        │
│  - WebSocket/SSE endpoints                                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
    ┌─────────────────────────────────────────┐
    │        gRPC Server (Port 50051)          │
    │  - AgentComm (bi-directional streaming) │
    │  - AgentRegistry (agent registration)   │
    │  - Database polling for message routing │
    └─────────────────────────────────────────┘
        ▲                  │                  ▲
        │                  │                  │
        │ gRPC            │ Postgres         │ gRPC
        │ Streaming        │                  │
        │                  ▼                  │
    ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
    │  Coordinator    Message      Agent Config/
    │  Agent          Database     Metadata
    │                            │
    │  ┌──────────────────────┐ │
    │  │ - Orchest tasks      │ │
    │  │ - Route to agents    │ │
    │  │ - Synthesize results │ │
    │  └──────────────────────┘ │
    └─────────────┘              │
        ▲                        ▼
        │                   ┌────────────────┐
        ├─────────────────►│ Research Agent │
        │                  │ Research Agent │
        ├─────────────────►│ Code Agent     │
        │                  │ etc...         │
        └──────────────────┘────────────────┘
```

## 📁 Project Structure

```
├── server/                          # Python gRPC backend
│   ├── main.py                     # gRPC server implementation
│   ├── api.py                      # FastAPI REST API layer
│   ├── auth.py                     # JWT token generation & verification
│   ├── agent_comm_pb2.py          # Generated protobuf Python files
│   └── agent_comm_pb2_grpc.py     # Generated gRPC service stubs
│
├── sdk/                            # Python Agent SDK
│   ├── agent.py                   # Base AgentClient class
│   ├── intelligent_agent.py       # AI-powered agent with LLM support
│   ├── coordinator_agent.py       # Task orchestration agent
│   ├── code_agent.py              # Code-focused specialist agent
│   ├── research_agent.py          # Research/analysis specialist agent
│   ├── demo_agent.py              # Demo example agent
│   ├── smart_coordinator.py       # Advanced coordinator
│   └── agent_comm_pb2*.py         # Generated protobuf files
│
├── agent-dashboard/                # Next.js web UI
│   ├── app/
│   │   ├── page.tsx              # Home page
│   │   ├── login/                # Authentication
│   │   ├── chat/                 # Chat interface
│   │   ├── layout.tsx            # Root layout
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx    # Agent chat UI
│   │   │   ├── SendMessageForm.tsx  # Message composer
│   │   │   ├── ClientLayout.tsx     # Client-side layout
│   │   │   └── ThemeToggle.tsx      # Dark mode toggle
│   │   ├── contexts/
│   │   │   └── ThemeContext.tsx     # Theme provider
│   │   └── globals.css
│   ├── services/
│   │   ├── api.ts                 # API client (axios)
│   │   └── index.ts
│   ├── hooks/
│   │   └── useSSE.ts              # Server-Sent Events hook
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   └── tailwind.config.js
│
├── proto/
│   └── agent_comm.proto           # gRPC service & message definitions
│
└── requirements.txt               # Python dependencies
```

## 🔌 Core Concepts

### Message Types
- **DIRECT**: Point-to-point messages between agents
- **BROADCAST**: One agent sends to all others
- **EVENT**: Event notifications
- **REQUEST**: Inter-agent request (for coordinator pattern)
- **RESPONSE**: Reply to a request
- **HEARTBEAT**: Keep-alive signal

### Agent Roles
1. **Specialist Agents** (code-agent, research-agent)
   - Focused expertise in a domain
   - Respond to direct requests
   - Can be chained by coordinator

2. **Coordinator Agent**
   - Receives complex user requests
   - Analyzes which specialist(s) to route to
   - Synthesizes results into final response
   - Manages inter-agent communication

3. **Basic Agents**
   - Simple message send/receive
   - No AI/LLM integration
   - Good for testing and light tasks

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+ (for dashboard)
- PostgreSQL 12+
- Groq API key (for AI agents): https://console.groq.com

### 1. Clone & Setup Environment

```bash
git clone https://github.com/PG1204/AI-Agent-Communication-Framework.git
cd "AI Agent Communication Framework"

# Setup Python
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Setup Node.js
cd agent-dashboard
npm install
cd ..
```

### 2. Database Setup

```bash
# Create PostgreSQL database
createdb agent_comm_db

# Create schema (connect to database)
psql -d agent_comm_db -c "
CREATE TABLE IF NOT EXISTS agent_messages (
  message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sender_id TEXT NOT NULL,
  recipient_id TEXT,
  message_type INTEGER NOT NULL,
  payload BYTEA,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  correlation_id TEXT
);

CREATE INDEX idx_recipient_timestamp ON agent_messages(recipient_id, timestamp);
CREATE INDEX idx_sender_timestamp ON agent_messages(sender_id, timestamp);
"
```

### 3. Configure Secrets

Create a `.env` file in the project root or export environment variables:

> **Note:** Currently configured for local development (localhost). Production deployment configurations will be documented soon.

```bash
# Database
export AGENT_DB_USER="your_db_user"
export AGENT_DB_PASSWORD="your_db_password"
export AGENT_DB_HOST="localhost"
export AGENT_DB_PORT="5432"
export AGENT_DB_NAME="agent_comm_db"

# JWT
export JWT_SECRET="your-super-secret-key-change-this-in-production"
export JWT_ALGORITHM="HS256"
export JWT_EXPIRY_MINUTES="60"

# AI Integration
export GROQ_API_KEY="your-groq-api-key"

# API URLs
export NEXT_PUBLIC_API_URL="http://localhost:8000"
export GRPC_HOST="localhost:50051"
```

### 4. Start the Services

**Terminal 1 - gRPC Server:**
```bash
python server/main.py
# Expected: "🚀 Starting gRPC server on [::]:50051..."
# Expected: "✅ Server started and ready!"
```

**Terminal 2 - REST API (FastAPI):**
```bash
uvicorn server.api:app --reload --port 8000
# Expected: "Uvicorn running on http://127.0.0.1:8000"
```

**Terminal 3 - Dashboard:**
```bash
cd agent-dashboard
npm run dev
# Expected: "▲ Next.js 15.5.4"
# Open: http://localhost:3000
```

**Terminal 4+ - Launch Agents:**
```bash
# Coordinator Agent (orchestrates tasks)
python sdk/coordinator_agent.py

# Research Agent (in another terminal)
python sdk/research_agent.py

# Code Agent (in another terminal)
python sdk/code_agent.py
```

## 📡 API Reference

### REST API Endpoints

#### Authentication
```http
POST /token
{
  "agent_id": "my-agent"
}
Response:
{
  "access_token": "eyJ0...",
  "token_type": "bearer"
}
```

#### Send Message
```http
POST /messages/send
Authorization: Bearer <token>
{
  "sender_id": "agent-1",
  "recipient_id": "agent-2",
  "message_type": 0,
  "payload": "Hello Agent 2!",
  "correlation_id": "optional-id"
}
```

#### Get Messages
```http
GET /messages?agent_id=agent-1&limit=20&offset=0
Authorization: Bearer <token>
```

#### Get All Agents
```http
GET /agents?agent_id=agent-1
Authorization: Bearer <token>
```

#### Get Conversation
```http
GET /conversations/{other_agent_id}?agent_id=agent-1&limit=50
Authorization: Bearer <token>
```

### gRPC API

See `proto/agent_comm.proto` for detailed service definitions:

#### AgentRegistry Service
```protobuf
rpc RegisterAgent(RegisterAgentRequest) returns (RegisterAgentResponse);
```
Registers a new agent and returns a JWT token.

#### AgentComm Service
```protobuf
rpc StreamMessages(stream AgentMessage) returns (stream AgentMessage);
```
Bi-directional streaming for real-time message exchange.

## 🤖 Creating Custom Agents

### Simple Agent (No AI)

```python
import asyncio
from sdk.agent import AgentClient

async def main():
    agent = AgentClient("my-simple-agent")
    
    # Register with server
    await agent.register_agent()
    
    # Send a direct message
    await agent.send_direct_message("recipient-agent-id", "Hello!")
    
    # Send broadcast
    await agent.send_broadcast_message("Hello everyone!")
    
    # Run agent (listen for incoming messages)
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### AI-Powered Agent

```python
import asyncio
import os
from sdk.intelligent_agent import IntelligentAgent

SYSTEM_PROMPT = """You are a helpful assistant specialized in [your domain].
Focus on [specific capabilities].
Keep responses concise and actionable."""

async def main():
    agent = IntelligentAgent(
        agent_id="my-ai-agent",
        system_prompt=SYSTEM_PROMPT,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    
    await agent.connect()

if __name__ == "__main__":
    asyncio.run(main())
```

### Coordinator Agent (Task Router)

```python
import asyncio
import os
from sdk.intelligent_agent import IntelligentAgent

COORDINATOR_PROMPT = """You are a Coordinator Agent.
When you receive a request:
1. Analyze what needs to be done
2. Decide which specialist agent(s) to send it to
3. Send request using format: "REQUEST TO [agent-name]: [specific task]"
4. Wait for responses and synthesize them"""

async def main():
    agent = IntelligentAgent(
        agent_id="coordinator-agent",
        system_prompt=COORDINATOR_PROMPT,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    
    await agent.connect()

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔐 Authentication & Security

### JWT Token Flow

1. **Agent Registration** → gRPC `RegisterAgent()` → Returns JWT token
2. **Agent Connection** → Includes token in gRPC metadata: `Authorization: Bearer <token>`
3. **Message Sending** → REST API validates token via `verify_jwt()`
4. **Dashboard Login** → Same JWT flow for web users

### Security Best Practices

- [ ] Move `JWT_SECRET` to environment variables (never hardcode)
- [ ] Use strong, randomly generated JWT secrets (32+ characters)
- [ ] Rotate tokens regularly (currently 60-minute expiry)
- [ ] Use HTTPS in production
- [ ] Add database password from environment (not hardcoded)
- [ ] Implement agent credential verification before registration
- [ ] Add rate limiting to REST API endpoints
- [ ] Use connection pooling with asyncpg (already implemented)

## 🛠️ Development

### Regenerate Protocol Buffers

If you modify `proto/agent_comm.proto`:

```bash
python -m grpc_tools.protoc \
  -I./proto \
  --python_out=./server \
  --grpc_python_out=./server \
  ./proto/agent_comm.proto

# Copy to SDK for agents
cp server/agent_comm_pb2*.py sdk/
```

### Run Tests

```bash
# Test agent registration
python sdk/test_auth_client.py

# Test messaging (after server is running)
python sdk/agent.py test-agent-1  # Terminal 1
python sdk/agent.py test-agent-2  # Terminal 2
```

### Debugging

- **gRPC Server Logs**: Watch `server/main.py` output for connection/message flow
- **API Server Logs**: Check `uvicorn` console for HTTP requests
- **Agent Logs**: Each agent prints its operations (connection, send, receive)
- **Dashboard**: Check browser console (F12) for frontend errors

## 📊 Example Workflows

### Scenario 1: Simple Agent-to-Agent Chat

```
1. Launch code-agent and research-agent
2. Open http://localhost:3000
3. Log in with agent ID
4. Select other agent from list
5. Send message → both agents receive and respond
```

### Scenario 2: Coordinator Routing Complex Task

```
User Request: "How do I build a REST API in Python and compare it with gRPC?"

Coordinator Flow:
1. Receives request from user/dashboard
2. Routes to code-agent: "Write example REST API in Python"
3. Routes to research-agent: "Compare REST vs gRPC"
4. Waits for both responses
5. Synthesizes final answer
6. Sends back to user via dashboard
```

### Scenario 3: Real-time Monitoring

```
1. Multiple specialist agents running
2. Dashboard shows live agent status
3. Message history visible
4. Admin can send broadcast messages to all agents
5. View message flow and response times
```

## 🚨 Known Issues & Limitations

1. **Database credentials in source code** (server/main.py, server/api.py)
   - Need to migrate to environment variables

2. **No persistent agent state** beyond message history
   - Consider adding agent metadata table for status, capabilities

3. **No rate limiting** on REST API
   - Consider adding FastAPI slowapi

4. **Groq API rate limits** for AI agents
   - Currently has retry logic with exponential backoff

5. **No agent discovery service**
   - Agents must be manually registered or hardcoded in coordinator

6. **WebSocket/SSE not fully implemented**
   - Dashboard uses polling instead of true push updates

7. **No message encryption** (TLS/SSL)
   - Add in production environments

## 📦 Dependencies

### Python (server & agents)
- `fastapi` - REST API framework
- `uvicorn` - ASGI server
- `grpcio` - gRPC runtime
- `protobuf` - Protocol buffers
- `asyncpg` - Async PostgreSQL driver
- `pydantic` - Data validation
- `python-jose` - JWT implementation
- `groq` - Groq API client
- `python-dotenv` - Environment variable management

### Node.js (dashboard)
- `next` 15.5.4 - React framework
- `react` 19.1.0 - UI library
- `axios` - HTTP client
- `tailwindcss` - Styling
- `lucide-react` - Icons

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Commit changes: `git commit -am "Add your feature"`
3. Push to branch: `git push origin feature/your-feature`
4. Create a Pull Request

## 📝 License

This project is open source. Specify your license here.

## 🆘 Support & Troubleshooting

### "Connection refused" on port 50051
- Ensure gRPC server is running: `python server/main.py`
- Check if port is already in use: `lsof -i :50051`

### "No such table: agent_messages"
- Ensure PostgreSQL is running and database schema is created
- Verify database connection settings in environment variables

### "Invalid token" errors
- Regenerate token via `/token` endpoint
- Check JWT_SECRET matches between server/main.py and server/auth.py
- Verify token expiration (60 minutes default)

### Agent not receiving messages
- Check agent is registered (should print "Registered with ID")
- Verify recipient_id is correct
- Check database for messages (they may be persisted but not routed)
- Check gRPC server logs for routing errors

### Dashboard shows "Connection error"
- Verify REST API running on http://localhost:8000
- Check browser CORS settings
- Verify `NEXT_PUBLIC_API_URL` environment variable

### Groq API rate limits
- Wait a few minutes before retrying
- Reduce max_tokens in IntelligentAgent (currently 500)
- Consider caching responses for repeated queries

## 📚 Further Reading

- [gRPC Documentation](https://grpc.io/docs/)
- [Protocol Buffers Guide](https://developers.google.com/protocol-buffers)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Groq API Documentation](https://groq.com/api/)
- [PostgreSQL Async Python](https://magicstack.github.io/asyncpg/)

---

**Created**: December 2024  
**Repository**: https://github.com/PG1204/AI-Agent-Communication-Framework  
**Branch**: new-improvements  

For issues and feature requests, please use the GitHub Issues page.
