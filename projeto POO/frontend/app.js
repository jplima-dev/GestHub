const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const dateFmt = new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC" });

const state = {
  token: localStorage.getItem("condoflow.token"),
  user: JSON.parse(localStorage.getItem("condoflow.user") || "null"),
  csrf: null,
  view: "dashboard",
  module: "moradores",
  records: [],
  editing: null,
  search: "",
  status: "",
};

const statusOptions = ["", "ativo", "pendente", "pago", "vencido", "cancelado", "aberta", "em_andamento", "resolvida", "publicado", "rascunho", "arquivado", "disponivel", "alugado", "encerrado"];

const modules = {
  proprietarios: {
  title: "Proprietários",
  subtitle: "Cadastro e gerenciamento de proprietários.",
  endpoint: "/api/proprietarios",
  report: "proprietarios",
  rolesCreate: ["proprietario"],

  columns: [
    ["id", "#"],
    ["nome", "Nome"],
    ["cpf_cnpj", "CPF/CNPJ"],
    ["telefone", "Telefone"],
    ["endereco", "Endereço"],
  ],

  fields: [
    ["nome", "Nome", "text", true],
    ["cpf_cnpj", "CPF/CNPJ", "text", true],
    ["telefone", "Telefone", "text"],
    ["endereco", "Endereço", "text"],
    ["observacoes", "Observações", "textarea"],
  ],
},
  moradores: {
    title: "Moradores",
    subtitle: "Cadastro, perfil completo, busca, filtros e histórico.",
    endpoint: "/api/moradores",
    report: "moradores",
    rolesCreate: ["proprietario"],
    columns: [
      ["id", "#"],
      ["nome", "Nome"],
      ["email", "E-mail"],
      ["cpf", "CPF"],
      ["telefone", "Telefone"],
      ["status", "Status", "status"],
    ],
    fields: [
      ["unidade_id", "Unidade", "number"],
      ["nome", "Nome", "text", true],
      ["email", "E-mail", "email", true],
      ["cpf", "CPF", "text", true],
      ["telefone", "Telefone", "text"],
      ["data_nascimento", "Nascimento", "date"],
      ["ocupacao", "Ocupação", "text"],
      ["status", "Status", "select", false, ["ativo", "inativo"]],
      ["observacoes", "Observações", "textarea"],
    ],
  },
  avisos: {
    title: "Avisos",
    subtitle: "Publicação, arquivamento, anexos e leitura.",
    endpoint: "/api/avisos",
    rolesCreate: ["proprietario"],
    columns: [
      ["id", "#"],
      ["titulo", "Título"],
      ["categoria", "Categoria"],
      ["prioridade", "Prioridade"],
      ["status", "Status", "status"],
      ["publicado_em", "Publicado", "datetime"],
    ],
    fields: [
      ["titulo", "Título", "text", true],
      ["mensagem", "Mensagem", "textarea", true],
      ["categoria", "Categoria", "select", false, ["geral", "manutencao", "financeiro", "assembleia", "seguranca"]],
      ["status", "Status", "select", false, ["rascunho", "publicado", "arquivado"]],
      ["prioridade", "Prioridade", "select", false, ["baixa", "normal", "alta"]],
      ["anexo_path", "Anexo", "text"],
    ],
    rowActions: ["publicar", "arquivar", "lido"],
  },
  boletos: {
    title: "Boletos",
    subtitle: "Geração, baixa, PDF, comprovantes e status.",
    endpoint: "/api/boletos",
    report: "boletos",
    rolesCreate: ["proprietario"],
    columns: [
      ["id", "#"],
      ["numero", "Número"],
      ["valor", "Valor", "money"],
      ["vencimento", "Vencimento", "date"],
      ["status", "Status", "status"],
      ["pago_em", "Pago em", "date"],
    ],
    fields: [
      ["contrato_id", "Contrato", "number"],
      ["morador_id", "Morador", "number", true],
      ["imovel_id", "Imóvel", "number", true],
      ["numero", "Número", "text", true],
      ["valor", "Valor", "number", true],
      ["vencimento", "Vencimento", "date", true],
      ["status", "Status", "select", false, ["pendente", "pago", "vencido", "cancelado"]],
      ["linha_digitavel", "Linha digitável", "text"],
    ],
    rowActions: ["pdf", "pagar", "cancelar"],
  },
  alugueis: {
    title: "Aluguel",
    subtitle: "Histórico mensal, pagamentos e reajustes operacionais.",
    endpoint: "/api/alugueis",
    rolesCreate: ["proprietario"],
    columns: [
      ["id", "#"],
      ["contrato_id", "Contrato"],
      ["competencia", "Competência"],
      ["valor", "Valor", "money"],
      ["vencimento", "Vencimento", "date"],
      ["status", "Status", "status"],
    ],
    fields: [
      ["contrato_id", "Contrato", "number", true],
      ["competencia", "Competência", "text", true],
      ["valor", "Valor", "number", true],
      ["vencimento", "Vencimento", "date", true],
      ["status", "Status", "select", false, ["pendente", "pago", "vencido", "cancelado"]],
      ["observacoes", "Observações", "textarea"],
    ],
  },
  contratos: {
    title: "Contratos",
    subtitle: "Vigência, renovação, encerramento, reajustes e documentos.",
    endpoint: "/api/contratos",
    report: "contratos",
    rolesCreate: ["proprietario"],
    columns: [
      ["id", "#"],
      ["imovel_id", "Imóvel"],
      ["morador_id", "Morador"],
      ["inicio", "Início", "date"],
      ["fim", "Fim", "date"],
      ["valor_aluguel", "Aluguel", "money"],
      ["status", "Status", "status"],
    ],
    fields: [
      ["imovel_id", "Imóvel", "number", true],
      ["morador_id", "Morador", "number", true],
      ["proprietario_id", "Proprietário", "number", true],
      ["inicio", "Início", "date", true],
      ["fim", "Fim", "date", true],
      ["valor_aluguel", "Aluguel", "number", true],
      ["status", "Status", "select", false, ["ativo", "encerrado", "renovacao"]],
      ["reajuste_indice", "Índice", "text"],
      ["deposito_garantia", "Garantia", "number"],
      ["documento_url", "Documento", "text"],
    ],
    rowActions: ["encerrar"],
  },
  imoveis: {
    title: "Imóveis",
    subtitle: "Casas, apartamentos, terrenos, salas, lojas e galpões.",
    endpoint: "/api/imoveis",
    rolesCreate: ["proprietario"],
    columns: [
      ["id", "#"],
      ["titulo", "Imóvel"],
      ["tipo", "Tipo"],
      ["cidade", "Cidade"],
      ["valor", "Valor", "money"],
      ["status", "Status", "status"],
    ],
    fields: [
      ["proprietario_id", "Proprietário", "number", true],
      ["unidade_id", "Unidade", "number"],
      ["tipo", "Tipo", "select", true, ["casa", "apartamento", "terreno", "sala_comercial", "loja", "galpao"]],
      ["titulo", "Título", "text", true],
      ["endereco", "Endereço", "text", true],
      ["cidade", "Cidade", "text", true],
      ["estado", "UF", "text", true],
      ["valor", "Valor", "number", true],
      ["area_m2", "Área m²", "number"],
      ["status", "Status", "select", false, ["disponivel", "alugado", "manutencao"]],
      ["descricao", "Descrição", "textarea"],
    ],
  },
  condominios: {
    title: "Condomínios",
    subtitle: "Condomínios, blocos, torres e unidades.",
    endpoint: "/api/condominios",
    rolesCreate: ["proprietario"],
    columns: [
      ["id", "#"],
      ["nome", "Nome"],
      ["cidade", "Cidade"],
      ["estado", "UF"],
      ["sindico", "Síndico"],
      ["ativo", "Ativo", "bool"],
    ],
    fields: [
      ["nome", "Nome", "text", true],
      ["cnpj", "CNPJ", "text"],
      ["endereco", "Endereço", "text", true],
      ["cidade", "Cidade", "text", true],
      ["estado", "UF", "text", true],
      ["cep", "CEP", "text"],
      ["sindico", "Síndico", "text"],
      ["telefone", "Telefone", "text"],
      ["ativo", "Ativo", "checkbox"],
    ],
  },
  financeiro: {
    title: "Financeiro",
    subtitle: "Receitas, despesas, fluxo de caixa, balancetes e relatórios.",
    endpoint: "/api/financeiro/lancamentos",
    report: "financeiro",
    rolesCreate: ["proprietario"],
    columns: [
      ["id", "#"],
      ["tipo", "Tipo"],
      ["categoria", "Categoria"],
      ["descricao", "Descrição"],
      ["valor", "Valor", "money"],
      ["data", "Data", "date"],
      ["status", "Status", "status"],
    ],
    fields: [
      ["proprietario_id", "Proprietário", "number", true],
      ["contrato_id", "Contrato", "number"],
      ["boleto_id", "Boleto", "number"],
      ["tipo", "Tipo", "select", true, ["receita", "despesa"]],
      ["categoria", "Categoria", "text", true],
      ["descricao", "Descrição", "text", true],
      ["valor", "Valor", "number", true],
      ["data", "Data", "date", true],
      ["status", "Status", "select", false, ["realizado", "previsto", "cancelado"]],
    ],
  },
  ocorrencias: {
    title: "Ocorrências",
    subtitle: "Reclamações, solicitações, sugestões e manutenção.",
    endpoint: "/api/ocorrencias",
    report: "ocorrencias",
    rolesCreate: ["proprietario", "morador"],
    columns: [
      ["id", "#"],
      ["titulo", "Título"],
      ["tipo", "Tipo"],
      ["prioridade", "Prioridade"],
      ["status", "Status", "status"],
      ["criado_em", "Abertura", "datetime"],
    ],
    fields: [
      ["morador_id", "Morador", "number"],
      ["imovel_id", "Imóvel", "number"],
      ["titulo", "Título", "text", true],
      ["descricao", "Descrição", "textarea", true],
      ["tipo", "Tipo", "select", false, ["reclamacao", "solicitacao", "sugestao", "manutencao"]],
      ["status", "Status", "select", false, ["aberta", "em_andamento", "resolvida", "cancelada"]],
      ["prioridade", "Prioridade", "select", false, ["baixa", "media", "alta"]],
    ],
  },
  documentos: {
    title: "Documentos",
    subtitle: "Upload, download e categorização de arquivos.",
    endpoint: "/api/documentos",
    rolesCreate: ["proprietario", "morador"],
    upload: true,
    columns: [
      ["id", "#"],
      ["titulo", "Título"],
      ["categoria", "Categoria"],
      ["mime_type", "Tipo"],
      ["tamanho", "Tamanho", "bytes"],
      ["criado_em", "Criado", "datetime"],
    ],
    fields: [
      ["titulo", "Título", "text", true],
      ["categoria", "Categoria", "select", false, ["contrato", "boleto", "comprovante", "documento_pessoal", "geral"]],
      ["contrato_id", "Contrato", "number"],
      ["imovel_id", "Imóvel", "number"],
      ["arquivo", "Arquivo", "file", true],
    ],
    rowActions: ["download"],
  },
};

