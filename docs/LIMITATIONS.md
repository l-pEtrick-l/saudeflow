# Limitações médicas e legais

## O sistema **não** faz

- Não diagnostica, não classifica risco automaticamente e não atribui cores oficiais de triagem.
- Não substitui classificação de risco presencial por profissional de saúde.
- Não aciona ambulância, não fala com o SAMU e não define unidade de destino.
- Não reserva leito, não garante horário e não confere prioridade clínica.
- Não substitui regulação médica nem prontuário oficial.
- Não usa IA generativa para decidir gravidade ou destino de emergência.

## Regras de orientação

- São **exemplos acadêmicos conservadores**, versionados (`2026.1-academico-v1`).
- Determinísticos: mesmas regras + mesmas respostas → mesmo resultado.
- Ausência de sinais de alerta **não** conclui que o caso é seguro.
- Respostas incompletas, contraditórias ou ambíguas geram orientação conservadora.
- Toda orientação deixa claro que a prioridade é definida por profissionais.

## Estimativas

- Cálculo explicável: mediana dos tempos recentes × taxa de processamento (profissionais).
- Faixas arredondadas (ex.: 40–70 min), nunca precisão falsa.
- Sem histórico mínimo: "Não há dados suficientes para estimar a espera."
- Sempre com horário da última atualização e aviso de que não é garantia.

## Integrações

- CNES/DATASUS são dados cadastrais com data de atualização; **não** são ocupação em tempo real.
- RNDS, SAMU e prontuários **não** estão integrados (exigem credenciais e autorização).
- Filas, tempos e pré-alertas da demonstração são simulados no banco próprio.

## Para uso real

Será necessária validação clínica, revisão jurídica/institucional, governança de dados (LGPD), credenciais oficiais e integração com sistemas autorizados.
