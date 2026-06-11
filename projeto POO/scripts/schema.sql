PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome VARCHAR(140) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(30) NOT NULL CHECK (role IN ('proprietario', 'morador')),
  ativo BOOLEAN NOT NULL DEFAULT 1,
  ultimo_login DATETIME,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS proprietarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  nome VARCHAR(140) NOT NULL,
  cpf_cnpj VARCHAR(32) NOT NULL UNIQUE,
  telefone VARCHAR(32),
  endereco VARCHAR(255),
  observacoes TEXT,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS condominios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome VARCHAR(160) NOT NULL,
  cnpj VARCHAR(32) UNIQUE,
  endereco VARCHAR(255) NOT NULL,
  cidade VARCHAR(100) NOT NULL,
  estado VARCHAR(2) NOT NULL,
  cep VARCHAR(16),
  sindico VARCHAR(140),
  telefone VARCHAR(32),
  ativo BOOLEAN NOT NULL DEFAULT 1,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blocos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  condominio_id INTEGER NOT NULL,
  nome VARCHAR(80) NOT NULL,
  descricao TEXT,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (condominio_id) REFERENCES condominios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS unidades (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  condominio_id INTEGER NOT NULL,
  bloco_id INTEGER,
  codigo VARCHAR(40) NOT NULL,
  tipo VARCHAR(60) NOT NULL DEFAULT 'apartamento',
  area_m2 FLOAT DEFAULT 0,
  quartos INTEGER DEFAULT 0,
  banheiros INTEGER DEFAULT 0,
  vagas INTEGER DEFAULT 0,
  status VARCHAR(40) NOT NULL DEFAULT 'disponivel',
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (condominio_id, codigo),
  FOREIGN KEY (condominio_id) REFERENCES condominios(id) ON DELETE CASCADE,
  FOREIGN KEY (bloco_id) REFERENCES blocos(id)
);

CREATE TABLE IF NOT EXISTS moradores (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER UNIQUE,
  unidade_id INTEGER,
  nome VARCHAR(140) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  cpf VARCHAR(20) NOT NULL UNIQUE,
  telefone VARCHAR(32),
  data_nascimento DATE,
  ocupacao VARCHAR(120),
  status VARCHAR(40) NOT NULL DEFAULT 'ativo',
  observacoes TEXT,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES usuarios(id) ON DELETE SET NULL,
  FOREIGN KEY (unidade_id) REFERENCES unidades(id)
);

CREATE TABLE IF NOT EXISTS imoveis (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  proprietario_id INTEGER NOT NULL,
  unidade_id INTEGER,
  tipo VARCHAR(60) NOT NULL,
  titulo VARCHAR(160) NOT NULL,
  endereco VARCHAR(255) NOT NULL,
  cidade VARCHAR(100) NOT NULL,
  estado VARCHAR(2) NOT NULL,
  valor FLOAT NOT NULL DEFAULT 0,
  area_m2 FLOAT DEFAULT 0,
  status VARCHAR(40) NOT NULL DEFAULT 'disponivel',
  descricao TEXT,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (proprietario_id) REFERENCES proprietarios(id),
  FOREIGN KEY (unidade_id) REFERENCES unidades(id)
);

CREATE TABLE IF NOT EXISTS contratos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  imovel_id INTEGER NOT NULL,
  morador_id INTEGER NOT NULL,
  proprietario_id INTEGER NOT NULL,
  inicio DATE NOT NULL,
  fim DATE NOT NULL,
  valor_aluguel FLOAT NOT NULL,
  status VARCHAR(40) NOT NULL DEFAULT 'ativo',
  reajuste_indice VARCHAR(40) DEFAULT 'IGP-M',
  deposito_garantia FLOAT DEFAULT 0,
  documento_url VARCHAR(255),
  encerrado_em DATE,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (imovel_id) REFERENCES imoveis(id),
  FOREIGN KEY (morador_id) REFERENCES moradores(id),
  FOREIGN KEY (proprietario_id) REFERENCES proprietarios(id)
);

CREATE TABLE IF NOT EXISTS alugueis (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  contrato_id INTEGER NOT NULL,
  competencia VARCHAR(7) NOT NULL,
  valor FLOAT NOT NULL,
  vencimento DATE NOT NULL,
  status VARCHAR(40) NOT NULL DEFAULT 'pendente',
  pago_em DATE,
  observacoes TEXT,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (contrato_id) REFERENCES contratos(id)
);

