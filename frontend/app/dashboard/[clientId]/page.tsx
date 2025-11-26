"use client"

export default function ClientDetailPage({ params }: { params: { clientId: string } }) {
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Client: {params.clientId}</h2>
      <p className="text-gray-600">Client detail page will be implemented in next prompt</p>
    </div>
  )
}

