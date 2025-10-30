/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'd3ppku6zdpgtef.cloudfront.net',
        pathname: '/**',
      },
    ],
  },
};

export default nextConfig;
