# SaúdeFlow

Plataforma web full-stack para orientação inteligente de acesso à saúde, filas virtuais e pré-alertas — Global Solution FIAP.

> **Demonstração acadêmica.** Não substitui médicos, classificação de risco presencial, regulação médica ou SAMU 192. Dados de demonstração; nenhuma integração real com RNDS, SAMU ou prontuários.

---

## O que faz

1. **Orientação inteligente** — questionário dinâmico e adaptativo; motor de regras versionado, determinístico e conservador (categorias A/B/C/D).
2. **Unidades compatíveis** — UBS, UPA, hospital e pronto-socorro com serviços, distância aproximada e estimativa de espera operacional.
3. **Pré-cadastro e protocolo** — protocolo único `SF-AAAA-NNNNNN`, fila digital administrativa e acompanhamento em tempo real.
4. **Pré-alerta de emergência** — paciente avisa a unidade que está a caminho; unidade confirma recebimento.
5. **Portais** — Paciente, UPA, Hospital e Administração, com RBAC.
6. **Integrações externas** — CNES, DATASUS Hospitais e Leitos, IBGE, ViaCEP e OSRM, com cache local e agendamento.

## Stack

| Camada | Tecnologias |
| --- | --- |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query, React Hook Form, Zod, Recharts, Leaflet |
| Backend | Python 3.11, FastAPI, SQLAlchemy, Alembic, Pydantic, JWT, bcrypt, WebSocket |
| Banco | PostgreSQL (Docker) / SQLite (desenvolvimento local) |
| Infra | Docker, Docker Compose, nginx |
| Testes | pytest (42 testes), TestClient, testes de motor e estimativas |

## Como executar

### Opção A — Docker Compose (recomendado para a banca)

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:8080
- API: http://localhost:8000/api/v1 — documentação interativa em http://localhost:8000/docs

O Compose sobe PostgreSQL, roda as migrations, executa o seed de demonstração e inicia backend e frontend.

### Opção B — Local sem Docker

```bash
# Backend
cd backend
uv venv --python 3.11 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.venv/Scripts/python.exe -m app.seed
.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000

# Frontend (outro terminal)
cd frontend
npm install
npm run dev   # http://localhost:5173 (proxy /api -> 8000)
```

Windows (PowerShell): `scripts/start.ps1`. Linux/macOS: `scripts/start.sh`.

## Contas de demonstração

> **Não precisa cadastrar nada para explorar.** No topo de qualquer página pública há a faixa **“Acesso rápido (demonstração)”** com os botões **Paciente**, **UPA**, **Visão Hospital** e **Admin** — um clique já entra no portal correspondente. A home também tem a seção “Acesso rápido de demonstração”.

| Papel | E-mail | Senha |
| --- | --- | --- |
| Administrador | `admin@saudeflow.com.br` | `Admin@123` |
| Gestora UPA | `gestor.upa@saudeflow.com.br` | `Upa@123` |
| Recepção UPA | `recepcao.upa@saudeflow.com.br` | `Upa@123` |
| Classificador | `classificador.upa@saudeflow.com.br` | `Upa@123` |
| Operador UPA Norte | `operador.norte@saudeflow.com.br` | `Upa@123` |
| Hospital | `hospital@saudeflow.com.br` | `Hosp@123` |
| Paciente | `paciente@saudeflow.com.br` | `Paciente@123` |

## Testes

```bash
cd backend
PYTHONPATH=. .venv/Scripts/python.exe -m pytest -q
# 42 passed
```

Cobrem: motor de orientação (puro), estimativas, API, RBAC, cenários de demonstração e adaptadores de integração.

## Estrutura

```
SaudeFlow/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # roteadores (auth, units, questionnaires, requests, queues, alerts, ...)
│   │   ├── models/          # modelos SQLAlchemy
│   │   ├── schemas/         # Pydantic
│   │   ├── repositories/    # acesso a dados
│   │   ├── services/        # regras de negócio (inclui guidance_engine)
│   │   ├── integrations/    # adaptadores CNES, DATASUS, IBGE, ViaCEP, OSRM
│   │   ├── realtime.py      # WebSocket + event bus
│   │   ├── seed.py          # dados de demonstração
│   │   └── main.py
│   ├── alembic/             # migrations
│   └── tests/
├── frontend/src/
│   ├── components/          # UI (estilo shadcn), layouts, mapa
│   ├── lib/                 # api, auth, ws, format, types
│   └── pages/               # public, patient, upa, hospital, admin
├── docs/                    # arquitetura, dados, API, integrações, roteiro
└── docker-compose.yml
```

## Demo offline (para enviar a alguém)

Pasta `demo-estatica/` (ou o `demo-estatica.zip` pronto): versão que **abre com 2 cliques no `index.html`**, sem backend, sem internet e sem cadastro. Ideal para mandar no WhatsApp e a pessoa descompactar e abrir.

Conteúdo: fluxo do paciente (questionário → orientação → unidade → protocolo → acompanhamento), pré-alerta, portal da UPA, visão do hospital, admin e tela de emergência — com dados simulados no navegador.

## Projeto completo (1 clique, para enviar a alguém)

`SaudeFlow-completo.zip` (~470 KB): a pessoa **descompacta e dá 2 cliques em `ABRIR-PROJETO.bat`**. O script baixa Python/dependências na primeira vez (internet), roda as migrations, semeia os dados e abre **http://localhost:8000** com o sistema inteiro (backend + frontend + banco + tempo real). **Sem Docker, sem Node, sem instalar nada manualmente.**

- Windows: `ABRIR-PROJETO.bat` (veja `INICIAR.txt`).
- macOS/Linux: `bash start-standalone.sh`.
- Contas e detalhes estão no `INICIAR.txt` e no `README.md`.

## Documentação

- [Arquitetura e diagramas](docs/ARCHITECTURE.md)
- [Modelo de dados](docs/DATA_MODEL.md)
- [API](docs/API.md)
- [Integrações externas — o que funciona](docs/INTEGRATIONS.md)
- [Roteiro de demonstração](docs/DEMO_SCRIPT.md)
- [Segurança e LGPD](docs/SECURITY.md)
- [Limitações médicas e legais](docs/LIMITATIONS.md)

## Avisos

- O protocolo digital **não** garante prioridade clínica, horário ou atendimento.
- A confirmação de recebimento pela unidade **não** é aceitação clínica, reserva de leito ou garantia.
- Estimativas são operacionais, arredondadas e sempre acompanhadas do horário de atualização.
- Em emergência grave, ligue **192**.
