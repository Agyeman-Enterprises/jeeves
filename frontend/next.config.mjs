/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  experimental: {
    webpackBuildWorker: true,
  },

  turbopack: {},

  webpack(config, { isServer }) {
    config.externals = config.externals || [];

    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        child_process: false,
        net: false,
        tls: false,
        path: false,
      };
    }

    if (isServer) {
      config.externals.push({
        "@nut-tree-fork/nut-js": "commonjs @nut-tree-fork/nut-js",
        fs: "commonjs fs",
        path: "commonjs path",
        child_process: "commonjs child_process",
      });
    }

    return config;
  },
};

export default nextConfig;
