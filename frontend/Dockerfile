FROM node:18-alpine as builder

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci

COPY . .

ENV NEXT_PUBLIC_API_URL=/api

RUN npm run build

FROM node:18-alpine

WORKDIR /app

COPY --from=builder /app/node_modules ./node_modules

COPY --from=builder /app/.next ./.next

COPY --from=builder /app/public ./public

COPY --from=builder /app/package.json ./

ENV NODE_ENV=production

ENV NEXT_PUBLIC_API_URL=/api

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

CMD ["npm", "start"]
