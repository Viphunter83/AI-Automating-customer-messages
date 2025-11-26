'use client'

import { useState } from 'react'
import { useFeedback } from '@/hooks/useMessages'
import { Classification, FeedbackType } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface MessageFeedbackProps {
  messageId: string
  classification: Classification
  operatorId: string
}

export function MessageFeedback({
  messageId,
  classification,
  operatorId
}: MessageFeedbackProps) {
  const [submitted, setSubmitted] = useState(false)
  const [selectedFeedback, setSelectedFeedback] = useState<FeedbackType | null>(null)
  const [comment, setComment] = useState('')
  
  const feedback = useFeedback()
  
  const handleSubmit = async (feedbackType: FeedbackType) => {
    try {
      await feedback.mutateAsync({
        message_id: messageId,
        classification_id: classification.id,
        feedback_type: feedbackType,
        operator_id: operatorId,
        comment: comment || undefined,
      })
      setSubmitted(true)
      setSelectedFeedback(null)
      setComment('')
      
      // Reset after 2 seconds
      setTimeout(() => setSubmitted(false), 2000)
    } catch (error) {
      console.error('Failed to submit feedback:', error)
    }
  }
  
  if (submitted) {
    return (
      <div className="p-3 bg-green-50 border border-green-200 rounded text-sm text-green-800">
        ✅ Feedback submitted. Thank you!
      </div>
    )
  }
  
  return (
    <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg space-y-3">
      <div>
        <h4 className="font-semibold text-sm mb-2">Was this classification correct?</h4>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant={selectedFeedback === 'correct' ? 'default' : 'outline'}
            onClick={() => handleSubmit('correct')}
            disabled={feedback.isPending}
          >
            ✅ Correct
          </Button>
          <Button
            size="sm"
            variant={selectedFeedback === 'incorrect' ? 'destructive' : 'outline'}
            onClick={() => setSelectedFeedback('incorrect')}
            disabled={feedback.isPending}
          >
            ❌ Incorrect
          </Button>
          <Button
            size="sm"
            variant={selectedFeedback === 'needs_escalation' ? 'secondary' : 'outline'}
            onClick={() => setSelectedFeedback('needs_escalation')}
            disabled={feedback.isPending}
          >
            ⚠️ Needs Escalation
          </Button>
        </div>
      </div>
      
      {selectedFeedback === 'incorrect' && (
        <div className="space-y-2">
          <p className="text-sm font-medium">What should it be?</p>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleSubmit('incorrect')}
              disabled={feedback.isPending}
            >
              GREETING
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleSubmit('incorrect')}
              disabled={feedback.isPending}
            >
              REFERRAL
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleSubmit('incorrect')}
              disabled={feedback.isPending}
            >
              TECH_SUPPORT
            </Button>
          </div>
        </div>
      )}
      
      {selectedFeedback && (
        <div>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Add optional comment..."
            className="w-full p-2 text-sm border border-gray-300 rounded"
            rows={2}
          />
          <Button
            size="sm"
            onClick={() => handleSubmit(selectedFeedback)}
            disabled={feedback.isPending}
            className="mt-2"
          >
            {feedback.isPending ? 'Submitting...' : 'Submit Feedback'}
          </Button>
        </div>
      )}
    </div>
  )
}