const reportTypes = [
  ["moradores", "Moradores"],
  ["boletos", "Boletos"],
  ["financeiro", "Financeiro"],
  ["contratos", "Contratos"],
  ["ocorrencias", "Ocorrências"],
];

function toast(message) {
  const node = $("#toast");
  node.textContent = message;
  node.classList.add("show");
  setTimeout(() => node.classList.remove("show"), 3200);
}

async function ensureCsrf() {
  if (state.csrf) return state.csrf;
  const response = await fetch("/api/auth/csrf");
  const data = await response.json();
  state.csrf = data.csrf_token;
  return state.csrf;
}

async function api(path, options = {}) {
  const method = options.method || "GET";
  const headers = new Headers(options.headers || {});
  if (state.token) headers.set("Authorization", `Bearer ${state.token}`);
  let body = options.body;

  if (!["GET", "HEAD"].includes(method)) {
    headers.set("x-csrf-token", await ensureCsrf());
  }

  if (body && !(body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(body);
  }

  const response = await fetch(path, { ...options, method, headers, body });
  if (response.status === 401) {
    logout();
    throw new Error("Sessão expirada.");
  }
  if (!response.ok) {
    let detail = "Não foi possível concluir a operação.";
    try {
      const data = await response.json();
      detail = data.detail || detail;
    } catch {
      detail = await response.text();
    }
    throw new Error(Array.isArray(detail) ? "Dados inválidos." : detail);
  }
  if (response.status === 204) return null;
  const type = response.headers.get("content-type") || "";
  if (type.includes("application/json")) return response.json();
  return response.blob();
}

function setAuth(token, user) {
  state.token = token;
  state.user = user;
  localStorage.setItem("condoflow.token", token);
  localStorage.setItem("condoflow.user", JSON.stringify(user));
}

function logout() {
  state.token = null;
  state.user = null;
  localStorage.removeItem("condoflow.token");
  localStorage.removeItem("condoflow.user");
  $("#authScreen").classList.remove("hidden");
  $("#appShell").classList.add("hidden");
}

async function login(event) {
  event.preventDefault();
  const form = new URLSearchParams();
  form.set("username", $("#email").value.trim());
  form.set("password", $("#password").value);
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form,
  });
  if (!response.ok) {
    toast("E-mail ou senha inválidos.");
    return;
  }
  const data = await response.json();
  setAuth(data.access_token, data.user);
  await startApp();
}

