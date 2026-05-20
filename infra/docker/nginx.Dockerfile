FROM node:22-alpine AS web-build

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml turbo.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages/shared-types/package.json packages/shared-types/package.json
COPY packages/ui-core/package.json packages/ui-core/package.json
COPY packages/api-client/package.json packages/api-client/package.json

RUN corepack pnpm install --frozen-lockfile

COPY apps/web apps/web
COPY packages packages

ARG NEXT_PUBLIC_API_URL=http://localhost:3100
ARG NEXT_PUBLIC_APP_URL=http://localhost:3100
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} \
    NEXT_PUBLIC_APP_URL=${NEXT_PUBLIC_APP_URL} \
    NODE_ENV=production

RUN corepack pnpm --filter @corp-portal/web run build

FROM nginx:1.25-alpine

RUN rm -f /etc/nginx/conf.d/default.conf

COPY infra/nginx/nginx.conf /etc/nginx/nginx.conf
COPY infra/nginx/conf.d /etc/nginx/conf.d
COPY --from=web-build /app/apps/web/out /var/www/web

EXPOSE 80
