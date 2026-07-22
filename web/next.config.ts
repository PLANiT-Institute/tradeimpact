import type { NextConfig } from "next";

// In local dev the Python function isn't served by `next dev`; point /api/compute at a
// local compute server (scripts/dev_compute.py) via TI_COMPUTE_URL. On Vercel the
// platform serves web/api/compute.py directly and this rewrite never matches first.
const computeUrl = process.env.TI_COMPUTE_URL;

const nextConfig: NextConfig = {
  async rewrites() {
    return computeUrl ? [{ source: "/api/compute", destination: computeUrl }] : [];
  },
};

export default nextConfig;