async function startApp() {
  try {
    if (!state.token) {
      logout();
      return;
    }
    state.user = await api("/api/auth/me");
    localStorage.setItem("condoflow.user", JSON.stringify(state.user));
    $("#authScreen").classList.add("hidden");
    $("#appShell").classList.remove("hidden");
    $("#roleBadge").textContent = state.user.role === "proprietario" ? "Proprietário" : "Morador";
    applyRoleVisibility();
    await renderDashboard();
  } catch (error) {
    toast(error.message);
    logout();
  }
}

function applyRoleVisibility() {
  const ownerOnly = ["financeiro", "relatorios"];
  $$("#nav button").forEach((button) => {
    const view = button.dataset.view;
    button.classList.toggle("hidden", state.user.role === "morador" && ownerOnly.includes(view));
  });
}

async function renderDashboard() {
  setView("dashboard");
  $("#pageTitle").textContent = "Dashboard";
  $("#kicker").textContent = "Visão executiva";
  const data = await api("/api/dashboard");
  const metrics = [
    ["Moradores", data.moradores, "Pessoas vinculadas"],
    ["Imóveis", data.imoveis, "Carteira gerenciada"],
    ["Boletos pendentes", data.boletos_pendentes, "A receber"],
    ["Boletos pagos", data.boletos_pagos, "Baixados"],
    ["Aluguéis ativos", data.alugueis_ativos, "Contratos vigentes"],
    ["Avisos recentes", data.avisos_recentes, "Comunicação"],
    ["Ocorrências abertas", data.ocorrencias_abertas, "Atendimento"],
    ["Saldo do mês", money.format(data.saldo_mes), `${money.format(data.receitas_mes)} em receitas`],
  ];
  const grid = $("#metricGrid");
  grid.replaceChildren();
  metrics.forEach(([label, value, hint]) => {
    const card = document.createElement("article");
    card.className = "metric-card";
    const labelNode = document.createElement("span");
    labelNode.textContent = label;
    const valueNode = document.createElement("strong");
    valueNode.textContent = value;
    const hintNode = document.createElement("small");
    hintNode.textContent = hint;
    card.append(labelNode, valueNode, hintNode);
    grid.append(card);
  });
  drawFinanceChart($("#financeChart"), data.financeiro_por_mes || []);
  drawStatusChart($("#statusChart"), data.boletos_por_status || []);
  renderRecentNotices(data.avisos || []);
}

