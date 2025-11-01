'use client';
import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Bot, Send, Loader2, CheckCircle2, XCircle, User, Sparkles, Wifi } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Message {
  message_id: string;
  sender_id: string;
  recipient_id: string;
  message_type: number;
  payload: string;
  timestamp: string;
  correlation_id?: string;
}

interface Agent {
  agent_id: string;
  last_message_time?: string;
}

export default function ChatPage() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [agentId, setAgentId] = useState('');
  const [token, setToken] = useState('');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [messageInput, setMessageInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load agents periodically
  useEffect(() => {
    if (isLoggedIn && token) {
      loadAgents();
      const interval = setInterval(loadAgents, 5000);
      return () => clearInterval(interval);
    }
  }, [isLoggedIn, token]);

  // Setup SSE connection for real-time messages
  useEffect(() => {
    if (isLoggedIn && token && agentId) {
      connectSSE();
      return () => {
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }
      };
    }
  }, [isLoggedIn, token, agentId]);

  // Load initial conversation when agent is selected
  useEffect(() => {
    if (selectedAgent && token) {
      loadConversation();
    }
  }, [selectedAgent, token]);

  const connectSSE = () => {
    // Close existing connection if any
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    console.log('🔌 Connecting to SSE stream...');
    const eventSource = new EventSource(
      `${API_URL}/messages/stream?agent_id=${agentId}&token=${token}`
    );

    eventSource.onopen = () => {
      console.log('✅ SSE Connected');
      setIsConnected(true);
    };

    eventSource.onmessage = (event) => {
      // Skip heartbeat messages
      if (event.data === 'heartbeat' || event.data === ':heartbeat') {
        return;
      }

      try {
        const newMessage: Message = JSON.parse(event.data);
        console.log('📨 New message received:', newMessage);

        setMessages((prevMessages) => {
          // Check if message already exists (check both temp and real IDs)
          const exists = prevMessages.some(m => 
            m.message_id === newMessage.message_id ||
            (m.sender_id === newMessage.sender_id && 
             m.recipient_id === newMessage.recipient_id &&
             m.payload === newMessage.payload &&
             Math.abs(new Date(m.timestamp).getTime() - new Date(newMessage.timestamp).getTime()) < 2000)
          );
          
          if (exists) {
            // Replace temp message if this is the real one
            return prevMessages.map(m => 
              m.message_id.startsWith('temp-') && 
              m.payload === newMessage.payload &&
              m.sender_id === newMessage.sender_id
                ? newMessage
                : m
            );
          }

          // Check if message is part of selected conversation
          if (selectedAgent && 
              ((newMessage.sender_id === agentId && newMessage.recipient_id === selectedAgent) ||
               (newMessage.sender_id === selectedAgent && newMessage.recipient_id === agentId))) {
            return [...prevMessages, newMessage];
          }
          
          return prevMessages;
        });

        // Refresh agents list to update last message time
        loadAgents();
      } catch (error) {
        console.error('Failed to parse SSE message:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('❌ SSE Error:', error);
      setIsConnected(false);
      eventSource.close();

      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        if (isLoggedIn && token && agentId) {
          console.log('🔄 Reconnecting SSE...');
          connectSSE();
        }
      }, 3000);
    };

    eventSourceRef.current = eventSource;
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_URL}/token`, {
        agent_id: agentId
      });
      
      setToken(response.data.access_token);
      setIsLoggedIn(true);
    } catch (error) {
      console.error('Login failed:', error);
      setLoginError('Login failed. Please check your agent ID and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const loadAgents = async () => {
    try {
      const response = await axios.get(`${API_URL}/agents`, {
        params: { agent_id: agentId },
        headers: { Authorization: `Bearer ${token}` }
      });
      setAgents(response.data);
    } catch (error) {
      console.error('Failed to load agents:', error);
    }
  };

  const loadConversation = async () => {
    if (!selectedAgent) return;
    
    try {
      const response = await axios.get(
        `${API_URL}/conversations/${selectedAgent}`,
        {
          params: { agent_id: agentId },
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      // Reverse to show oldest first
      setMessages(response.data.reverse());
    } catch (error) {
      console.error('Failed to load conversation:', error);
      setMessages([]);
    }
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!messageInput.trim() || !selectedAgent) return;

    setIsLoading(true);
    const messageContent = messageInput;
    setMessageInput(''); // Clear input immediately for better UX

    // Create optimistic message to show immediately
    const optimisticMessage: Message = {
      message_id: `temp-${Date.now()}`, // Temporary ID
      sender_id: agentId,
      recipient_id: selectedAgent,
      message_type: 1,
      payload: messageContent,
      timestamp: new Date().toISOString(),
      correlation_id: undefined
    };

    // Add optimistic message immediately
    setMessages((prevMessages) => [...prevMessages, optimisticMessage]);

    try {
      const response = await axios.post(
        `${API_URL}/messages/send`,
        {
          sender_id: agentId,
          recipient_id: selectedAgent,
          message_type: 1,
          payload: messageContent,
          correlation_id: null
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      // Replace optimistic message with real one from server
      const realMessageId = response.data.message_id;
      setMessages((prevMessages) => 
        prevMessages.map(msg => 
          msg.message_id === optimisticMessage.message_id 
            ? { ...msg, message_id: realMessageId }
            : msg
        )
      );
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove optimistic message on error
      setMessages((prevMessages) => 
        prevMessages.filter(msg => msg.message_id !== optimisticMessage.message_id)
      );
      setMessageInput(messageContent); // Restore message on error
    } finally {
      setIsLoading(false);
    }
  };

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
        <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <div className="inline-flex p-4 bg-purple-500/10 rounded-2xl mb-4">
              <Bot className="h-12 w-12 text-purple-400" />
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">Agent Login</h1>
            <p className="text-gray-400">Enter your agent ID to access the platform</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Agent ID
              </label>
              <input
                type="text"
                value={agentId}
                onChange={(e) => setAgentId(e.target.value)}
                placeholder="e.g., test-agent-123"
                className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                required
              />
            </div>

            {loginError && (
              <div className="flex items-center gap-2 text-red-400 text-sm bg-red-500/10 p-3 rounded-lg">
                <XCircle className="h-4 w-4" />
                {loginError}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Connecting...
                </>
              ) : (
                'Login'
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-700">
            <p className="text-sm text-gray-400 text-center">
              Demo agent IDs: <span className="text-purple-400">test-agent-123, research-agent, code-agent</span>
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-slate-900">
      {/* Sidebar */}
      <div className="w-80 bg-slate-800 border-r border-slate-700 flex flex-col">
        <div className="p-4 border-b border-slate-700">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-purple-500/10 rounded-lg">
              <User className="h-6 w-6 text-purple-400" />
            </div>
            <div className="flex-1">
              <p className="text-sm text-gray-400">Logged in as</p>
              <p className="font-medium text-white">{agentId}</p>
            </div>
            <div className="flex items-center gap-1">
              <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-gray-500'}`} />
              <Wifi className={`h-4 w-4 ${isConnected ? 'text-green-400' : 'text-gray-500'}`} />
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Available Agents ({agents.length})
          </h2>
          <div className="space-y-2">
            {agents.map((agent) => (
              <button
                key={agent.agent_id}
                onClick={() => setSelectedAgent(agent.agent_id)}
                className={`w-full text-left p-3 rounded-lg transition-all ${
                  selectedAgent === agent.agent_id
                    ? 'bg-purple-600 text-white'
                    : 'bg-slate-700/50 text-gray-300 hover:bg-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Bot className="h-5 w-5" />
                    <span className="font-medium">{agent.agent_id}</span>
                  </div>
                  <div className="h-2 w-2 rounded-full bg-green-400" />
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {selectedAgent ? (
          <>
            {/* Chat Header */}
            <div className="h-16 bg-slate-800 border-b border-slate-700 flex items-center justify-between px-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-500/10 rounded-lg">
                  <Sparkles className="h-5 w-5 text-purple-400" />
                </div>
                <div>
                  <h2 className="font-semibold text-white">{selectedAgent}</h2>
                  <p className="text-sm text-gray-400">AI Agent</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-400" />
                <span className="text-sm text-gray-400">Real-time Connected</span>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <Sparkles className="h-12 w-12 text-gray-600 mx-auto mb-3" />
                    <p className="text-gray-400">No messages yet. Start the conversation!</p>
                  </div>
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.message_id}
                    className={`flex ${msg.sender_id === agentId ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xl px-4 py-3 rounded-2xl ${
                        msg.sender_id === agentId
                          ? 'bg-purple-600 text-white'
                          : 'bg-slate-700 text-gray-100'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.payload}</p>
                      <p className={`text-xs mt-1 ${
                        msg.sender_id === agentId ? 'text-purple-200' : 'text-gray-400'
                      }`}>
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input */}
            <div className="border-t border-slate-700 p-4">
              <form onSubmit={sendMessage} className="flex gap-3">
                <input
                  type="text"
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  placeholder="Type your message..."
                  className="flex-1 px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                <button
                  type="submit"
                  disabled={isLoading || !messageInput.trim()}
                  className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                >
                  {isLoading ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <Send className="h-5 w-5" />
                  )}
                </button>
              </form>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Bot className="h-16 w-16 text-gray-600 mx-auto mb-4" />
              <p className="text-xl font-medium text-gray-400">Select an agent to start chatting</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
