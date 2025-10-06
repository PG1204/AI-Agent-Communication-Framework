"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSSE } from "../hooks/useSSE";
import ChatInterface from "./components/ChatInterface";

interface Message {
  message_id: string;
  sender_id: string;
  recipient_id: string | null;
  message_type: number;
  payload: string | null;
  timestamp: string | null;
  correlation_id: string | null;
}

export default function Home() {
  const [agentId, setAgentId] = useState<string>("");
  const [token, setToken] = useState<string>("");
  const router = useRouter();

  // SSE for real-time updates
  const sseUrl = agentId && token 
    ? `${process.env.NEXT_PUBLIC_API_URL}/messages/stream?agent_id=${agentId}&token=${token}`
    : "";
  
  const { messages: newMessages, isConnected } = useSSE(sseUrl, !!agentId && !!token);

  // Check authentication on mount
  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    const storedAgentId = localStorage.getItem("agent_id");

    if (!storedToken || !storedAgentId) {
      router.push("/login");
    } else {
      setToken(storedToken);
      setAgentId(storedAgentId);
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("agent_id");
    router.push("/login");
  };

  const handleSendMessage = async (recipientId: string, payload: string, messageType: number) => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/messages/send`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        sender_id: agentId,
        recipient_id: recipientId,
        message_type: messageType,
        payload: payload,
      }),
    });

    if (!response.ok) {
      throw new Error("Failed to send message");
    }

    return response.json();
  };

  if (!agentId || !token) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Checking authentication...</p>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-semibold text-gray-800">Agent Communication</h1>
            <p className="text-sm text-gray-600 mt-1">Logged in as: <span className="font-medium">{agentId}</span></p>
          </div>
          <div className="flex items-center gap-4">
            <span className={`text-sm font-medium px-3 py-1 rounded-full ${
              isConnected ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
            }`}>
              {isConnected ? '● Live' : '○ Connecting...'}
            </span>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>

        {/* Chat Interface */}
        <ChatInterface 
          agentId={agentId} 
          token={token} 
          onSendMessage={handleSendMessage}
          newMessages={newMessages}
        />
      </div>
    </main>
  );
}
