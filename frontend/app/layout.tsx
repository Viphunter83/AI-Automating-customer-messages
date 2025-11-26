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
          <nav className="bg-gray-900 text-white p-4">
            <h1 className="text-xl font-bold">AI Support Dashboard</h1>
          </nav>
          <main className="p-8">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  )
}

