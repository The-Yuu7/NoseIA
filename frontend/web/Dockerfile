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

HEALTHCHECK --interval=5s --timeout=3s --start-period=3s --retries=5 \
    CMD node -e "const http = require('http'); const port = process.env.PORT || 4200; http.get('http://127.0.0.1:' + port + '/', (res) => res.statusCode < 400 ? process.exit(0) : process.exit(1)).on('error', () => process.exit(1));" || exit 1

CMD ["npm", "start"]
