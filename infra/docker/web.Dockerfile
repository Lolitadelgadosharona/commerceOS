FROM node:22.14.0-alpine AS dependencies
WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

FROM node:22.14.0-alpine AS build
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY apps/web ./
RUN npm run build

FROM node:22.14.0-alpine AS runtime
ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
WORKDIR /app
RUN addgroup --system commerce && adduser --system --ingroup commerce commerce
COPY --from=build --chown=commerce:commerce /app/.next/standalone ./
COPY --from=build --chown=commerce:commerce /app/.next/static ./.next/static
USER commerce
EXPOSE 3000
CMD ["node", "server.js"]
