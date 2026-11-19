# Arquitetura

Monólito modular: um backend FastAPI com módulos bem delimitados e um frontend React. Sem microsserviços.

## 1. Arquitetura geral

```mermaid
flowchart TB
    subgraph Cliente["Cliente (mobile-first)"]
        P["Portal do Paciente"]
        U["Portal da UPA"]
        H["Portal do Hospital"]
        A["Administração"]
    end

    subgraph Gateway["Camada de apresentação"]
        NG["nginx / Vite"]
    end

    subgraph API["FastAPI (monólito modular)"]
        AUTH["Auth + RBAC"]
        Q["Questionários"]
        G["Care Guidance"]
        R["Requests"]
        QE["Queues"]
        ES["Estimates"]
        AL["Emergency Alerts"]
        NT["Notifications"]
        AN["Analytics"]
        IT["Integrations"]
        AU["Audit"]
        WS["WebSocket / EventBus"]
    end

    subgraph Dados["Dados"]
        PG[("PostgreSQL")]
        EXT[("cache external_units")]
        SET[("integration_settings")]
    end

    subgraph Externos["Fontes externas (cache)"]
        CNES["CNES / DATASUS"]
        IBGE["IBGE"]
        CEP["ViaCEP"]
        OSRM["OSRM"]
    end

    P & U & H & A --> NG --> API
    API --> Dados
    IT --> Externos
    WS --> NG
    Q --> G
    R --> QE
    QE --> ES
    AL --> NT
```

## 2. Fluxo do paciente

```mermaid
flowchart LR
    A["Acessa o SaúdeFlow"] --> B["Motivo da procura"]
    B --> C["Questionário dinâmico"]
    C --> D["Motor de regras"]
    D --> E{"Categoria"}
    E -->|A| F["UBS compatível"]
    E -->|B| G["UPA compatível"]
    E -->|C| H["Hospital / PS orientativo"]
    E -->|D| I["Emergência: SAMU 192"]
    F & G & H --> J["Escolha da unidade"]
    J --> K["Pré-cadastro + protocolo"]
    K --> L["Unidade recebe"]
    L --> M["Acompanhamento em tempo real"]
```

## 3. Orientação de atendimento

```mermaid
flowchart TD
    IN["Respostas + texto livre"] --> FLAGS["Sinais de alerta das perguntas"]
    IN --> RULES["Regras versionadas (prioridade)"]
    FLAGS --> RULES
    RULES -->|"primeira regra que casa"| OUT["Orientação estruturada"]
    RULES -->|"nenhuma casa"| FB["Fallback conservador (B)"]
    FLAGS -->|"sinal de emergência sem regra"| EM["Emergência (D) + stop_flow"]
    OUT --> OUT2["categoria, serviço, justificativa, confiança, unidade recomendada"]
```

O motor é **puro** (`app/services/guidance_engine.py`), não depende do React e é deterministicamente testável.

## 4. Fluxo de emergência

```mermaid
flowchart TD
    E["Relato com sinal de emergência"] --> S["Interrompe o fluxo normal"]
    S --> T["Tela de emergência"]
    T --> L["Botão ligar SAMU 192 (tel:192)"]
    T --> O["Opção: já estou a caminho"]
    O --> Q["Questionário curto e opcional"]
    Q --> PA["Pré-alerta para a unidade"]
    PA --> UN["Unidade recibe em tempo real"]
    UN --> C["Confirma recebimento"]
    C --> PAC["Paciente vê a confirmação"]
```

## 5. Integração entre portais

```mermaid
sequenceDiagram
    participant Paciente
    participant API
    participant UPA
    participant Hospital

    Paciente->>API: questionário + conclusão
    API->>API: motor de regras
    Paciente->>API: cria pré-cadastro (unidade UPA)
    API->>UPA: evento em tempo real (nova solicitação)
    UPA->>API: confirma recebimento / atualiza status
    API-->>Paciente: WebSocket / polling (novo status)
    Paciente->>API: pré-alerta (a caminho do hospital)
    API->>Hospital: evento em tempo real
    Hospital->>API: confirma recebimento
    API-->>Paciente: confirmação
```

## 6. Módulos do backend

| Módulo | Responsabilidade |
| --- | --- |
| `auth` | registro, login, refresh, JWT, perfil |
| `users` | usuários, papéis e permissões (RBAC) |
| `units` | unidades, serviços, capacidade |
| `questionnaires` | versões, perguntas, opções, submissões, respostas |
| `care_guidance` | regras, resultados, motor de orientação |
| `requests` | solicitações, protocolos, eventos, status |
| `queues` | tickets, fila digital, check-in, atendimentos |
| `estimates` | cálculo e cache de estimativas |
| `emergency_alerts` | pré-alertas e confirmações |
| `notifications` | notificações internas |
| `analytics` | indicadores e relatórios |
| `integrations` | adaptadores, sincronização, cache, geolocalização |
| `audit` | trilha de auditoria |

Cada módulo segue a separação **router → service → repository → model → schema**, com testes.
