import { useQuery } from "@tanstack/react-query"
import { messagesAPI } from "@/lib/api"
import { Message } from "@/lib/types"

export function useMessages(clientId: string) {
  return useQuery<Message[]>({
    queryKey: ["messages", clientId],
    queryFn: async () => {
      const response = await messagesAPI.getClientMessages(clientId)
      return response.data
    },
    enabled: !!clientId,
  })
}

