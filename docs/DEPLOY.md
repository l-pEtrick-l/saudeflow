# Deploy na web (Render)

## Deploy real (executado em 19/11/2026)

- **URL:** https://saudeflow-fiap.onrender.com
- **Repositório:** https://github.com/l-pEtrick-l/saudeflow (público)
- **Web service:** `srv-dbvil22vcj2c73d2d6gg` (Python, plan free, região ohio)
- **PostgreSQL:** `dpg-dbvijrqfngtc73cd3oqg-a` (plan free; expira em 30 dias)
- **Python:** fixado em 3.11 via `.python-version` (o default 3.14 não tem wheels dos pins)
- **Env:** `DATABASE_URL` (interna do banco), `SECRET_KEY` (gerada), `CORS_ORIGINS=*`, `SYNC_ENABLED=false`, `DEMO_MODE=true`

## Arquitetura de deploy

- **Web service (Python)**: FastAPI servindo a API em `/api/v1` e o frontend construído em `frontend/dist` (SPA).
- **PostgreSQL gerenciado** (plano free, 1 GB, expira em 30 dias).
- Build: `pip install -r backend/requirements.txt` (o frontend já vai construído no repositório).
- Start: `cd backend && alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

## Via Blueprint (1 clique)

1. Crie conta no Render e conecte seu GitHub.
2. Em *New* → *Blueprint*, aponte este repositório.
3. O `render.yaml` cria o web service + o banco.

## Via API (o que foi usado)

1. Repositório público no GitHub com o código (`frontend/dist` incluído).
2. Token de API do Render.
3. `POST /v1/postgresql` (banco free) e `POST /v1/services` (web, `repo` = URL do GitHub),
   com `rootDir: "."`, `buildCommand`, `startCommand` e `envVars` (`DATABASE_URL` do banco,
   `SECRET_KEY`, `CORS_ORIGINS=*`, `SYNC_ENABLED=false`).

## Observações

- O serviço **free hiberna** após inatividade: a primeira requisição pode demorar ~30–60 s.
- O Postgres free **expira em 30 dias**. Para algo permanente, use Neon/Supabase (grátis, sem expiração) e defina `DATABASE_URL` manualmente.
- `SECRET_KEY` é gerada automaticamente; nunca use a do `.env.example` em produção.
