"use client"

interface ClientDetailPageProps {
  params: {
    clientId: string
  }
}

export default function ClientDetailPage({ params }: ClientDetailPageProps) {
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Client: {params.clientId}</h2>
      <p className="text-gray-600">Client detail page will be implemented in next prompt</p>
    </div>
  )
}