function renderRecentNotices(items) {
  $("#noticeCount").textContent = items.length;
  const list = $("#recentNotices");
  list.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "Nenhum aviso publicado.";
    list.append(empty);
    return;
  }
  items.forEach((item) => {
    const node = document.createElement("article");
    node.className = "notice-item";
    const title = document.createElement("strong");
    title.textContent = item.titulo;
    const message = document.createElement("span");
    message.textContent = item.mensagem;
    node.append(title, message);
    list.append(node);
  });
}

function drawFinanceChart(canvas, rows) {
  const ctx = setupCanvas(canvas);
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  ctx.clearRect(0, 0, width, height);
  const months = [...new Set(rows.map((row) => row.mes))].slice(-6);
  const grouped = months.map((mes) => ({
    mes,
    receita: rows.filter((row) => row.mes === mes && row.tipo === "receita").reduce((sum, row) => sum + Number(row.total), 0),
    despesa: rows.filter((row) => row.mes === mes && row.tipo === "despesa").reduce((sum, row) => sum + Number(row.total), 0),
  }));
  const max = Math.max(1, ...grouped.flatMap((row) => [row.receita, row.despesa]));
  const baseY = height - 36;
  ctx.strokeStyle = getCss("--line");
  ctx.beginPath();
  ctx.moveTo(30, baseY);
  ctx.lineTo(width - 18, baseY);
  ctx.stroke();
  grouped.forEach((row, index) => {
    const slot = (width - 70) / Math.max(grouped.length, 1);
    const x = 44 + index * slot;
    const receitaH = (row.receita / max) * (height - 78);
    const despesaH = (row.despesa / max) * (height - 78);
    ctx.fillStyle = "#10B981";
    roundRect(ctx, x, baseY - receitaH, 18, receitaH, 5);
    ctx.fillStyle = "#F59E0B";
    roundRect(ctx, x + 24, baseY - despesaH, 18, despesaH, 5);
    ctx.fillStyle = getCss("--muted");
    ctx.font = "12px system-ui";
    ctx.fillText(row.mes.slice(5), x, height - 12);
  });
}

