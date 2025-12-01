/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    esmExternals: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
  eslint: {
    // Don't fail build on ESLint warnings during production builds
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Don't fail build on TypeScript errors during production builds
    ignoreBuildErrors: true,
  },
}

module.exports = nextConfig

