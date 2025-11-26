import type { Metadata } from "next"
import "./styles/globals.css"
import { Providers } from "./providers"

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
          <nav className="bg-gray-900 text-white p-4 flex items-center gap-8">
            <h1 className="text-xl font-bold">AI Support</h1>
            <div className="flex gap-4">
              <a href="/dashboard" className="hover:text-gray-300">Dashboard</a>
              <a href="/admin" className="hover:text-gray-300">Admin</a>
            </div>
          </nav>
          <main>
            {children}
          </main>
        </Providers>
      </body>
    </html>
  )
}

