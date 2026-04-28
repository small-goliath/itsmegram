import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: "http://localhost:8000/api/v1/:path*",
      },
    ];
  },
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "instagram.com" },
      { protocol: "https", hostname: "cdninstagram.com" },
      { protocol: "https", hostname: "**.instagram.com" },
      { protocol: "https", hostname: "scontent-*.instagram.com" },
      { protocol: "https", hostname: "scontent.*.instagram.com" },
      { protocol: "https", hostname: "**.cdninstagram.com" },
    ],
    formats: ["image/webp", "image/avif"],
    minimumCacheTTL: 3600,
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
  compress: true,
  productionBrowserSourceMaps: false,
  experimental: {
    optimizePackageImports: ["framer-motion", "lucide-react"],
  },
  poweredByHeader: false,
  reactStrictMode: true,
};

export default nextConfig;
