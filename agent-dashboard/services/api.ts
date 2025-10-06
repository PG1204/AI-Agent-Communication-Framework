import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Message {
  message_id: string;
  sender_id: string;
  recipient_id: string | null;
  message_type: number;
  payload: string | null;
  timestamp: string | null;
  correlation_id: string | null;
}

export interface Agent {
  agent_id: string;
  last_message_time: string | null;
}

export async function fetchMessages(
  agentId: string,
  token: string,
  limit = 20,
  offset = 0
): Promise<Message[]> {
  const response = await axios.get<Message[]>(`${API_URL}/messages`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    params: {
      agent_id: agentId,
      limit,
      offset,
    },
  });
  return response.data;
}

export async function fetchAgents(agentId: string, token: string): Promise<Agent[]> {
  const response = await axios.get<Agent[]>(`${API_URL}/agents`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    params: {
      agent_id: agentId,
    },
  });
  return response.data;
}

export async function fetchConversation(
  agentId: string,
  otherAgentId: string,
  token: string,
  limit: number = 50,
  offset: number = 0
): Promise<Message[]> {
  const response = await axios.get<Message[]>(
    `${API_URL}/conversations/${otherAgentId}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      params: {
        agent_id: agentId,
        limit,
        offset,
      },
    }
  );
  return response.data;
}
