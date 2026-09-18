# ======================================================================
# DOCKERFILE - FRONTEND ANGULAR SCADA WEB (PORT SUPPORT)
# ======================================================================
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install --legacy-peer-deps || true

COPY . .

ARG PORT=4200
ENV PORT=${PORT}
EXPOSE ${PORT}

CMD ["npm", "start"]
