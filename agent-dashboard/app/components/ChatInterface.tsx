"use client";

import { useState, useEffect, useRef } from "react";
import { fetchAgents, fetchConversation } from "../../services";

interface Agent {
  agent_id: string;
  last_message_time: string | null;
}

interface Message {
  message_id: string;
  sender_id: string;
  recipient_id: string | null;
  message_type: number;
  payload: string | null;
  timestamp: string | null;
  correlation_id: string | null;
}

interface ChatInterfaceProps {
  agentId: string;
  token: string;
  onSendMessage: (recipientId: string, payload: string, messageType: number) => Promise<void>;
  newMessages: Message[];
}

export default function ChatInterface({ agentId, token, onSendMessage, newMessages }: ChatInterfaceProps) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [conversation, setConversation] = useState<Message[]>([]);
  const [messageInput, setMessageInput] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [sending, setSending] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch list of agents on mount
  useEffect(() => {
    async function loadAgents() {
      try {
        const data = await fetchAgents(agentId, token);
        setAgents(data);
      } catch (error) {
        console.error("Error loading agents:", error);
      }
    }
    loadAgents();
  }, [agentId, token]);

  // Load conversation when agent is selected
  useEffect(() => {
    async function loadConversation() {
      if (!selectedAgent) return;
      
      setLoading(true);
      try {
        const data = await fetchConversation(agentId, selectedAgent, token);
        setConversation(data.reverse()); // Reverse to show oldest first
      } catch (error) {
        console.error("Error loading conversation:", error);
      } finally {
        setLoading(false);
      }
    }
    loadConversation();
  }, [selectedAgent, agentId, token]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation]);

  // Handle new real-time messages
  useEffect(() => {
    if (newMessages.length > 0 && selectedAgent) {
      const relevantMessages = newMessages.filter(
        (msg) =>
          (msg.sender_id === selectedAgent && msg.recipient_id === agentId) ||
          (msg.sender_id === agentId && msg.recipient_id === selectedAgent)
      );

      if (relevantMessages.length > 0) {
        setConversation((prev) => {
          const existingIds = new Set(prev.map((m) => m.message_id));
          const uniqueNew = relevantMessages.filter((m) => !existingIds.has(m.message_id));
          return [...prev, ...uniqueNew];
        });
      }
    }
  }, [newMessages, selectedAgent, agentId]);

  const handleSend = async () => {
    if (!selectedAgent || !messageInput.trim() || sending) return;

    setSending(true);
    try {
      await onSendMessage(selectedAgent, messageInput, 1);
      setMessageInput("");
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setSending(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (timestamp: string | null) => {
    if (!timestamp) return "";
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="flex h-[600px] bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Left Sidebar - Agent List */}
      <div className="w-64 bg-gray-50 border-r border-gray-200 overflow-y-auto">
        <div className="p-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-800">Conversations</h2>
        </div>
        <div>
          {agents.length === 0 ? (
            <p className="p-4 text-sm text-gray-500">No conversations yet</p>
          ) : (
            agents.map((agent) => (
              <button
                key={agent.agent_id}
                onClick={() => setSelectedAgent(agent.agent_id)}
                className={`w-full p-4 text-left hover:bg-gray-100 transition-colors border-b border-gray-100 ${
                  selectedAgent === agent.agent_id ? "bg-blue-50 border-l-4 border-l-blue-500" : ""
                }`}
              >
                <div className="font-medium text-gray-800">{agent.agent_id}</div>
                {agent.last_message_time && (
                  <div className="text-xs text-gray-500 mt-1">
                    {new Date(agent.last_message_time).toLocaleString()}
                  </div>
                )}
              </button>
            ))
          )}
        </div>
      </div>

      {/* Right Side - Chat Area */}
      <div className="flex-1 flex flex-col">
        {selectedAgent ? (
          <>
            {/* Chat Header */}
            <div className="p-4 border-b border-gray-200 bg-white">
              <h3 className="font-semibold text-gray-800">{selectedAgent}</h3>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
              {loading ? (
                <p className="text-gray-500 text-center">Loading conversation...</p>
              ) : conversation.length === 0 ? (
                <p className="text-gray-500 text-center">No messages yet. Start the conversation!</p>
              ) : (
                conversation.map((msg) => {
                  const isSentByMe = msg.sender_id === agentId;
                  return (
                    <div
                      key={msg.message_id}
                      className={`flex ${isSentByMe ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                          isSentByMe
                            ? "bg-blue-500 text-white"
                            : "bg-white text-gray-800 border border-gray-200"
                        }`}
                      >
                        <p className="whitespace-pre-wrap break-words">{msg.payload}</p>
                        <p
                          className={`text-xs mt-1 ${
                            isSentByMe ? "text-blue-100" : "text-gray-500"
                          }`}
                        >
                          {formatTime(msg.timestamp)}
                        </p>
                      </div>
                    </div>
                  );
                })
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input */}
            <div className="p-4 bg-white border-t border-gray-200">
              <div className="flex gap-2">
                <textarea
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type a message..."
                  rows={2}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                />
                <button
                  onClick={handleSend}
                  disabled={!messageInput.trim() || sending}
                  className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                    !messageInput.trim() || sending
                      ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                      : "bg-blue-500 text-white hover:bg-blue-600"
                  }`}
                >
                  {sending ? "..." : "Send"}
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            Select a conversation to start messaging
          </div>
        )}
      </div>
    </div>
  );
}
