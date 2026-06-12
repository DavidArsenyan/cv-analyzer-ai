import type { NextConfig } from "next";

const internalApiUrl = process.env.INTERNAL_API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/health",
        destination: `${internalApiUrl}/health`,
      },
    ];
  },
};

export default nextConfig;
