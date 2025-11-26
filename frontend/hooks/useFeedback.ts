import { useMutation } from "@tanstack/react-query"
import { feedbackAPI } from "@/lib/api"

export function useFeedback() {
  return useMutation({
    mutationFn: async (feedback: any) => {
      const response = await feedbackAPI.submitFeedback(feedback)
      return response.data
    },
  })
}

