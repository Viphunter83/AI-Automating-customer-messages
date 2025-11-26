'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { messagesAPI, feedbackAPI, dialogsApi } from '@/lib/api'
import { Message, Classification, MessageWithClassification, ChatSession } from '@/lib/types'

// Hook для получения сообщений клиента
export function useMessages(clientId: string) {
  return useQuery({
    queryKey: ['messages', clientId],
    queryFn: () => messagesAPI.getClientMessages(clientId).then(res => res.data),
    refetchInterval: 3000, // Poll every 3 seconds
    enabled: !!clientId,
  })
}

// Hook для получения классификаций
export function useClassifications(clientId: string) {
  return useQuery({
    queryKey: ['classifications', clientId],
    queryFn: () => messagesAPI.getClientClassifications(clientId).then(res => res.data),
    refetchInterval: 3000,
    enabled: !!clientId,
  })
}

// Hook для отправки сообщения (test только)
export function useSendMessage() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: { client_id: string; content: string }) =>
      messagesAPI.createMessage(data.client_id, data.content),
    
    onSuccess: (data, variables) => {
      // Invalidate queries
      queryClient.invalidateQueries({
        queryKey: ['messages', variables.client_id]
      })
      queryClient.invalidateQueries({
        queryKey: ['classifications', variables.client_id]
      })
    },
  })
}

// Hook для отправки фидбэка
export function useFeedback() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (feedback: any) => feedbackAPI.submitFeedback(feedback),
    
    onSuccess: (data) => {
      // Invalidate feedback-related queries
      queryClient.invalidateQueries({ queryKey: ['feedback'] })
    },
  })
}

// Hook для объединения сообщений с классификациями
export function useChatSession(clientId: string) {
  const { data: messages = [], isLoading: messagesLoading } = useMessages(clientId)
  const { data: classifications = [], isLoading: classificationsLoading } = useClassifications(clientId)
  
  const combined: MessageWithClassification[] = messages.map((msg: Message) => ({
    ...msg,
    classification: classifications.find((c: Classification) => c.message_id === msg.id)
  }))
  
  return {
    messages: combined,
    isLoading: messagesLoading || classificationsLoading,
    messageCount: messages.length,
  }
}

export function useDialog(clientId: string | null) {
  return useQuery({
    queryKey: ['dialog', clientId],
    queryFn: () => dialogsApi.get(clientId!).then(res => res.data),
    enabled: !!clientId,
    refetchInterval: 5000, // Poll every 5 seconds
  })
}

export function useDialogStats(clientId: string | null) {
  return useQuery({
    queryKey: ['dialogStats', clientId],
    queryFn: () => dialogsApi.getStats(clientId!).then(res => res.data),
    enabled: !!clientId,
  })
}

export function useCloseDialog() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (clientId: string) => dialogsApi.close(clientId),
    onSuccess: (_, clientId) => {
      queryClient.invalidateQueries({ queryKey: ['dialog', clientId] })
      queryClient.invalidateQueries({ queryKey: ['dialogStats', clientId] })
    },
  })
}

export function useReopenDialog() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (clientId: string) => dialogsApi.reopen(clientId),
    onSuccess: (_, clientId) => {
      queryClient.invalidateQueries({ queryKey: ['dialog', clientId] })
      queryClient.invalidateQueries({ queryKey: ['dialogStats', clientId] })
    },
  })
}
