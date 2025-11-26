"use client"

import { useState } from "react"
import { FeedbackType } from "@/lib/types"

interface MessageFeedbackProps {
  messageId: string
  classificationId: string
  onSubmit: (feedback: {
    message_id: string
    classification_id: string
    feedback_type: FeedbackType
    operator_id: string
    comment?: string
  }) => void
}

export default function MessageFeedback({ messageId, classificationId, onSubmit }: MessageFeedbackProps) {
  const [feedbackType, setFeedbackType] = useState<FeedbackType>("correct")
  const [comment, setComment] = useState("")
  const [operatorId, setOperatorId] = useState("op_1")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      message_id: messageId,
      classification_id: classificationId,
      feedback_type: feedbackType,
      operator_id: operatorId,
      comment: comment || undefined,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-4 border rounded">
      <h3 className="font-bold">Feedback</h3>
      <div>
        <label className="block mb-2">Feedback Type</label>
        <select
          value={feedbackType}
          onChange={(e) => setFeedbackType(e.target.value as FeedbackType)}
          className="w-full p-2 border rounded"
        >
          <option value="correct">Correct</option>
          <option value="incorrect">Incorrect</option>
          <option value="needs_escalation">Needs Escalation</option>
        </select>
      </div>
      <div>
        <label className="block mb-2">Comment</label>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          className="w-full p-2 border rounded"
          rows={3}
        />
      </div>
      <button type="submit" className="px-4 py-2 bg-blue-500 text-white rounded">
        Submit Feedback
      </button>
    </form>
  )
}

