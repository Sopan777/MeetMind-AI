import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Required for ONNX Runtime WASM and VAD model files
  async headers() {
    return [
      {
        source: "/:path*.wasm",
        headers: [
          {
            key: "Content-Type",
            value: "application/wasm",
          },
        ],
      },
      {
        source: "/:path*.onnx",
        headers: [
          {
            key: "Content-Type",
            value: "application/octet-stream",
          },
        ],
      },
    ];
  },
  // Empty turbopack config to silence Turbopack warning
  turbopack: {},
};

export default nextConfig;
