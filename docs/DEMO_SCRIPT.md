# Roteiro de demonstração (Global Solution)

Duração sugerida: 15–20 minutos. Tenha o sistema rodando (Docker Compose ou local) e dois perfis abertos: **paciente** e **UPA**.

## Abertura (2 min)

1. Abra o portal do paciente em `http://localhost:8080` (ou `5173`).
2. Mostre a home, o aviso de demonstração e o botão **Emergência**.
3. Reforce: "não substitui o SAMU 192".

## Cenário 1 — consulta de rotina (2 min)

1. Login paciente (`paciente@saudeflow.com.br / Paciente@123`).
2. **Preciso de atendimento** → motivo **"Preciso de uma consulta"**.
3. Conclua. Resultado **Categoria A — Atenção básica / UBS**.
4. Mostre a UBS na lista e no mapa.

## Cenário 2 — atendimento na UPA (4 min)

1. **Preciso de atendimento** → **"Estou sentindo dor"**.
2. Mostre que as perguntas mudaram (região, intensidade, sinais).
3. Conclua → **Categoria B — UPA**. Compare as duas UPAs (estimativas diferentes).
4. Selecione a **UPA Centro** e gere o protocolo `SF-...`.
5. No mesmo navegador, entre como **recepção da UPA** (`recepcao.upa@...`) e abra **Fila**.
6. Clique em **Confirmar** na solicitação.
7. Volte ao paciente e mostre a página do protocolo atualizando para **Pré-cadastro confirmado**.

## Cenário 3 — comparação de unidades (2 min)

1. Mostre que a UPA Centro tem histórico suficiente (estimativa 5–15 min) e a UPA Norte, insuficiente ("sem dados suficientes").
2. Explique que o sistema **nunca inventa** tempo sem histórico.

## Cenário 4 — ferimento grave (2 min)

1. Questionário → **"Estou com algum ferimento"** → causa **"arma branca"** → sangramento intenso.
2. A tela de emergência aparece com **SAMU 192** e o fluxo é interrompido (sem fila virtual).

## Cenário 5 — paciente a caminho do hospital (3 min)

1. Login hospital (`hospital@saudeflow.com.br / Hosp@123`) → Dashboard mostra **1 paciente a caminho**.
2. No portal do paciente, **Emergência → já estou a caminho → enviar pré-alerta** para o hospital.
3. No hospital, **Confirmar** o alerta; o paciente vê a confirmação.

## Cenário 6 — alteração de capacidade (2 min)

1. Como recepção, abra **Capacidade** e reduza profissionais para 1.
2. Mostre a estimativa aumentando. Depois restaure para 6.

## Cenário 7 — dados insuficientes

1. Abra a **UPA Norte**: "Não há dados suficientes para estimar a espera".

## Cenário 8 — falha de comunicação

1. No navegador, abra o painel do paciente e desconecte o WebSocket (ou pare o backend).
2. O selo muda para "Tempo real indisponível — atualizando por consulta" e a página continua atualizando por polling.

## Cenário 9 — respostas ambíguas

1. Questionário: responda **apenas o texto livre**, sem motivo.
2. Resultado: **fallback conservador** (Categoria B), baixa confiança e "avaliação profissional necessária".

## Encerramento

- Mostre o **Admin** → Integrações: sincronizações reais de CNES/DATASUS e o cache de unidades.
- Reforce as limitações médicas e legais e a necessidade de validação clínica/institucional.
