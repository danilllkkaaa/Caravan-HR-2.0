/** @type {import('next').NextConfig} */
const withPWA = require('@ducanh2912/next-pwa').default({
  dest: 'public',
  disable: process.env.NODE_ENV === 'development',
  register: true,
  skipWaiting: true,
  reloadOnOnline: true,
  cacheOnFrontEndNav: true,
  fallbacks: {
    document: '/offline',
  },
  runtimeCaching: [
    {
      urlPattern: /^https?:\/\/.*\/api\/v1\/auth\/.*/,
      handler: 'NetworkOnly',
      options: {
        cacheName: 'api-auth',
      },
    },
    {
      urlPattern: /^https?:\/\/.*\/api\/v1\/dashboard/,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'api-dashboard',
        expiration: { maxEntries: 1, maxAgeSeconds: 60 * 5 },
      },
    },
    {
      urlPattern: /^https?:\/\/.*\/api\/v1\/vacations/,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'api-vacations',
        expiration: { maxEntries: 20, maxAgeSeconds: 60 * 10 },
      },
    },
    {
      urlPattern: /^https?:\/\/.*\/api\/v1\/timesheet/,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'api-timesheet',
        expiration: { maxEntries: 12, maxAgeSeconds: 60 * 10 },
      },
    },
    {
      urlPattern: /^https?:\/\/.*\/api\/v1\/notifications/,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'api-notifications',
        expiration: { maxEntries: 1, maxAgeSeconds: 60 * 2 },
      },
    },
  ],
});

const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  output: 'export',
  trailingSlash: true,

  // Transpile workspace packages
  transpilePackages: ['@corp-portal/shared-types', '@corp-portal/ui-core'],

  // Environment variables available in browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
  },

  // Image optimization
  images: {
    domains: ['localhost', 'minio', 'cdn.corp-portal.ru'],
    formats: ['image/avif', 'image/webp'],
    unoptimized: true,
  },

  // Security headers are applied by infra/nginx/conf.d/portal.conf.
};

module.exports = withPWA(nextConfig);
