"use client";

import { useState } from "react";

interface SendMessageFormProps {
  agentId: string;
  token: string;
  onMessageSent?: () => void;
}

export default function SendMessageForm({ agentId, token, onMessageSent }: SendMessageFormProps) {
  const [recipientId, setRecipientId] = useState<string>("");
  const [messageType, setMessageType] = useState<number>(1);
  const [payload, setPayload] = useState<string>("");
  const [sending, setSending] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSending(true);
    setError(null);
    setSuccess(false);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/messages/send`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          sender_id: agentId,
          recipient_id: recipientId || null,
          message_type: messageType,
          payload: payload,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to send message");
      }

      const result = await response.json();
      console.log("✅ Message sent:", result);
      
      setSuccess(true);
      setPayload(""); // Clear payload after sending
      
      if (onMessageSent) {
        onMessageSent();
      }

      // Hide success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      console.error("❌ Error sending message:", err);
      setError(err.message || "Failed to send message");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-6">
      <h2 className="text-xl font-semibold mb-4">Send Message</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="recipientId" className="block text-sm font-medium text-gray-700 mb-1">
            Recipient Agent ID (leave empty for broadcast)
          </label>
          <input
            id="recipientId"
            type="text"
            value={recipientId}
            onChange={(e) => setRecipientId(e.target.value)}
            placeholder="e.g., agent-456"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label htmlFor="messageType" className="block text-sm font-medium text-gray-700 mb-1">
            Message Type (0-127)
          </label>
          <input
            id="messageType"
            type="number"
            min="0"
            max="127"
            value={messageType}
            onChange={(e) => setMessageType(parseInt(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label htmlFor="payload" className="block text-sm font-medium text-gray-700 mb-1">
            Message Content *
          </label>
          <textarea
            id="payload"
            value={payload}
            onChange={(e) => setPayload(e.target.value)}
            placeholder="Enter your message..."
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        )}

        {success && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-md">
            <p className="text-green-600 text-sm">✓ Message sent successfully!</p>
          </div>
        )}

        <button
          type="submit"
          disabled={sending || !payload.trim()}
          className={`w-full px-4 py-2 rounded-md font-medium transition-colors ${
            sending || !payload.trim()
              ? "bg-gray-300 text-gray-500 cursor-not-allowed"
              : "bg-blue-600 text-white hover:bg-blue-700"
          }`}
        >
          {sending ? "Sending..." : "Send Message"}
        </button>
      </form>
    </div>
  );
}
