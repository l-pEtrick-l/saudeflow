# Integrações externas — status

Princípio: **nenhuma consulta externa é feita a cada acesso do usuário**. Os dados ficam em cache no banco do SaúdeFlow (tabelas `external_units` e `integration_settings`), com origem e data de atualização registradas.

## Status das integrações

| Fonte | Status | Uso no sistema | Observação |
| --- | --- | --- | --- |
| **CNES — Estabelecimentos (MS/DATASUS)** | ✅ Funcionando (verificado) | Importa estabelecimentos por UF para o cache; admin pode promover a unidade | API `apidadosabertos.saude.gov.br/cnes/estabelecimentos`. Paginação de 20 em 20. O filtro `codigo_municipio` retornou vazio nos testes; usamos `codigo_uf` |
| **DATASUS — Hospitais e Leitos** | ✅ Funcionando (verificado) | Enriquece cadastro hospitalar com leitos totais/SUS e endereço | **Não fornece ocupação em tempo real** — apenas cadastro e leitos por competência |
| **IBGE — Localidades** | ✅ Funcionando | Padroniza municípios/UF e códigos geográficos | Cache por UF |
| **ViaCEP** | ✅ Funcionando | Preenchimento de endereço por CEP | Cache por CEP |
| **OSRM + OpenStreetMap/Leaflet** | ✅ Funcionando | Mapa e cálculo de rota | Distância em linha reta por padrão; rota quando OSRM disponível. Servidor demo público tem limites |
| **RNDS / SAMU / prontuários** | ⛔ Não implementado | — | Exige credenciais e autorização institucional. Não simulamos |

## Verificação realizada

Sincronização real executada em 19/11/2026:

```
CNES:    success  fetch 60   ins 60   upd 0
DATASUS: success  fetch 100  ins 100  upd 0
total de registros externos em cache: 160
```

## Adaptadores

`app/integrations/adapters.py`:

- `CNESAdapter` — `/cnes/tipounidades` + `/cnes/estabelecimentos` (converte sigla de UF para código IBGE).
- `DatasusHospitaisLeitosAdapter` — `/assistencia-a-saude/hospitais-e-leitos`.
- `IbgeAdapter` — `/localidades/estados/{uf}/municipios`.
- `ViaCepAdapter` — `/{cep}/json/`.
- `OsrmAdapter` — `/route/v1/driving/...`.

Cada adaptador tem **rate limiter** próprio e tratamento de indisponibilidade. A sincronização registra `sync_logs` com status, contagens e erro, e **nunca** derruba a aplicação.

## Agendamento

`SYNC_ENABLED=true` habilita sincronização periódica (padrão 360 min) em thread separada. Também é possível disparar manualmente por `POST /api/v1/integrations/sync`.

## O que é demonstrativo

- As **filas, tempos de espera e pré-alertas** usam dados simulados no banco próprio. As estimativas não são informações oficiais em tempo real.
- Unidades de demonstração são marcadas com `is_simulated=true` e exibem o selo "Simulada".
- Dados de CNES/DATASUS no cache são **reais**, mas com data de atualização própria; não representam ocupação atual.
