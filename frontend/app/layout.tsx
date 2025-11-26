import type { Metadata } from "next"
import "./styles/globals.css"
import { Providers } from "./providers"
import Link from "next/link"

export const metadata: Metadata = {
  title: "AI Customer Support",
  description: "First-line customer support powered by AI",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <nav className="bg-gray-900 text-white p-4">
            <div className="max-w-7xl mx-auto flex items-center gap-8">
              <h1 className="text-xl font-bold">🤖 AI Support</h1>
              <div className="flex gap-6">
                <Link href="/dashboard" className="hover:text-gray-300">Dashboard</Link>
                <Link href="/search" className="hover:text-gray-300">Search</Link>
                <Link href="/analytics" className="hover:text-gray-300">Analytics</Link>
                <Link href="/admin" className="hover:text-gray-300">Admin</Link>
              </div>
            </div>
          </nav>
          <main className="min-h-screen bg-gray-50">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  )
}

