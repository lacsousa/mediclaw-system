import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Build "standalone": empacota só o necessário para rodar em produção
  // (usado pelo Dockerfile.prod em cima de node:20-slim).
  output: "standalone",
  experimental: {
    optimizePackageImports: ["@chakra-ui/react"],
  },
};

export default nextConfig;
