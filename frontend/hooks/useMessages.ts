'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { messagesAPI, feedbackAPI, dialogsApi } from '@/lib/api'
import { Message, Classification, MessageWithClassification, ChatSession } from '@/lib/types'
import { safeParseMessages, safeParseClassifications } from '@/lib/validation'

// Hook для получения сообщений клиента с валидацией
export function useMessages(clientId: string) {
  return useQuery({
    queryKey: ['messages', clientId],
    queryFn: async () => {
      const response = await messagesAPI.getClientMessages(clientId);
      const result = safeParseMessages(response.data);
      
      if (!result.success) {
        console.error('Invalid messages data:', result.error);
        throw new Error('Invalid response format from API');
      }
      
      return result.data;
    },
    refetchInterval: 3000, // Poll every 3 seconds
    enabled: !!clientId,
    retry: 3, // Retry failed requests
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff
  })
}

// Hook для получения классификаций с валидацией
export function useClassifications(clientId: string) {
  return useQuery({
    queryKey: ['classifications', clientId],
    queryFn: async () => {
      const response = await messagesAPI.getClientClassifications(clientId);
      const result = safeParseClassifications(response.data);
      
      if (!result.success) {
        console.error('Invalid classifications data:', result.error);
        throw new Error('Invalid response format from API');
      }
      
      return result.data;
    },
    refetchInterval: 3000,
    enabled: !!clientId,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  })
}

// Hook для отправки сообщения (test только) с обработкой ошибок
export function useSendMessage() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (data: { client_id: string; content: string }) => {
      try {
        const response = await messagesAPI.createMessage(data.client_id, data.content);
        return response.data;
      } catch (error: any) {
        // Enhanced error handling
        if (error.response?.status === 429) {
          throw new Error('Rate limit exceeded. Please wait before sending another message.');
        }
        if (error.response?.status === 400) {
          throw new Error(error.response.data?.detail || 'Invalid request');
        }
        if (error.code === 'ECONNABORTED') {
          throw new Error('Request timeout. Please check your connection.');
        }
        throw error;
      }
    },
    
    onSuccess: (data, variables) => {
      // Invalidate queries
      queryClient.invalidateQueries({
        queryKey: ['messages', variables.client_id]
      })
      queryClient.invalidateQueries({
        queryKey: ['classifications', variables.client_id]
      })
    },
    
    retry: 2, // Retry failed mutations
    retryDelay: 1000,
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
