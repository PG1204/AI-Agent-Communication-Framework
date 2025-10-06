import { useEffect, useState, useRef } from 'react';

interface Message {
  message_id: string;
  sender_id: string;
  recipient_id: string | null;
  message_type: number;
  payload: string | null;
  timestamp: string | null;
  correlation_id: string | null;
}

export function useSSE(url: string, enabled: boolean = true) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!enabled || !url) {
      console.log('⏭️ SSE: Not enabled or no URL');
      return;
    }

    console.log('🔌 SSE: Creating connection to', url);

    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.addEventListener('open', () => {
      console.log('✅ SSE: Connected');
      setIsConnected(true);
    });

    eventSource.addEventListener('message', (event) => {
      console.log('📨 SSE: Raw data received:', event.data);
      
      if (!event.data || event.data.trim() === '') {
        return;
      }

      try {
        const newMessage: Message = JSON.parse(event.data);
        console.log('✅ SSE: Parsed message:', newMessage.payload?.substring(0, 30));
        
        setMessages(prev => {
          const exists = prev.some(m => m.message_id === newMessage.message_id);
          if (exists) {
            console.log('⏭️ SSE: Duplicate, skipping');
            return prev;
          }
          console.log('✨ SSE: Adding new message to state');
          return [newMessage, ...prev];
        });
      } catch (error) {
        console.error('❌ SSE: Parse error:', error);
      }
    });

    eventSource.addEventListener('error', (error) => {
      console.error('❌ SSE: Connection error');
      setIsConnected(false);
      eventSource.close();
    });

    return () => {
      console.log('🧹 SSE: Cleanup - closing connection');
      eventSource.close();
      setIsConnected(false);
    };
  }, [url, enabled]); // React to URL and enabled changes

  return { 
    messages, 
    isConnected, 
    error: null, 
    clearMessages: () => {
      console.log('🗑️ SSE: Clearing messages');
      setMessages([]);
    }
  };
}
