import { useQuery } from "@tanstack/react-query"

export function useClientChat(clientId: string) {
  // TODO: Implement in next prompt
  return useQuery({
    queryKey: ["clientChat", clientId],
    queryFn: async () => {
      return { messages: [] }
    },
    enabled: !!clientId,
  })
}

