FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
COPY . .
# CI: no hay dist → npm install + npm run build
# Local: dist/ ya generado → se reutiliza (evita npm flaky en el daemon)
RUN if [ -d dist/frontend-angular-scada/browser ] || [ -d dist/frontend-angular-crud/browser ]; then \
      echo "Using prebuilt dist from context"; \
    else \
      npm install --no-audit --no-fund && npm run build || true; \
    fi

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/scripts/serve.mjs ./scripts/serve.mjs

ARG PORT=4200
ENV PORT=${PORT}
EXPOSE ${PORT}

HEALTHCHECK --interval=5s --timeout=3s --start-period=3s --retries=5 \
  CMD node -e "fetch('http://127.0.0.1:'+(process.env.PORT||4200)+'/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))" || exit 1

CMD ["node", "scripts/serve.mjs"]
