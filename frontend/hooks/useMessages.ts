'use client'

import { useQuery, useMutation } from '@tanstack/react-query'
import { messagesAPI } from '@/lib/api'
import { Message } from '@/lib/types'

export function useMessages(clientId: string) {
  return useQuery({
    queryKey: ['messages', clientId],
    queryFn: () => messagesAPI.getClientMessages(clientId).then(res => res.data),
    refetchInterval: 5000, // Poll every 5 seconds
    enabled: !!clientId,
  })
}

export function useSendMessage() {
  return useMutation({
    mutationFn: (data: { client_id: string; content: string }) =>
      messagesAPI.createMessage(data.client_id, data.content),
    onSuccess: (data) => {
      console.log('Message processed:', data.data)
    },
  })
}
