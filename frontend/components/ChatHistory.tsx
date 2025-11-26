"use client"

import { Message } from "@/lib/types"

interface ChatHistoryProps {
  messages: Message[]
}

export default function ChatHistory({ messages }: ChatHistoryProps) {
  return (
    <div className="space-y-2">
      {messages.map((msg) => (
        <div key={msg.id} className="p-2 border rounded">
          <p className="text-sm text-gray-600">{msg.message_type}</p>
          <p>{msg.content}</p>
          <p className="text-xs text-gray-400">{new Date(msg.created_at).toLocaleString()}</p>
        </div>
      ))}
    </div>
  )
}

