# API — SaúdeFlow

Base: `/api/v1`. Documentação OpenAPI interativa: `/docs` (Swagger) e `/redoc`.

## Autenticação

`POST /auth/register` e `POST /auth/login` retornam `access_token` (JWT, Bearer) e `refresh_token`.
`POST /auth/refresh` renova. `GET /auth/me` retorna o perfil.

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"paciente@saudeflow.com.br","password":"Paciente@123"}'
```

## Endpoints principais

### Públicos
| Método | Rota | Descrição |
| --- | --- | --- |
| GET | `/units` | Lista unidades (filtros `type`, `city`, `state`, `q`, `lat`, `lon`) enriquecida com estimativa e fila digital |
| GET | `/units/{id}` | Detalhe da unidade |
| GET | `/units/{id}/estimate` | Estimativa operacional (`recompute=true` recalcula) |
| GET | `/questionnaires/active` | Inicia questionário (submissão + primeiras perguntas) |
| POST | `/questionnaires/versions/{id}/next` | Próximas perguntas visíveis dado o mapa de respostas |
| GET | `/requests/track/{protocol}` | Acompanhamento público e limitado (sem relatos de saúde) |
| GET | `/integrations/external-units` | Cache de CNES/DATASUS |
| GET | `/integrations/viacep/{cep}` | ViaCEP com cache |
| GET | `/integrations/ibge/municipios?uf=` | Municípios IBGE com cache |
| GET | `/integrations/route?from_lat=...` | Rota OSRM com cache |

### Paciente (Bearer)
| Método | Rota |
| --- | --- |
| POST | `/questionnaires/submissions` |
| POST | `/questionnaires/submissions/{id}/answers` |
| POST | `/questionnaires/submissions/{id}/complete` |
| GET | `/questionnaires/submissions/{id}/result` |
| POST | `/requests` (cria solicitação + ticket) |
| GET | `/requests` / `/requests/{id}` / `/requests/{id}/timeline` |
| POST | `/requests/{id}/cancel` |
| POST | `/alerts` (pré-alerta) |
| GET | `/alerts` / `/alerts/{id}` |
| GET | `/notifications` |

### UPA / Hospital (papéis de unidade)
| Método | Rota |
| --- | --- |
| GET | `/units/{id}/queue/board` |
| POST | `/units/{id}/queue/call-next` |
| POST | `/requests/{id}/confirm-receipt` |
| POST | `/requests/{id}/checkin` |
| POST | `/requests/{id}/care-start` / `care-finish` |
| POST | `/units/{id}/capacity` |
| GET | `/units/{id}/capacity` |
| PATCH | `/alerts/{id}` / POST `/alerts/{id}/confirm` |
| GET | `/analytics/units/{id}` / `/analytics/hospitals/{id}` |

### Administração
| Método | Rota |
| --- | --- |
| GET | `/analytics/overview` |
| GET/POST/PATCH | `/users`, `/users/{id}`, `/users/{id}/roles` |
| POST | `/units`, PATCH `/units/{id}`, POST `/units/{id}/active` |
| GET/POST | `/integrations/sources`, `/integrations/sync`, `/integrations/sync-logs` |
| POST | `/integrations/external-units/{id}/promote` |
| GET | `/audit-logs` |

### Tempo real
`WebSocket /api/v1/ws?token=...&channels=request:<id>,unit:<id>` — eventos `request_status`, `queue_updated`, `alert_status`, `alert_received`, `capacity_updated`. O frontend faz fallback por polling.

## Respostas de erro

```json
{ "error": { "code": "not_found", "message": "...", "details": {} } }
```

## Rate limiting

Limitador em memória por IP/rota (padrão 120 req/min; ViaCEP/OSRM 30–60 req/min).
