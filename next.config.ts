import type { NextConfig } from "next";

const BACKEND =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.RAIMON_BACKEND_URL ||
  "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      // FE calls /api/* -> forwards to FastAPI /api/*
      {
        source: "/api/:path*",
        destination: `${BACKEND}/api/:path*`,
      },

      // Optional but VERY useful for testing the pipe:
      {
  source: "/health",
  destination: `${BACKEND}/api/health`,
},
    ];
  },
};

export default nextConfig;
