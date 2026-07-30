# Container build for the Next.js frontend. Vercel is the recommended
# production target (see README.md) — this Dockerfile exists mainly for
# docker-compose local dev and as a fallback if you'd rather self-host.
FROM node:22-slim AS base

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 3000
ENV PORT=3000
CMD ["npm", "start"]
