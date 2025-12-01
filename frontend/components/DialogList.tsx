'use client'

import { useQuery } from '@tanstack/react-query'
import { dialogsApi } from '@/lib/api'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { formatDistanceToNow } from 'date-fns'
import { ru } from 'date-fns/locale'
import { DialogStatusBadge } from './DialogStatusBadge'

interface DialogListProps {
  onSelectDialog: (clientId: string) => void
  selectedClientId?: string
}

export function DialogList({ onSelectDialog, selectedClientId }: DialogListProps) {
  const { data: dialogs, isLoading } = useQuery({
    queryKey: ['dialogs', 'open'],
    queryFn: () => dialogsApi.list('open').then(res => res.data),
    refetchInterval: 10000, // Refresh every 10 seconds
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500">Загрузка диалогов...</div>
      </div>
    )
  }

  if (!dialogs || dialogs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <p className="text-lg mb-2">Нет активных диалогов</p>
        <p className="text-sm">Ожидание обращений клиентов...</p>
      </div>
    )
  }

  // Sort: Telegram clients first, then by last activity
  const sortedDialogs = [...dialogs].sort((a, b) => {
    const aIsTelegram = a.client_id.startsWith('telegram_')
    const bIsTelegram = b.client_id.startsWith('telegram_')
    if (aIsTelegram && !bIsTelegram) return -1
    if (!aIsTelegram && bIsTelegram) return 1
    return new Date(b.last_activity_at).getTime() - new Date(a.last_activity_at).getTime()
  })

  return (
    <div className="space-y-2 overflow-y-auto">
      {sortedDialogs.map((dialog) => (
        <Card
          key={dialog.client_id}
          className={`p-4 cursor-pointer transition-all hover:shadow-md ${
            selectedClientId === dialog.client_id
              ? 'border-blue-500 bg-blue-50'
              : 'hover:border-gray-300'
          }`}
          onClick={() => onSelectDialog(dialog.client_id)}
        >
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h4 className="font-semibold text-sm font-mono truncate">
                  {dialog.client_id}
                </h4>
                <DialogStatusBadge status={dialog.status} />
              </div>
              
              {dialog.last_message_preview && (
                <p className="text-sm text-gray-600 truncate mb-1">
                  {dialog.last_message_preview}
                </p>
              )}
              
              <div className="flex items-center gap-3 text-xs text-gray-500">
                {dialog.message_count !== undefined && (
                  <span>{dialog.message_count} сообщений</span>
                )}
                {dialog.last_message_at && (
                  <span>
                    {formatDistanceToNow(new Date(dialog.last_message_at), {
                      addSuffix: true,
                      locale: ru,
                    })}
                  </span>
                )}
              </div>
            </div>
          </div>
        </Card>
      ))}
    </div>
  )
}