function drawStatusChart(canvas, rows) {
  const ctx = setupCanvas(canvas);
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  ctx.clearRect(0, 0, width, height);
  const total = rows.reduce((sum, row) => sum + Number(row.total), 0) || 1;
  let start = -Math.PI / 2;
  const colors = ["#10B981", "#2563EB", "#F59E0B", "#EF4444", "#8B5CF6"];
  rows.forEach((row, index) => {
    const angle = (Number(row.total) / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(width / 2, height / 2);
    ctx.arc(width / 2, height / 2, Math.min(width, height) / 2 - 34, start, start + angle);
    ctx.closePath();
    ctx.fillStyle = colors[index % colors.length];
    ctx.fill();
    start += angle;
  });
  ctx.fillStyle = getCss("--surface");
  ctx.beginPath();
  ctx.arc(width / 2, height / 2, 54, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = getCss("--text");
  ctx.font = "700 24px system-ui";
  ctx.textAlign = "center";
  ctx.fillText(String(total), width / 2, height / 2 + 8);
  ctx.textAlign = "left";
}

function setupCanvas(canvas) {
  const ratio = window.devicePixelRatio || 1;
  const width = canvas.clientWidth || Number(canvas.getAttribute("width"));
  const height = canvas.clientHeight || Number(canvas.getAttribute("height"));
  canvas.width = width * ratio;
  canvas.height = height * ratio;
  const ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  return ctx;
}

function roundRect(ctx, x, y, width, height, radius) {
  ctx.beginPath();
  ctx.roundRect(x, y, width, Math.max(height, 1), radius);
  ctx.fill();
}

function getCss(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

async function renderModule(name = state.module) {
  state.module = name;
  const config = modules[name];
  if (!config) return;
  setView("module");
  $("#pageTitle").textContent = config.title;
  $("#kicker").textContent = "Módulo";
  $("#moduleTitle").textContent = config.title;
  $("#moduleSubtitle").textContent = config.subtitle;
  setupStatusFilter();
  $("#newRecord").classList.toggle("hidden", !canCreate(config));
  $("#exportCsv").classList.toggle("hidden", !config.report);

  const params = new URLSearchParams();
  if (state.search) params.set("search", state.search);
  if (state.status) params.set("status", state.status);
  params.set("page_size", "50");
  const data = await api(`${config.endpoint}?${params.toString()}`);
  state.records = data.items || [];
  renderTable(config, state.records);
}

function setupStatusFilter() {
  const select = $("#statusFilter");
  select.replaceChildren();
  statusOptions.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value ? value.replaceAll("_", " ") : "Todos";
    select.append(option);
  });
  select.value = state.status;
}

function renderTable(config, records) {
  const head = $("#tableHead");
  const body = $("#tableBody");
  head.replaceChildren();
  body.replaceChildren();

  const tr = document.createElement("tr");
  config.columns.forEach(([, label]) => {
    const th = document.createElement("th");
    th.textContent = label;
    tr.append(th);
  });
  const actionHead = document.createElement("th");
  actionHead.textContent = "Ações";
  tr.append(actionHead);
  head.append(tr);

  records.forEach((record) => {
    const row = document.createElement("tr");
    config.columns.forEach(([key, , type]) => {
      const td = document.createElement("td");
      td.append(formatCell(record[key], type));
      row.append(td);
    });
    const actions = document.createElement("td");
    actions.append(renderActions(config, record));
    row.append(actions);
    body.append(row);
  });
  $("#emptyState").classList.toggle("hidden", records.length > 0);
}

function formatCell(value, type) {
  if (type === "status") {
    const pill = document.createElement("span");
    pill.className = `status-pill ${statusClass(value)}`;
    pill.textContent = String(value || "-").replaceAll("_", " ");
    return pill;
  }
  const span = document.createElement("span");
  if (type === "money") span.textContent = money.format(Number(value || 0));
  else if (type === "date" && value) span.textContent = dateFmt.format(new Date(value));
  else if (type === "datetime" && value) span.textContent = new Date(value).toLocaleString("pt-BR");
  else if (type === "bool") span.textContent = value ? "Sim" : "Não";
  else if (type === "bytes") span.textContent = `${Math.ceil(Number(value || 0) / 1024)} KB`;
  else span.textContent = value ?? "-";
  return span;
}

function statusClass(value) {
  if (["vencido", "cancelado", "encerrado"].includes(value)) return "danger";
  if (["pendente", "aberta", "em_andamento", "renovacao"].includes(value)) return "warn";
  return "";
}

function renderActions(config, record) {
  const wrap = document.createElement("div");
  wrap.className = "row-actions";
  if (canEdit(config)) wrap.append(actionButton("✎", "Editar", () => openDrawer(record)));
  if (config.rowActions?.includes("pdf")) wrap.append(actionButton("PDF", "PDF", () => download(`/api/boletos/${record.id}/pdf`, `boleto-${record.numero}.pdf`)));
  if (config.rowActions?.includes("download")) wrap.append(actionButton("⇩", "Baixar", () => download(`/api/documentos/${record.id}/download`, record.titulo)));
  if (config.rowActions?.includes("pagar") && record.status !== "pago") wrap.append(actionButton("✓", "Pagar", () => runRecordAction(`/api/boletos/${record.id}/pagar`)));
  if (config.rowActions?.includes("cancelar") && state.user.role === "proprietario") wrap.append(actionButton("×", "Cancelar", () => runRecordAction(`/api/boletos/${record.id}/cancelar`)));
  if (config.rowActions?.includes("publicar") && state.user.role === "proprietario") wrap.append(actionButton("↑", "Publicar", () => runRecordAction(`/api/avisos/${record.id}/publicar`)));
  if (config.rowActions?.includes("arquivar") && state.user.role === "proprietario") wrap.append(actionButton("□", "Arquivar", () => runRecordAction(`/api/avisos/${record.id}/arquivar`)));
  if (config.rowActions?.includes("lido") && state.user.role === "morador" && !record.lido) wrap.append(actionButton("✓", "Lido", () => runRecordAction(`/api/avisos/${record.id}/lido`)));
  if (config.rowActions?.includes("encerrar") && state.user.role === "proprietario" && record.status === "ativo") wrap.append(actionButton("■", "Encerrar", () => runRecordAction(`/api/contratos/${record.id}/encerrar`)));
  if (canDelete(config)) wrap.append(actionButton("⌫", "Excluir", () => deleteRecord(record.id)));
  return wrap;
}

function actionButton(text, title, handler) {
  const button = document.createElement("button");
  button.type = "button";
  button.title = title;
  button.textContent = text;
  button.addEventListener("click", handler);
  return button;
}

function canCreate(config) {
  return config.rolesCreate?.includes(state.user.role);
}

function canEdit(config) {
  return state.user.role === "proprietario" && !config.upload;
}

function canDelete(config) {
  return state.user.role === "proprietario" && !["dashboard"].includes(state.module);
}

function openDrawer(record = null) {
  const config = modules[state.module];
  state.editing = record;
  $("#drawerTitle").textContent = record ? `Editar ${config.title}` : `Novo ${config.title}`;
  const form = $("#recordForm");
  form.replaceChildren();

  const grid = document.createElement("div");
  grid.className = "form-grid";
  config.fields.forEach(([name, label, type = "text", required = false, options = []]) => {
    if (record && type === "file") return;
    const wrapper = document.createElement("label");
    if (type === "textarea") wrapper.classList.add("full");
    wrapper.textContent = label;
    const input = buildInput(name, type, required, options, record?.[name]);
    wrapper.append(input);
    grid.append(wrapper);
  });
  form.append(grid);

  const actions = document.createElement("div");
  actions.className = "form-actions";
  const cancel = document.createElement("button");
  cancel.className = "secondary-button";
  cancel.type = "button";
  cancel.textContent = "Cancelar";
  cancel.addEventListener("click", closeDrawer);
  const save = document.createElement("button");
  save.className = "primary-button";
  save.type = "submit";
  save.textContent = record ? "Salvar" : "Criar";
  actions.append(cancel, save);
  form.append(actions);

  $("#drawer").classList.add("open");
  $("#drawer").setAttribute("aria-hidden", "false");
}

function buildInput(name, type, required, options, value) {
  let input;
  if (type === "textarea") {
    input = document.createElement("textarea");
  } else if (type === "select") {
    input = document.createElement("select");
    options.forEach((optionValue) => {
      const option = document.createElement("option");
      option.value = optionValue;
      option.textContent = optionValue.replaceAll("_", " ");
      input.append(option);
    });
  } else {
    input = document.createElement("input");
    input.type = type;
    if (type === "number") input.step = "0.01";
  }
  input.name = name;
  input.required = required;
  if (type === "checkbox") input.checked = value ?? true;
  else if (value !== undefined && value !== null) input.value = String(value).slice(0, type === "date" ? 10 : undefined);
  return input;
}

function closeDrawer() {
  $("#drawer").classList.remove("open");
  $("#drawer").setAttribute("aria-hidden", "true");
  state.editing = null;
}

async function saveRecord(event) {
  event.preventDefault();
  const config = modules[state.module];
  try {
    const body = collectForm(config);
    if (config.upload) {
      await api(config.endpoint, { method: "POST", body });
    } else if (state.editing) {
      await api(`${config.endpoint}/${state.editing.id}`, { method: "PUT", body });
    } else {
      await api(config.endpoint, { method: "POST", body });
    }
    closeDrawer();
    await renderModule(state.module);
    toast("Registro salvo.");
  } catch (error) {
    toast(error.message);
  }
}

function collectForm(config) {
  const form = $("#recordForm");
  if (config.upload) {
    const formData = new FormData(form);
    config.fields.forEach(([name, , type]) => {
      const value = formData.get(name);
      if (type !== "file" && value === "") formData.delete(name);
    });
    return formData;
  }
  const data = {};
  config.fields.forEach(([name, , type]) => {
    const input = form.elements[name];
    if (!input) return;
    if (type === "checkbox") {
      data[name] = input.checked;
      return;
    }
    if (input.value === "") return;
    if (type === "number") data[name] = Number(input.value);
    else data[name] = input.value;
  });
  return data;
}

async function deleteRecord(id) {
  if (!confirm("Excluir este registro?")) return;
  const config = modules[state.module];
  try {
    await api(`${config.endpoint}/${id}`, { method: "DELETE" });
    await renderModule(state.module);
    toast("Registro excluído.");
  } catch (error) {
    toast(error.message);
  }
}

async function runRecordAction(path) {
  try {
    await api(path, { method: "POST" });
    await renderModule(state.module);
    toast("Ação concluída.");
  } catch (error) {
    toast(error.message);
  }
}

async function download(path, filename) {
  try {
    const blob = await api(path);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename || "arquivo";
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  } catch (error) {
    toast(error.message);
  }
}

function renderReports() {
  setView("reports");
  $("#pageTitle").textContent = "Relatórios";
  $("#kicker").textContent = "Exportações";
  const grid = $("#reportGrid");
  grid.replaceChildren();
  reportTypes.forEach(([type, label]) => {
    const card = document.createElement("article");
    card.className = "report-card";
    const title = document.createElement("h2");
    title.textContent = label;
    const text = document.createElement("span");
    text.textContent = "Baixe uma visão completa deste módulo.";
    const actions = document.createElement("div");
    actions.className = "report-actions";
    ["csv", "xlsx", "pdf"].forEach((format) => {
      const button = document.createElement("button");
      button.className = "secondary-button";
      button.type = "button";
      button.textContent = format.toUpperCase();
      button.addEventListener("click", () => download(`/api/relatorios/${type}?formato=${format}`, `${type}.${format}`));
      actions.append(button);
    });
    card.append(title, text, actions);
    grid.append(card);
  });
}

function setView(view) {
  state.view = view;
  $("#dashboardView").classList.toggle("active-view", view === "dashboard");
  $("#moduleView").classList.toggle("active-view", view === "module");
  $("#reportsView").classList.toggle("active-view", view === "reports");
  $$("#nav button").forEach((button) => {
    const active = button.dataset.view === (view === "module" ? state.module : view);
    button.classList.toggle("active", active);
  });
}

function debounce(callback, delay = 260) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => callback(...args), delay);
  };
}

