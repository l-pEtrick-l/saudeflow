/* SaúdeFlow — demonstração offline (sem backend, sem cadastro). */
(function () {
  "use strict";

  var STORAGE_KEY = "saudeflow_demo_v1";

  /* ===================== Util ===================== */
  function esc(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
  function nowLabel(d) {
    d = d || new Date();
    return d.toLocaleString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }
  function uid() {
    return "id-" + Math.random().toString(36).slice(2, 10);
  }

  /* ===================== Dados de demonstração ===================== */
  function seed() {
    var units = [
      {
        id: "ubs-1",
        name: "UBS Parque das Flores (Simulada)",
        type: "ubs",
        city: "São Paulo",
        state: "SP",
        neighborhood: "Parque das Flores",
        street: "Rua das Flores, 120",
        phone: "(11) 3555-0100",
        lat: -23.5605,
        lng: -46.6533,
        services: ["Consulta de rotina", "Vacinação", "Renovação de receitas"],
        capacity: { professionals: 2, rooms: 2, welcome: 10 },
        estimate: { reliable: false, message: "UBS não trabalha com fila de pronto atendimento." },
        simulated: true,
        source: "manual",
      },
      {
        id: "upa-centro",
        name: "UPA Centro (Simulada)",
        type: "upa",
        city: "São Paulo",
        state: "SP",
        neighborhood: "Bela Vista",
        street: "Avenida Paulista, 1000",
        phone: "(11) 3555-0200",
        lat: -23.5605,
        lng: -46.656,
        services: ["Clínico geral", "Pediatria", "Ortopedia", "Enfermagem"],
        capacity: { professionals: 6, rooms: 8, welcome: 30 },
        estimate: { reliable: true, low: 10, high: 20, p50: 30, message: "Espera estimada: 10–20 minutos." },
        simulated: true,
        source: "manual",
      },
      {
        id: "upa-norte",
        name: "UPA Norte (Simulada)",
        type: "upa",
        city: "São Paulo",
        state: "SP",
        neighborhood: "Santana",
        street: "Rua da Santana, 500",
        phone: "(11) 3555-0300",
        lat: -23.495,
        lng: -46.625,
        services: ["Clínico geral", "Enfermagem"],
        capacity: { professionals: 2, rooms: 3, welcome: 10 },
        estimate: { reliable: false, message: "Não há dados suficientes para estimar a espera." },
        simulated: true,
        source: "manual",
      },
      {
        id: "hospital-1",
        name: "Hospital Geral Simulado",
        type: "hospital",
        city: "São Paulo",
        state: "SP",
        neighborhood: "Vila Mariana",
        street: "Rua do Hospital, 200",
        phone: "(11) 3555-0400",
        lat: -23.595,
        lng: -46.64,
        services: ["Pronto-socorro", "Internação", "Centro cirúrgico", "UTI"],
        capacity: { professionals: 10, rooms: 12, welcome: 40 },
        estimate: { reliable: false, message: "Estimativa não disponível para hospitais." },
        simulated: true,
        source: "manual",
      },
      {
        id: "ps-1",
        name: "Pronto-Socorro Municipal Simulado",
        type: "emergency",
        city: "São Paulo",
        state: "SP",
        neighborhood: "Jardins",
        street: "Avenida Brasil, 300",
        phone: "(11) 3555-0500",
        lat: -23.57,
        lng: -46.665,
        services: ["Emergência adulto", "Emergência pediátrica"],
        capacity: { professionals: 8, rooms: 10, welcome: 30 },
        estimate: { reliable: false, message: "Estimativa não disponível para pronto-socorro." },
        simulated: true,
        source: "manual",
      },
    ];

    var requests = [
      mkRequest("SF-2026-000016", "Aguardando Centro 1", "upa-centro", "B", "awaiting_confirmation", 2),
      mkRequest("SF-2026-000017", "Aguardando Centro 2", "upa-centro", "B", "awaiting_confirmation", 2),
      mkRequest("SF-2026-000018", "Aguardando Norte 1", "upa-norte", "B", "awaiting_confirmation", 1),
      mkRequest("SF-2026-000019", "Aguardando Norte 2", "upa-norte", "B", "awaiting_confirmation", 1),
      mkRequest("SF-2026-000020", "Paciente Histórico", "upa-centro", "B", "finished", 3),
    ];

    var alerts = [
      {
        id: uid(),
        code: "ALERT-DEMO01",
        unitId: "hospital-1",
        description: "Paciente simulado a caminho com dor torácica. Dados não verificados clinicamente.",
        conscious: "yes",
        breathing: "yes",
        bleeding: "no",
        situation: "Estável, acompanhado por familiar.",
        eta: 20,
        flags: ["patient_on_the_way"],
        status: "confirmed",
        createdAt: new Date(Date.now() - 12 * 60000).toISOString(),
      },
    ];

    return {
      seq: 21,
      units: units,
      requests: requests,
      alerts: alerts,
      audit: [{ action: "demo.inicio", at: new Date().toISOString(), detail: "Demonstração iniciada" }],
    };
  }

  function mkRequest(protocol, patient, unitId, category, status, position) {
    return {
      id: uid(),
      protocol: protocol,
      patient: patient,
      unitId: unitId,
      category: category,
      status: status,
      position: position,
      createdAt: new Date(Date.now() - 30 * 60000).toISOString(),
      timeline: [
        { label: "Solicitação criada", at: new Date(Date.now() - 30 * 60000).toISOString() },
      ],
    };
  }

  function load() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }
  function save() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
      /* armazenamento indisponível: segue em memória */
    }
  }
  var state = load() || seed();
  save();

  function unitById(id) {
    for (var i = 0; i < state.units.length; i++) if (state.units[i].id === id) return state.units[i];
    return null;
  }
  function addAudit(action, detail) {
    state.audit.unshift({ action: action, at: new Date().toISOString(), detail: detail || "" });
    save();
  }

  var STATUS = {
    sent: "Solicitação enviada",
    awaiting_confirmation: "Aguardando confirmação",
    pre_register_confirmed: "Pré-cadastro confirmado",
    patient_arrived: "Paciente chegou",
    awaiting_welcome: "Aguardando acolhimento",
    awaiting_care: "Aguardando atendimento",
    in_care: "Em atendimento",
    finished: "Atendimento finalizado",
    cancelled: "Cancelado",
  };
  var STATUS_ORDER = ["sent", "awaiting_confirmation", "pre_register_confirmed", "patient_arrived", "awaiting_welcome", "awaiting_care", "in_care", "finished"];

  function advanceStatus(request) {
    var i = STATUS_ORDER.indexOf(request.status);
    if (i >= 0 && i < STATUS_ORDER.length - 1) {
      request.status = STATUS_ORDER[i + 1];
      request.timeline.push({ label: STATUS[request.status], at: new Date().toISOString() });
    }
    save();
  }

  /* ===================== Questionário ===================== */
  var QUESTIONS = [
    {
      id: "reason",
      text: "O que você precisa?",
      type: "single",
      required: true,
      options: ["Estou passando mal", "Estou sentindo dor", "Sofri um acidente", "Estou com algum ferimento", "Preciso de um exame", "Preciso de medicamento ou receita", "Preciso de uma consulta", "Estou acompanhando outra pessoa", "É uma situação de emergência", "Outro motivo"],
      values: ["mal_estar", "dor", "acidente", "ferimento", "exame", "medicamento", "consulta", "acompanhando", "emergencia", "outro"],
    },
    { id: "description", text: "Descreva brevemente o que está acontecendo (opcional).", type: "text", required: false },
    {
      id: "dor_regiao", text: "Onde dói?", type: "single", required: false,
      options: ["Cabeça", "Peito", "Barriga", "Costas", "Braços ou pernas", "Outra região"],
      values: ["cabeca", "peito", "barriga", "costas", "bracos_pernas", "outro"],
      showIf: { question: "reason", in: ["dor"] },
    },
    {
      id: "dor_intensidade", text: "De 0 a 10, qual a intensidade da dor?", type: "scale", required: false,
      min: 0, max: 10, showIf: { question: "reason", in: ["dor"] },
    },
    {
      id: "dor_toracica", text: "A dor é no peito ou parece pressão/falta de ar?", type: "boolean", required: false,
      showIf: { any: [{ question: "reason", eq: "dor" }, { question: "reason", eq: "mal_estar" }] },
      flagWhen: { eq: true, flag: "chest_emergency" },
    },
    {
      id: "dificuldade_respirar", text: "Há dificuldade para respirar?", type: "boolean", required: false,
      showIf: { any: [{ question: "reason", eq: "mal_estar" }, { question: "reason", eq: "dor" }, { question: "reason", eq: "emergencia" }] },
      flagWhen: { eq: true, flag: "respiratory_emergency" },
    },
    {
      id: "febre", text: "Há febre?", type: "boolean", required: false,
      showIf: { any: [{ question: "reason", eq: "mal_estar" }, { question: "reason", eq: "dor" }, { question: "reason", eq: "acompanhando" }] },
      flagWhen: { eq: true, flag: "fever" },
    },
    {
      id: "febre_temperatura", text: "Se souber, qual a temperatura (°C)?", type: "scale", required: false,
      min: 35, max: 41, showIf: { question: "febre", eq: true },
      flagWhen: { gte: 39, flag: "high_fever" },
    },
    {
      id: "vomitos", text: "Há vômitos persistentes?", type: "boolean", required: false,
      showIf: { question: "reason", eq: "mal_estar" },
    },
    {
      id: "consciencia", text: "A pessoa está consciente?", type: "boolean", required: false,
      showIf: { any: [{ question: "reason", eq: "acidente" }, { question: "reason", eq: "ferimento" }, { question: "reason", eq: "emergencia" }, { question: "reason", eq: "mal_estar" }] },
      flagWhen: { eq: false, flag: "loss_of_consciousness" },
    },
    {
      id: "respiracao", text: "A pessoa está respirando normalmente?", type: "boolean", required: false,
      showIf: { any: [{ question: "reason", eq: "acidente" }, { question: "reason", eq: "ferimento" }, { question: "reason", eq: "emergencia" }, { question: "reason", eq: "mal_estar" }] },
      flagWhen: { eq: false, flag: "respiratory_emergency" },
    },
    {
      id: "sangramento", text: "Há sangramento?", type: "boolean", required: false,
      showIf: { any: [{ question: "reason", eq: "ferimento" }, { question: "reason", eq: "acidente" }] },
    },
    {
      id: "sangramento_intenso", text: "O sangramento é intenso (não para com pressão)?", type: "boolean", required: false,
      showIf: { question: "sangramento", eq: true },
      flagWhen: { eq: true, flag: "severe_bleeding" },
    },
    {
      id: "causa_ferimento", text: "O que causou o ferimento?", type: "single", required: false,
      options: ["Corte com objeto comum", "Ferimento por arma branca", "Ferimento por arma de fogo", "Queimadura", "Queda", "Outro"],
      values: ["corte", "arma_branca", "arma_fogo", "queimadura", "queda", "outro"],
      optionFlags: { arma_branca: "weapon_injury", arma_fogo: "weapon_injury" },
      showIf: { question: "reason", eq: "ferimento" },
    },
    {
      id: "tipo_acidente", text: "Que tipo de acidente?", type: "single", required: false,
      options: ["Acidente de trânsito", "Acidente doméstico", "Acidente de trabalho", "Queda", "Outro"],
      values: ["transito", "domestico", "trabalho", "queda", "outro"],
      showIf: { question: "reason", eq: "acidente" },
    },
    {
      id: "convulsao", text: "Houve convulsão?", type: "boolean", required: false,
      showIf: { any: [{ question: "reason", eq: "mal_estar" }, { question: "reason", eq: "emergencia" }] },
      flagWhen: { eq: true, flag: "seizure" },
    },
    {
      id: "sinais_avc", text: "Há fraqueza ou formigamento em um lado do corpo?", type: "boolean", required: false,
      showIf: { any: [{ question: "reason", eq: "mal_estar" }, { question: "reason", eq: "dor" }] },
      flagWhen: { eq: true, flag: "stroke" },
    },
  ];

  var TEXT_EMERGENCY = ["arma branca", "arma de fogo", "desmai", "inconscient", "convuls", "avc", "derrame", "infart", "sem respirar", "não respira", "nao respira", "sangramento intenso", "atropel", "acidente grave"];

  function condMatches(cond, answers) {
    if (!cond) return true;
    if (cond.all) return cond.all.every(function (c) { return condMatches(c, answers); });
    if (cond.any) return cond.any.some(function (c) { return condMatches(c, answers); });
    if (cond.question) {
      var value = answers[cond.question];
      if (cond.eq !== undefined) return value === cond.eq;
      if (cond.in) {
        if (Array.isArray(value)) return value.some(function (v) { return cond.in.indexOf(v) >= 0; });
        return cond.in.indexOf(value) >= 0;
      }
      if (cond.gte !== undefined) return typeof value === "number" && value >= cond.gte;
      if (cond.lte !== undefined) return typeof value === "number" && value <= cond.lte;
      if (cond.gt !== undefined) return typeof value === "number" && value > cond.gt;
      if (cond.lt !== undefined) return typeof value === "number" && value < cond.lt;
    }
    return true;
  }

  function visibleQuestions(answers) {
    return QUESTIONS.filter(function (q) {
      if (!q.showIf) return true;
      return condMatches(q.showIf, answers);
    });
  }

  function collectFlags(answers) {
    var flags = [];
    QUESTIONS.forEach(function (q) {
      var value = answers[q.id];
      if (q.flagWhen) {
        var match = false;
        if (q.flagWhen.eq !== undefined) match = value === q.flagWhen.eq;
        if (q.flagWhen.gte !== undefined) match = typeof value === "number" && value >= q.flagWhen.gte;
        if (match && q.flagWhen.flag) flags.push(q.flagWhen.flag);
      }
      if (q.optionFlags && value && q.optionFlags[value]) flags.push(q.optionFlags[value]);
    });
    return flags.filter(function (v, i) { return flags.indexOf(v) === i; });
  }

  function evaluate(answers, freeText) {
    var flags = collectFlags(answers);
    var text = (freeText || "").toLowerCase();
    TEXT_EMERGENCY.forEach(function (word) {
      if (text.indexOf(word) >= 0) flags.push(word.replace(/ /g, "_"));
    });

    var emergency = ["weapon_injury", "loss_of_consciousness", "respiratory_emergency", "severe_bleeding", "convulsao", "seizure", "stroke", "chest_emergency", "arma_branca", "arma_de_fogo", "desmai", "inconscient", "convuls", "avc", "derrame", "infart", "sem_respirar", "nao_respira", "sangramento_intenso", "atropel", "acidente_grave"];
    var isEmergency =
      answers.reason === "emergencia" ||
      flags.some(function (f) { return emergency.indexOf(f) >= 0; });

    if (isEmergency) {
      return {
        category: "D",
        categoryLabel: "Possível emergência grave — SAMU 192",
        serviceLabel: "Emergência (SAMU 192)",
        justification: "O relato indica possível emergência. Interrompemos o pré-cadastro: procure socorro imediato ligando para o SAMU 192.",
        confidence: 0.9,
        stopFlow: true,
        needsProfessional: true,
        unitTypes: ["emergency"],
        ruleName: "emergencia_grave",
        alertFlags: flags,
        emergencyMessage: "Com base no relato, pode ser necessária ajuda imediata. Ligue agora para o SAMU 192. Este sistema não substitui o atendimento de emergência nem a regulação médica.",
      };
    }

    var hospital = ["transito", "trabalho"].indexOf(answers.tipo_acidente) >= 0 || (typeof answers.dor_intensidade === "number" && answers.dor_intensidade >= 8) || (answers.febre === true && typeof answers.febre_temperatura === "number" && answers.febre_temperatura >= 39.5);
    if (hospital) {
      return {
        category: "C",
        categoryLabel: "Possível necessidade de hospital ou pronto-socorro",
        serviceLabel: "Hospital / pronto-socorro",
        justification: "Pelo relato, pode ser necessária avaliação com recursos hospitalares. A indicação é orientativa e não substitui a regulação médica.",
        confidence: 0.65,
        stopFlow: false,
        needsProfessional: true,
        unitTypes: ["hospital", "emergency"],
        ruleName: "possivel_necessidade_hospitalar",
        alertFlags: flags,
      };
    }

    var upa = ["mal_estar", "dor", "ferimento", "acidente", "acompanhando"].indexOf(answers.reason) >= 0 || answers.febre === true || answers.vomitos === true;
    if (upa) {
      return {
        category: "B",
        categoryLabel: "Possível atendimento em UPA",
        serviceLabel: "UPA / pronto atendimento",
        justification: "Com base nas informações, uma UPA pode ser adequada para avaliação. A prioridade será definida por profissionais de saúde.",
        confidence: 0.6,
        stopFlow: false,
        needsProfessional: true,
        unitTypes: ["upa", "emergency"],
        ruleName: "possivel_atendimento_upa",
        alertFlags: flags,
      };
    }

    if (["consulta", "medicamento", "exame", "outro"].indexOf(answers.reason) >= 0) {
      return {
        category: "A",
        categoryLabel: "Atenção básica / UBS",
        serviceLabel: "Atenção básica (UBS)",
        justification: "Para esta necessidade, a atenção básica (UBS) costuma ser o caminho mais adequado. Procure a UBS mais próxima.",
        confidence: 0.7,
        stopFlow: false,
        needsProfessional: false,
        unitTypes: ["ubs"],
        ruleName: "atencao_basica",
        alertFlags: flags,
      };
    }

    return {
      category: "B",
      categoryLabel: "Possível atendimento em UPA",
      serviceLabel: "UPA / pronto atendimento",
      justification: "As respostas foram insuficientes, ambíguas ou não casaram com nenhuma regra específica. A orientação conservadora é buscar avaliação em uma UPA.",
      confidence: 0.3,
      stopFlow: false,
      needsProfessional: true,
      unitTypes: ["upa", "emergency"],
      ruleName: "fallback_conservador",
      alertFlags: flags,
    };
  }

  /* ===================== Questionário: estado ===================== */
  var qState = null;

  function startQuestionnaire() {
    qState = { answers: {}, index: 0, result: null };
    renderQuestion();
  }

  function currentQuestions() {
    return visibleQuestions(qState.answers);
  }

  function renderQuestion() {
    var questions = currentQuestions();
    var current = questions[qState.index];
    if (!current) {
      qState.result = evaluate(qState.answers, qState.answers.description);
      renderResult(qState.result);
      return;
    }
    var total = questions.length;
    var pct = Math.round(((qState.index + 1) / total) * 100);
    var html = "";
    html += '<div class="card" style="max-width:720px;margin:0 auto;">';
    html += '<div class="row" style="justify-content:space-between;color:var(--slate-500);font-size:13px;">';
    html += "<span>Pergunta " + (qState.index + 1) + " de " + total + "</span><span>" + pct + "%</span></div>";
    html += '<div class="progress" style="margin-top:8px;"><div style="width:' + pct + '%"></div></div>';
    html += '<div class="alert warning" style="margin-top:16px;">Situações graves exigem socorro imediato. Este formulário não é um serviço de emergência. Se houver risco de vida, ligue 192.</div>';
    html += '<h2 style="margin:18px 0 4px;color:var(--slate-900);font-size:22px;">' + esc(current.text) + "</h2>";

    if (current.type === "boolean") {
      html += '<div class="grid cols-2" style="margin-top:16px;">';
      html += '<button class="btn success" onclick="qAnswer(true)">Sim</button>';
      html += '<button class="btn secondary" onclick="qAnswer(false)">Não</button></div>';
    } else if (current.type === "single") {
      html += '<div style="margin-top:16px;">';
      current.options.forEach(function (label, i) {
        html += '<button class="option" onclick="qAnswer(' + JSON.stringify(current.values[i]).replace(/"/g, "&quot;") + ')">' + esc(label) + "<span>→</span></button>";
      });
      html += "</div>";
    } else if (current.type === "scale") {
      html += '<div style="margin-top:16px;">';
      html += '<input type="range" id="qScale" min="' + (current.min || 0) + '" max="' + (current.max || 10) + '" value="' + (current.min || 0) + '" style="width:100%" />';
      html += '<button class="btn primary" style="margin-top:12px;" onclick="qAnswer(Number(document.getElementById(\'qScale\').value))">Continuar</button>';
      html += "</div>";
    } else {
      html += '<div style="margin-top:16px;">';
      html += '<textarea id="qText" rows="4" placeholder="Descreva brevemente, sem dados pessoais"></textarea>';
      html += '<button class="btn primary" style="margin-top:12px;" onclick="qAnswer(document.getElementById(\'qText\').value)">Continuar</button>';
      html += "</div>";
    }

    html += '<div class="row" style="justify-content:space-between;margin-top:16px;border-top:1px solid var(--slate-100);padding-top:12px;">';
    html += qState.index > 0 ? '<button class="btn secondary" onclick="qBack()">← Voltar</button>' : "<span></span>";
    html += '<span class="muted">SaúdeFlow · demonstração</span></div>';
    html += "</div>";
    document.getElementById("app").innerHTML = html;
    window.scrollTo(0, 0);
  }

  window.qAnswer = function (value) {
    if (!qState) return;
    var current = currentQuestions()[qState.index];
    qState.answers[current.id] = value;
    qState.index += 1;
    if (qState.index >= currentQuestions().length) {
      qState.result = evaluate(qState.answers, qState.answers.description);
      renderResult(qState.result);
    } else {
      renderQuestion();
    }
  };
  window.qBack = function () {
    if (!qState || qState.index === 0) return;
    qState.index -= 1;
    renderQuestion();
  };

  /* ===================== Resultado ===================== */
  function renderResult(result) {
    addAudit("questionario.concluido", "Categoria " + result.category);
    if (result.stopFlow) {
      var h = '<div class="emergency-hero" style="max-width:760px;margin:0 auto;">';
      h += "<h1>Procure socorro imediato</h1>";
      h += "<p>" + esc(result.emergencyMessage) + "</p>";
      h += '<a class="tel" href="tel:192">📞 Ligar SAMU 192</a>';
      h += '<p style="margin-top:14px;font-size:14px;opacity:.9;">Não criamos fila virtual para este relato. A regulação médica define o destino.</p>';
      h += '<a href="#/" style="color:#fff;font-size:14px;">Voltar ao início</a>';
      h += "</div>";
      document.getElementById("app").innerHTML = h;
      return;
    }

    var units = state.units.filter(function (u) { return result.unitTypes.indexOf(u.type) >= 0; });
    var html = '<div style="max-width:900px;margin:0 auto;">';
    var tone = result.category === "A" ? "var(--mint-600)" : result.category === "B" ? "var(--brand-600)" : "var(--violet, #7c3aed)";
    html += '<div class="card" style="background:linear-gradient(135deg,' + tone + ',var(--slate-900));color:#fff;">';
    html += '<span class="pill" style="background:rgba(255,255,255,.18);color:#fff;">Categoria ' + result.category + "</span>";
    html += "<h1 style='margin:10px 0 4px;font-size:30px;color:#fff;'>" + esc(result.categoryLabel) + "</h1>";
    html += "<p style='color:rgba(255,255,255,.85);margin:0;'>" + esc(result.serviceLabel) + "</p></div>";

    html += '<div class="card"><h3>O que consideramos</h3><p>' + esc(result.justification) + "</p>";
    html += '<div class="row" style="margin-top:10px;">';
    result.alertFlags.forEach(function (f) { html += '<span class="pill amber">' + esc(f) + "</span>"; });
    html += "</div>";
    html += '<p class="muted" style="margin-top:12px;">Confiança operacional: ' + Math.round(result.confidence * 100) + "% · Avaliação profissional: " + (result.needsProfessional ? "necessária" : "não obrigatória") + " · Regra: " + esc(result.ruleName) + "</p>";
    html += "</div>";

    html += '<div class="alert warning">Esta orientação é auxiliar e conservadora. A prioridade do atendimento é definida por profissionais de saúde. O protocolo digital não garante horário nem prioridade clínica.</div>';

    if (units.length) {
      html += '<h2 class="section-title">Unidades compatíveis</h2><div class="grid cols-2">';
      units.forEach(function (unit) {
        html += '<div class="card"><div class="row" style="justify-content:space-between;"><h3>' + esc(unit.name) + "</h3>" + (unit.simulated ? '<span class="pill slate">Simulada</span>' : "") + "</div>";
        html += '<p class="muted">' + esc(unit.neighborhood || "") + ", " + esc(unit.city || "") + " · " + esc(unit.street || "") + "</p>";
        html += "<p>" + estimateLabel(unit) + "</p>";
        if (unit.type !== "ubs") {
          html += '<button class="btn primary" onclick="createRequest(\'' + unit.id + "')\">Gerar protocolo</button>";
        } else {
          html += '<span class="pill mint">Procure a UBS</span>';
        }
        html += "</div>";
      });
      html += "</div>";
    }
    html += '<div class="spacer"></div><a class="btn secondary" href="#/">Voltar ao início</a>';
    html += "</div>";
    document.getElementById("app").innerHTML = html;
  }

  function estimateLabel(unit) {
    var e = unit.estimate || {};
    if (!e.reliable) return "⚠ " + (e.message || "Sem dados suficientes para estimar.");
    if (e.low === 0 && e.high === 0) return "Nenhuma pessoa aguardando no momento.";
    return "⏱ Estimativa: " + Math.round(e.low) + "–" + Math.round(e.high) + " min";
  }

  window.createRequest = function (unitId) {
    state.seq += 1;
    var protocol = "SF-2026-" + String(state.seq).padStart(6, "0");
    var request = {
      id: uid(),
      protocol: protocol,
      patient: "Você (usuário teste)",
      unitId: unitId,
      category: qState && qState.result ? qState.result.category : "B",
      status: "sent",
      position: state.requests.filter(function (r) { return r.unitId === unitId && ["sent", "awaiting_confirmation", "pre_register_confirmed"].indexOf(r.status) >= 0; }).length + 1,
      createdAt: new Date().toISOString(),
      timeline: [{ label: "Solicitação criada", at: new Date().toISOString() }],
    };
    state.requests.unshift(request);
    addAudit("request.create", protocol);
    save();
    location.hash = "#/protocolo/" + encodeURIComponent(protocol);
  };

  /* ===================== Acompanhamento ===================== */
  var simulateTimer = null;
  function viewTracking(protocol) {
    var request = state.requests.filter(function (r) { return r.protocol === protocol; })[0];
    if (!request) {
      return '<div class="empty">Protocolo não encontrado. Confira o número.</div>';
    }
    var unit = unitById(request.unitId);
    var html = '<div style="max-width:760px;margin:0 auto;">';
    html += '<div class="card"><div class="row" style="justify-content:space-between;"><div><p class="muted">PROTOCOLO</p><p style="font-size:28px;font-weight:800;color:var(--brand-700);">' + esc(request.protocol) + "</p></div>";
    html += '<span class="pill blue">' + esc(STATUS[request.status]) + "</span></div>";
    html += '<div class="grid cols-2" style="margin-top:14px;">';
    html += "<div><p class='muted'>Unidade</p><p>" + esc(unit ? unit.name : "—") + "</p></div>";
    html += "<div><p class='muted'>Estimativa</p><p>" + (unit ? estimateLabel(unit) : "—") + "</p></div>";
    html += "<div><p class='muted'>Criada em</p><p>" + nowLabel(new Date(request.createdAt)) + "</p></div>";
    html += "<div><p class='muted'>Status</p><p>" + esc(STATUS[request.status]) + "</p></div>";
    html += "</div>";
    html += '<p class="muted" style="margin-top:14px;">⏳ Emulação: o status avança automaticamente alguns segundos (dados simulados).</p>';
    html += '<h3 style="margin:18px 0 0;">Linha do tempo</h3><ul class="timeline">';
    request.timeline.forEach(function (item) {
      html += "<li><strong>" + esc(item.label) + "</strong><br><span class='muted'>" + nowLabel(new Date(item.at)) + "</span></li>";
    });
    html += "</ul></div>";
    html += '<div class="spacer"></div><a class="btn secondary" href="#/">Voltar ao início</a></div>';
    return html;
  }

  /* ===================== Pré-alerta ===================== */
  function viewPreAlert() {
    var options = state.units.filter(function (u) { return u.type === "hospital" || u.type === "emergency"; });
    var html = '<div style="max-width:760px;margin:0 auto;">';
    html += '<div class="emergency-hero"><h1>Pré-alerta de paciente a caminho</h1><p>Envie informações preliminares para a unidade. Não substitui o SAMU 192.</p>';
    html += '<a class="tel" href="tel:192">📞 SAMU 192</a></div>';
    html += '<div class="card" style="margin-top:18px;"><label>Unidade de destino</label><select id="paUnit"><option value="">Selecione...</option>';
    options.forEach(function (u) { html += '<option value="' + u.id + '">' + esc(u.name) + "</option>"; });
    html += "</select>";
    html += "<label>O que aconteceu?</label><textarea id='paDescription' rows='3' placeholder='Descreva brevemente, sem dados pessoais'></textarea>";
    html += '<div class="grid cols-3"><div><label>Consciente?</label><select id="paConscious"><option value="unknown">Não sei</option><option value="yes">Sim</option><option value="no">Não</option></select></div>';
    html += '<div><label>Respirando?</label><select id="paBreathing"><option value="unknown">Não sei</option><option value="yes">Sim</option><option value="no">Não</option></select></div>';
    html += '<div><label>Sangramento?</label><select id="paBleeding"><option value="unknown">Não sei</option><option value="yes">Sim</option><option value="no">Não</option></select></div></div>';
    html += "<label>Previsão de chegada (min)</label><input id='paEta' type='number' min='0' />";
    html += '<button class="btn primary block" style="margin-top:16px;" onclick="sendPreAlert()">Enviar pré-alerta</button></div>';
    html += '<div id="paResult"></div></div>';
    return html;
  }

  window.sendPreAlert = function () {
    var unitId = document.getElementById("paUnit").value;
    if (!unitId) {
      document.getElementById("paResult").innerHTML = '<div class="alert danger">Selecione a unidade de destino.</div>';
      return;
    }
    var flags = [];
    if (document.getElementById("paConscious").value === "no") flags.push("loss_of_consciousness");
    if (document.getElementById("paBreathing").value === "no") flags.push("respiratory_emergency");
    if (document.getElementById("paBleeding").value === "yes") flags.push("severe_bleeding");
    var eta = Number(document.getElementById("paEta").value);
    if (!isNaN(eta) && eta > 0) flags.push("patient_on_the_way");
    var alert = {
      id: uid(),
      code: "ALERT-" + Math.random().toString(16).slice(2, 10).toUpperCase(),
      unitId: unitId,
      description: document.getElementById("paDescription").value,
      conscious: document.getElementById("paConscious").value,
      breathing: document.getElementById("paBreathing").value,
      bleeding: document.getElementById("paBleeding").value,
      eta: isNaN(eta) ? null : eta,
      flags: flags,
      status: "new",
      createdAt: new Date().toISOString(),
    };
    state.alerts.unshift(alert);
    addAudit("alert.create", alert.code);
    save();
    document.getElementById("paResult").innerHTML =
      '<div class="alert success" style="margin-top:16px;"><div><strong>Pré-alerta enviado: ' + esc(alert.code) + "</strong><br>Status: Novo alerta. A unidade pode confirmar o recebimento. Continue seguindo as orientações de emergência.</div></div>";
    document.getElementById("paUnit").value = "";
    document.getElementById("paDescription").value = "";
    document.getElementById("paEta").value = "";
  };

  /* ===================== UPA ===================== */
  function upaQueue(unitId) {
    return state.requests.filter(function (r) { return r.unitId === unitId && ["sent", "awaiting_confirmation", "pre_register_confirmed", "patient_arrived", "awaiting_welcome", "awaiting_care", "in_care"].indexOf(r.status) >= 0; });
  }

  function viewUpaDashboard() {
    var unit = state.units.filter(function (u) { return u.type === "upa"; })[0] || state.units[0];
    var queue = upaQueue(unit.id);
    var html = "<h1 style='color:var(--slate-900);'>" + esc(unit.name) + "</h1><p class='muted'>Visão operacional da unidade (dados simulados)</p>";
    html += '<div class="grid cols-4" style="margin-top:16px;">';
    html += '<div class="stat"><div class="label">Aguardando</div><div class="value">' + queue.length + "</div></div>";
    html += '<div class="stat mint"><div class="label">Profissionais</div><div class="value">' + unit.capacity.professionals + "</div></div>";
    html += '<div class="stat violet"><div class="label">Em atendimento</div><div class="value">' + state.requests.filter(function (r) { return r.unitId === unit.id && r.status === "in_care"; }).length + "</div></div>";
    html += '<div class="stat amber"><div class="label">Pré-alertas</div><div class="value">' + state.alerts.filter(function (a) { return a.unitId === unit.id; }).length + "</div></div>";
    html += "</div>";
    html += '<div class="grid cols-2" style="margin-top:18px;">';
    html += '<a class="card" href="#/upa/fila"><h3>⚑ Fila digital</h3><p>Chamar protocolos e acompanhar posições.</p></a>';
    html += '<a class="card" href="#/upa/solicitacoes"><h3>📋 Solicitações</h3><p>Confirmar recebimento, registrar chegada e atualizar status.</p></a>';
    html += "</div>";
    html += '<p class="muted" style="margin-top:16px;">A fila digital é administrativa e não define prioridade clínica.</p>';
    return html;
  }

  function viewUpaQueue() {
    var unit = state.units.filter(function (u) { return u.type === "upa"; })[0] || state.units[0];
    var queue = upaQueue(unit.id);
    var html = "<h1 style='color:var(--slate-900);'>Fila digital</h1><p class='muted'>" + esc(unit.name) + " · ordem administrativa, não clínica</p>";
    if (!queue.length) return html + '<div class="empty" style="margin-top:16px;">Nenhuma solicitação ativa.</div>';
    html += '<div class="card" style="margin-top:16px;"><table><thead><tr><th>Posição</th><th>Protocolo</th><th>Paciente</th><th>Status</th><th></th></tr></thead><tbody>';
    queue.forEach(function (r, i) {
      html += "<tr><td>" + (i + 1) + "</td><td><strong>" + esc(r.protocol) + "</strong></td><td>" + esc(r.patient) + "</td><td>" + esc(STATUS[r.status]) + "</td>";
      html += '<td><button class="btn secondary" style="padding:6px 10px;font-size:12px;" onclick="upaAdvance(\'' + r.id + "')\">Avançar</button></td></tr>";
    });
    html += "</tbody></table></div>";
    return html;
  }

  window.upaAdvance = function (id) {
    var r = state.requests.filter(function (x) { return x.id === id; })[0];
    if (!r) return;
    advanceStatus(r);
    addAudit("request.status", r.protocol + " → " + r.status);
    route();
  };

  function viewUpaRequests() {
    var html = "<h1 style='color:var(--slate-900);'>Solicitações</h1><p class='muted'>Pré-cadastros digitais recebidos</p>";
    html += '<div class="card" style="margin-top:16px;"><table><thead><tr><th>Protocolo</th><th>Paciente</th><th>Categoria</th><th>Status</th><th></th></tr></thead><tbody>';
    state.requests.forEach(function (r) {
      html += "<tr><td><strong>" + esc(r.protocol) + "</strong></td><td>" + esc(r.patient) + "</td><td>" + r.category + "</td><td>" + esc(STATUS[r.status]) + "</td>";
      html += '<td><button class="btn secondary" style="padding:6px 10px;font-size:12px;" onclick="upaAdvance(\'' + r.id + "')\">Avançar</button> ";
      html += '<a href="#/protocolo/' + encodeURIComponent(r.protocol) + '">Ver</a></td></tr>';
    });
    html += "</tbody></table></div>";
    html += '<p class="muted" style="margin-top:12px;">As informações vieram de formulário digital e não foram verificadas clinicamente.</p>';
    return html;
  }

  /* ===================== Hospital ===================== */
  function viewHospital() {
    var unit = state.units.filter(function (u) { return u.type === "hospital"; })[0] || state.units[0];
    var alerts = state.alerts.filter(function (a) { return a.unitId === unit.id; });
    var onTheWay = alerts.filter(function (a) { return ["new", "received", "confirmed"].indexOf(a.status) >= 0; }).length;
    var html = "<h1 style='color:var(--slate-900);'>" + esc(unit.name) + "</h1><p class='muted'>Recebimento de pré-alertas e indicadores</p>";
    html += '<div class="grid cols-4" style="margin-top:16px;">';
    html += '<div class="stat"><div class="label">Pré-alertas recebidos</div><div class="value">' + alerts.length + "</div></div>";
    html += '<div class="stat amber"><div class="label">Pacientes a caminho</div><div class="value">' + onTheWay + "</div></div>";
    html += '<div class="stat mint"><div class="label">Confirmados</div><div class="value">' + alerts.filter(function (a) { return a.status === "confirmed"; }).length + "</div></div>";
    html += '<div class="stat red"><div class="label">Novos</div><div class="value">' + alerts.filter(function (a) { return a.status === "new"; }).length + "</div></div>";
    html += "</div>";
    html += '<h2 class="section-title">Pré-alertas</h2>';
    if (!alerts.length) return html + '<div class="empty">Nenhum pré-alerta.</div>';
    html += '<div class="grid" style="gap:12px;">';
    alerts.forEach(function (a) {
      html += '<div class="card"><div class="row" style="justify-content:space-between;"><strong>' + esc(a.code) + "</strong>" + alertPill(a.status) + "</div>";
      html += '<p style="margin-top:8px;">' + esc(a.description || "—") + "</p>";
      html += '<p class="muted">Consciente: ' + esc(a.conscious) + " · Respirando: " + esc(a.breathing) + " · Sangramento: " + esc(a.bleeding) + (a.eta ? " · Previsão: " + a.eta + " min" : "") + "</p>";
      html += '<div class="row" style="margin-top:10px;">';
      if (a.status === "new") html += '<button class="btn secondary" style="padding:6px 10px;font-size:12px;" onclick="alertSet(\'' + a.id + "\', 'received')\">Marcar recebido</button>";
      if (["new", "received"].indexOf(a.status) >= 0) html += '<button class="btn primary" style="padding:6px 10px;font-size:12px;" onclick="alertSet(\'' + a.id + "\', 'confirmed')\">Confirmar</button>";
      if (a.status === "confirmed") html += '<button class="btn success" style="padding:6px 10px;font-size:12px;" onclick="alertSet(\'' + a.id + "\', 'arrived')\">Registrar chegada</button>";
      if (["confirmed", "arrived"].indexOf(a.status) >= 0) html += '<button class="btn secondary" style="padding:6px 10px;font-size:12px;" onclick="alertSet(\'' + a.id + "\', 'closed')\">Encerrar</button>";
      html += "</div></div>";
    });
    html += "</div>";
    html += '<p class="muted" style="margin-top:12px;">Confirmar recebimento não significa aceitação clínica, reserva de leito ou garantia de atendimento.</p>';
    return html;
  }

  function alertPill(status) {
    var map = { new: ["red", "Novo"], received: ["amber", "Recebido"], confirmed: ["blue", "Confirmado"], arrived: ["mint", "Chegada registrada"], closed: ["slate", "Encerrado"], cancelled: ["red", "Cancelado"] };
    var item = map[status] || ["slate", status];
    return '<span class="pill ' + item[0] + '">' + item[1] + "</span>";
  }

  window.alertSet = function (id, status) {
    var a = state.alerts.filter(function (x) { return x.id === id; })[0];
    if (!a) return;
    a.status = status;
    addAudit("alert.status", a.code + " → " + status);
    save();
    route();
  };

  /* ===================== Admin ===================== */
  function viewAdmin() {
    var html = "<h1 style='color:var(--slate-900);'>Administração</h1><p class='muted'>Indicadores gerais e integrações (demonstração offline)</p>";
    html += '<div class="grid cols-4" style="margin-top:16px;">';
    html += '<div class="stat"><div class="label">Unidades</div><div class="value">' + state.units.length + "</div></div>";
    html += '<div class="stat violet"><div class="label">Solicitações</div><div class="value">' + state.requests.length + "</div></div>";
    html += '<div class="stat amber"><div class="label">Ativas</div><div class="value">' + state.requests.filter(function (r) { return ["finished", "cancelled"].indexOf(r.status) < 0; }).length + "</div></div>";
    html += '<div class="stat red"><div class="label">Pré-alertas</div><div class="value">' + state.alerts.length + "</div></div>";
    html += "</div>";
    html += '<h2 class="section-title">Integrações externas (status)</h2><div class="card"><table><thead><tr><th>Fonte</th><th>Status</th><th>Uso</th></tr></thead><tbody>';
    html += "<tr><td>CNES — Estabelecimentos (MS/DATASUS)</td><td><span class='pill mint'>Funcionando no projeto completo</span></td><td>Cadastro de estabelecimentos</td></tr>";
    html += "<tr><td>DATASUS — Hospitais e Leitos</td><td><span class='pill mint'>Funcionando no projeto completo</span></td><td>Leitos e endereço (sem ocupação em tempo real)</td></tr>";
    html += "<tr><td>IBGE — Localidades</td><td><span class='pill mint'>Funcionando no projeto completo</span></td><td>Municípios e códigos</td></tr>";
    html += "<tr><td>ViaCEP</td><td><span class='pill mint'>Funcionando no projeto completo</span></td><td>Endereço por CEP</td></tr>";
    html += "<tr><td>OSRM + OpenStreetMap</td><td><span class='pill mint'>Funcionando no projeto completo</span></td><td>Mapa e rotas</td></tr>";
    html += "<tr><td>RNDS / SAMU / prontuários</td><td><span class='pill red'>Não implementado</span></td><td>Exige autorização institucional</td></tr>";
    html += "</tbody></table></div>";
    html += '<h2 class="section-title">Auditoria recente</h2><div class="card"><table><thead><tr><th>Ação</th><th>Quando</th></tr></thead><tbody>';
    state.audit.slice(0, 8).forEach(function (a) {
      html += "<tr><td>" + esc(a.action) + "</td><td class='muted'>" + nowLabel(new Date(a.at)) + "</td></tr>";
    });
    html += "</tbody></table></div>";
    return html;
  }

  /* ===================== Páginas públicas ===================== */
  function viewHome() {
    var html = '<div class="hero"><span class="badge">Demonstração offline — Global Solution FIAP</span>';
    html += "<h1>Orientação inteligente para o atendimento de saúde</h1>";
    html += "<p>Questionário inteligente, orientação de acesso, unidades compatíveis, pré-cadastro e acompanhamento em tempo real — nesta versão de demonstração, tudo roda no navegador, sem cadastro.</p>";
    html += '<div class="hero-actions"><a href="#/atendimento">❤ Preciso de atendimento</a><a class="secondary" href="#/unidades">Ver unidades</a><a class="danger" href="#/emergencia">Emergência</a></div></div>';
    html += '<h2 class="section-title">Acesso rápido</h2><div class="grid cols-4">';
    html += '<div class="card"><h3>Paciente</h3><p>Questionário, protocolo e acompanhamento.</p><a class="btn primary block" href="#/atendimento">Abrir</a></div>';
    html += '<div class="card"><h3>UPA</h3><p>Dashboard, fila digital e solicitações.</p><a class="btn secondary block" href="#/upa">Abrir</a></div>';
    html += '<div class="card"><h3>Visão Hospital</h3><p>Recebimento de pré-alertas.</p><a class="btn secondary block" href="#/hospital">Abrir</a></div>';
    html += '<div class="card"><h3>Admin</h3><p>Indicadores e integrações.</p><a class="btn secondary block" href="#/admin">Abrir</a></div>';
    html += "</div>";
    html += '<h2 class="section-title">Como funciona</h2><div class="grid cols-2">';
    html += '<div class="card"><h3>1. Questionário dinâmico</h3><p>As perguntas mudam conforme as respostas. Sinais de emergência interrompem o fluxo e mostram o SAMU 192.</p></div>';
    html += '<div class="card"><h3>2. Orientação conservadora</h3><p>Categorias A (UBS), B (UPA), C (hospital) ou D (emergência), sempre com linguagem simples.</p></div>';
    html += '<div class="card"><h3>3. Protocolo e fila digital</h3><p>Protocolo único, acompanhamento em tempo real e estimativas operacionais (nunca garantia).</p></div>';
    html += '<div class="card"><h3>4. Pré-alerta</h3><p>Avise a unidade que está a caminho, sem substituir o SAMU ou a regulação médica.</p></div>';
    html += "</div>";
    html += '<div class="alert warning" style="margin-top:22px;">Aviso: demonstração acadêmica com dados simulados. Não substitui atendimento médico, SAMU 192, regulação ou sistemas oficiais.</div>';
    return html;
  }

  function viewUnits() {
    var html = "<h1 style='color:var(--slate-900);'>Unidades de saúde</h1><p class='muted'>Unidades de demonstração (fictícias). Distância em linha reta quando disponível.</p>";
    html += '<div class="grid cols-2" style="margin-top:16px;">';
    state.units.forEach(function (u) {
      var typeLabel = { ubs: "UBS", upa: "UPA", hospital: "Hospital", emergency: "Pronto-socorro" }[u.type] || u.type;
      html += '<div class="card"><div class="row" style="justify-content:space-between;"><h3>' + esc(u.name) + "</h3>" + (u.simulated ? '<span class="pill slate">Simulada</span>' : "") + "</div>";
      html += '<p class="muted">' + typeLabel + " · " + esc(u.neighborhood || "") + ", " + esc(u.city || "") + "</p>";
      html += "<p>" + esc(u.street || "") + "</p>";
      html += "<p>" + estimateLabel(u) + "</p>";
      html += '<div class="row" style="margin-top:6px;">';
      u.services.slice(0, 3).forEach(function (s) { html += '<span class="pill slate">' + esc(s) + "</span>"; });
      html += "</div>";
      if (u.type !== "ubs") html += '<button class="btn primary" style="margin-top:10px;" onclick="location.hash=\'#/atendimento\'">Solicitar atendimento</button>';
      html += "</div>";
    });
    html += "</div>";
    return html;
  }

  function viewEmergency() {
    var html = '<div class="emergency-hero"><h1>Emergência</h1><p>Se é uma emergência grave, ligue agora para o SAMU 192.</p>';
    html += '<a class="tel" href="tel:192">📞 192</a>';
    html += '<p style="margin-top:12px;font-size:13px;opacity:.9;">A ligação é necessária para solicitar atendimento. O sistema não aciona ambulância nem simula o serviço oficial.</p></div>';
    html += '<div class="grid cols-2" style="margin-top:18px;">';
    html += '<div class="card"><h3>Preciso de socorro imediato</h3><p>1. Ligue para o SAMU 192.<br>2. Informe local, o que aconteceu e o estado da pessoa.<br>3. Siga as orientações do atendente.</p><a class="btn danger block" href="tel:192">📞 Ligar SAMU 192</a></div>';
    html += '<div class="card"><h3>Já estou a caminho de uma unidade</h3><p>Envie um pré-alerta digital com informações preliminares. Não substitui o SAMU nem garante atendimento.</p><a class="btn primary block" href="#/pre-alerta">Enviar pré-alerta</a></div>';
    html += "</div>";
    html += '<div class="alert warning" style="margin-top:18px;">O sistema não aciona ambulância, não define destino hospitalar e não oferece fila virtual como alternativa ao socorro.</div>';
    return html;
  }

  function viewLogin() {
    var html = '<div style="max-width:420px;margin:0 auto;">';
    html += '<div class="card"><h1 style="color:var(--slate-900);margin-top:0;">Entrar</h1><p class="muted">Nesta demo não é preciso conta: use o usuário teste.</p>';
    html += '<button class="btn success block" onclick="demoEnter(\'paciente\', \'#/paciente/pre-alerta\')">Entrar como usuário teste (sem cadastro)</button>';
    html += '<div class="spacer"></div><p class="muted" style="text-align:center;">ou acesse pelos botões do topo: Paciente · UPA · Visão Hospital · Admin</p></div>';
    html += "</div>";
    return html;
  }

  window.demoEnter = function (role, redirect) {
    if (redirect) {
      location.hash = redirect;
      return;
    }
    var homes = { paciente: "#/", upa: "#/upa", hospital: "#/hospital", admin: "#/admin" };
    location.hash = homes[role] || "#/";
  };

  /* ===================== Layout / router ===================== */
  function layout(content) {
    return (
      '<div class="topstrip"><span>Acesso rápido:</span>' +
      '<button onclick="demoEnter(\'paciente\')">Paciente</button>' +
      '<button onclick="demoEnter(\'upa\')">UPA</button>' +
      '<button onclick="demoEnter(\'hospital\')">Visão Hospital</button>' +
      '<button onclick="demoEnter(\'admin\')">Admin</button>' +
      "</div>" +
      '<header><div class="header-inner">' +
      '<a class="brand" href="#/"><span class="brand-icon">❤</span> SaúdeFlow</a>' +
      '<nav class="nav">' +
      '<a href="#/unidades">Unidades</a>' +
      '<button class="hospital" onclick="demoEnter(\'hospital\')">Visão Hospital</button>' +
      '<a class="emergency" href="#/emergencia">Emergência</a>' +
      '<a href="#/login">Entrar</a>' +
      "</nav></div></header>" +
      "<main>" +
      content +
      "</main>" +
      "<footer>SaúdeFlow — demonstração offline com dados fictícios. Não substitui atendimento médico, SAMU 192, regulação ou sistemas oficiais. Em emergência, ligue 192.</footer>"
    );
  }

  function route() {
    if (simulateTimer) {
      clearInterval(simulateTimer);
      simulateTimer = null;
    }
    var hash = location.hash || "#/";
    var app = document.getElementById("app");
    var html = "";

    if (hash === "#/" || hash === "") html = viewHome();
    else if (hash === "#/unidades") html = viewUnits();
    else if (hash === "#/emergencia") html = viewEmergency();
    else if (hash === "#/login") html = viewLogin();
    else if (hash === "#/atendimento") {
      startQuestionnaire();
      return; // startQuestionnaire já renderiza
    } else if (hash === "#/pre-alerta") html = viewPreAlert();
    else if (hash.indexOf("#/protocolo/") === 0) {
      html = viewTracking(decodeURIComponent(hash.replace("#/protocolo/", "")));
      simulateTimer = setInterval(function () {
        var request = state.requests.filter(function (r) {
          return r.protocol === decodeURIComponent((location.hash || "").replace("#/protocolo/", ""));
        })[0];
        if (request && ["finished", "cancelled"].indexOf(request.status) < 0) {
          advanceStatus(request);
          route();
        }
      }, 8000);
    } else if (hash === "#/upa") html = viewUpaDashboard();
    else if (hash === "#/upa/fila") html = viewUpaQueue();
    else if (hash === "#/upa/solicitacoes") html = viewUpaRequests();
    else if (hash === "#/hospital") html = viewHospital();
    else if (hash === "#/admin") html = viewAdmin();
    else html = viewHome();

    app.innerHTML = layout(html);
    window.scrollTo(0, 0);
  }

  window.addEventListener("hashchange", route);
  route();
})();