CREATE TABLE IF NOT EXISTS boletos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  contrato_id INTEGER,
  morador_id INTEGER NOT NULL,
  imovel_id INTEGER NOT NULL,
  numero VARCHAR(60) NOT NULL UNIQUE,
  valor FLOAT NOT NULL,
  vencimento DATE NOT NULL,
  status VARCHAR(40) NOT NULL DEFAULT 'pendente',
  linha_digitavel VARCHAR(120),
  pdf_path VARCHAR(255),
  comprovante_path VARCHAR(255),
  pago_em DATE,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (contrato_id) REFERENCES contratos(id),
  FOREIGN KEY (morador_id) REFERENCES moradores(id),
  FOREIGN KEY (imovel_id) REFERENCES imoveis(id)
);

CREATE TABLE IF NOT EXISTS avisos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  autor_id INTEGER NOT NULL,
  titulo VARCHAR(180) NOT NULL,
  mensagem TEXT NOT NULL,
  categoria VARCHAR(60) NOT NULL DEFAULT 'geral',
  status VARCHAR(40) NOT NULL DEFAULT 'rascunho',
  prioridade VARCHAR(40) NOT NULL DEFAULT 'normal',
  anexo_path VARCHAR(255),
  publicado_em DATETIME,
  expira_em DATETIME,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (autor_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS avisos_leituras (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  aviso_id INTEGER NOT NULL,
  morador_id INTEGER NOT NULL,
  lido_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (aviso_id, morador_id),
  FOREIGN KEY (aviso_id) REFERENCES avisos(id) ON DELETE CASCADE,
  FOREIGN KEY (morador_id) REFERENCES moradores(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ocorrencias (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  morador_id INTEGER NOT NULL,
  imovel_id INTEGER,
  titulo VARCHAR(180) NOT NULL,
  descricao TEXT NOT NULL,
  tipo VARCHAR(60) NOT NULL DEFAULT 'solicitacao',
  status VARCHAR(40) NOT NULL DEFAULT 'aberta',
  prioridade VARCHAR(40) NOT NULL DEFAULT 'media',
  resolvido_em DATETIME,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (morador_id) REFERENCES moradores(id),
  FOREIGN KEY (imovel_id) REFERENCES imoveis(id)
);

CREATE TABLE IF NOT EXISTS documentos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_user_id INTEGER NOT NULL,
  contrato_id INTEGER,
  imovel_id INTEGER,
  titulo VARCHAR(180) NOT NULL,
  categoria VARCHAR(80) NOT NULL DEFAULT 'geral',
  file_path VARCHAR(255) NOT NULL,
  mime_type VARCHAR(120),
  tamanho INTEGER DEFAULT 0,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (owner_user_id) REFERENCES usuarios(id),
  FOREIGN KEY (contrato_id) REFERENCES contratos(id),
  FOREIGN KEY (imovel_id) REFERENCES imoveis(id)
);

CREATE TABLE IF NOT EXISTS lancamentos_financeiros (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  proprietario_id INTEGER NOT NULL,
  contrato_id INTEGER,
  boleto_id INTEGER,
  tipo VARCHAR(30) NOT NULL CHECK (tipo IN ('receita', 'despesa')),
  categoria VARCHAR(80) NOT NULL,
  descricao VARCHAR(220) NOT NULL,
  valor FLOAT NOT NULL,
  data DATE NOT NULL,
  status VARCHAR(40) NOT NULL DEFAULT 'realizado',
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (proprietario_id) REFERENCES proprietarios(id),
  FOREIGN KEY (contrato_id) REFERENCES contratos(id),
  FOREIGN KEY (boleto_id) REFERENCES boletos(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  acao VARCHAR(80) NOT NULL,
  recurso VARCHAR(80) NOT NULL,
  recurso_id INTEGER,
  ip VARCHAR(80),
  detalhes TEXT,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES usuarios(id)
);

CREATE INDEX IF NOT EXISTS ix_moradores_nome ON moradores(nome);
CREATE INDEX IF NOT EXISTS ix_imoveis_status ON imoveis(status);
CREATE INDEX IF NOT EXISTS ix_boletos_status ON boletos(status);
CREATE INDEX IF NOT EXISTS ix_contratos_status ON contratos(status);
CREATE INDEX IF NOT EXISTS ix_ocorrencias_status ON ocorrencias(status);
CREATE INDEX IF NOT EXISTS ix_lancamentos_data ON lancamentos_financeiros(data);