function applyTheme() {
  const theme = localStorage.getItem("condoflow.theme") || "light";
  document.documentElement.dataset.theme = theme;
}

function toggleTheme() {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  localStorage.setItem("condoflow.theme", next);
  if (state.view === "dashboard") renderDashboard().catch((error) => toast(error.message));
}

$("#loginForm").addEventListener("submit", login);
$("#logoutButton").addEventListener("click", logout);
$("#themeToggle").addEventListener("click", toggleTheme);
$("#closeDrawer").addEventListener("click", closeDrawer);
$("#recordForm").addEventListener("submit", saveRecord);
$("#statusFilter").addEventListener("change", async (event) => {
  state.status = event.target.value;
  await renderModule(state.module);
});
$("#newRecord").addEventListener("click", () => openDrawer());
$("#exportCsv").addEventListener("click", () => {
  const report = modules[state.module]?.report;
  if (report) download(`/api/relatorios/${report}?formato=csv`, `${report}.csv`);
});
$("#globalSearch").addEventListener(
  "input",
  debounce(async (event) => {
    state.search = event.target.value.trim();
    if (state.view === "module") await renderModule(state.module);
  }),
);

$$("[data-demo]").forEach((button) => {
  button.addEventListener("click", () => {
    const role = button.dataset.demo;
    $("#email").value = role === "morador" ? "morador@demo.com" : "proprietario@demo.com";
    $("#password").value = "Senha@123";
  });
});

$("#nav").addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-view]");
  if (!button) return;
  const view = button.dataset.view;
  state.status = "";
  $("#statusFilter").value = "";
  try {
    if (view === "dashboard") await renderDashboard();
    else if (view === "relatorios") renderReports();
    else await renderModule(view);
  } catch (error) {
    toast(error.message);
  }
});

window.addEventListener("resize", debounce(() => {
  if (state.view === "dashboard") renderDashboard().catch(() => {});
}, 180));

applyTheme();
startApp();


