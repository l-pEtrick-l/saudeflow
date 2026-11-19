# Segurança e privacidade (LGPD)

## Medidas implementadas

- **Autenticação JWT** com expiração; refresh token separado; senha com **bcrypt**.
- **RBAC** com papéis e permissões; autoria de ações registrada.
- **Escopo por unidade**: usuários de UPA/hospital só veem dados das suas unidades.
- **Validação de entrada** com Pydantic em todos os endpoints.
- **Rate limiting** por IP/rota.
- **Auditoria** de ações relevantes (quem, o quê, quando, IP).
- **Não exponha relatos de saúde em URL**: o acompanhamento público por protocolo retorna apenas status/unidade/estimativa.
- **Erros padronizados** que não vazam valores enviados pelo cliente.
- **Segredos por variável de ambiente**; `.env` ignorado pelo git.
- **CORS** restrito às origens configuradas.
- **Comunicação** deve usar HTTPS em produção (Docker Compose local é HTTP).

## LGPD — pontos de atenção

- Dados de saúde são **sensíveis** (art. 5º, II + art. 11). A demo usa apenas dados fictícios.
- **Minimização**: coletamos só o necessário para a orientação e o pré-cadastro.
- **Consentimento**: um termo isolado **não** torna o tratamento adequado; é preciso base legal (legítimo interesse, saúde pública, execução de política pública) e governança.
- **Retenção e eliminação**: defina prazos; há soft delete em usuários/unidades, mas é preciso política de retenção formal.
- **Direitos do titular**: canais de acesso, correção e exclusão precisam ser institucionalizados.
- **Relatório de impacto (RIPD)** e revisão jurídica são recomendados antes de qualquer uso real.

## Limites da demo

- Sem criptografia de colunas, sem anonimização, sem DPO, sem contrato de operação de dados.
- O ambiente local usa SQLite; produção deve usar PostgreSQL com backup e TLS.
