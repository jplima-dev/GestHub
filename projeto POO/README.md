# CondoFlow

Sistema web profissional para gerenciamento de condomínios, imóveis, moradores, contratos, aluguéis, boletos, ocorrências, documentos e finanças.

## Stack

- Backend: Python, FastAPI, SQLAlchemy e SQLite
- Frontend: HTML, CSS e JavaScript responsivo
- Segurança: hash PBKDF2, JWT, CSRF token, CORS, headers de segurança, RBAC e auditoria
- Relatórios: CSV, Excel e PDF
- Documentação: Swagger/OpenAPI em `/docs`

## Estrutura

```text
backend/app/
  core/              configuração, banco, segurança e auditoria
  routers/           endpoints REST por módulo
  models.py          modelos relacionais SQLAlchemy
  schemas.py         validação e contratos da API
  seed.py            dados iniciais
frontend/
  index.html         aplicação web
  styles.css         tema claro/escuro e layout SaaS
  app.js             consumo da API, dashboard e CRUD
scripts/
  init_db.py         cria o banco e popula dados demo
  schema.sql         DDL SQLite
docs/
  ERD.md             diagrama entidade-relacionamento
```

## Instalação

```powershell
cd "E:\projeto POO\projeto POO"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\init_db.py
uvicorn backend.app.main:app --reload
```

Acesse:

- Aplicação: http://127.0.0.1:8000
- Swagger/OpenAPI: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

## Usuários demo

```text
Proprietário
E-mail: proprietario@demo.com
Senha: Senha@123

Morador
E-mail: morador@demo.com
Senha: Senha@123
```

## Módulos

- Dashboard: moradores, imóveis, boletos, aluguéis, avisos, ocorrências e resumo financeiro com gráficos.
- Moradores: cadastro, edição, exclusão, busca, filtros e perfil completo.
- Avisos: criar, editar, publicar, arquivar, anexos e leitura por morador.
- Boletos: geração, listagem, pagamento, histórico, PDF e status.
- Aluguel e contratos: vigência, renovação, encerramento, reajustes e pagamentos.
- Condomínios: condomínios, blocos, torres e unidades.
- Imóveis: casas, apartamentos, terrenos, salas comerciais, lojas e galpões.
- Financeiro: receitas, despesas, fluxo de caixa, balancete e relatórios.
- Ocorrências: reclamações, solicitações, sugestões e manutenção.
- Documentos: upload, download e categorização.
- Relatórios: exportação em CSV, Excel e PDF.

## Perfis

- Proprietário: gerencia imóveis, contratos, pagamentos, moradores, boletos, documentos, ocorrências, avisos e finanças.
- Morador: visualiza seus dados, avisos, boletos, aluguel, documentos e abre ocorrências.

## API

Principais grupos de endpoints:

```text
POST /api/auth/login
GET  /api/auth/me
GET  /api/dashboard
/api/moradores
/api/proprietarios
/api/condominios
/api/imoveis
/api/avisos
/api/boletos
/api/alugueis
/api/contratos
/api/documentos
/api/ocorrencias
/api/financeiro
/api/relatorios/{tipo}?formato=csv|xlsx|pdf
```

Todas as rotas protegidas usam `Authorization: Bearer <token>`. Requisições de escrita exigem também o header `x-csrf-token`, obtido em `GET /api/auth/csrf`.

## Banco de dados

O SQLite é criado em `backend/data/condoflow.db`. O script SQL está em `scripts/schema.sql` e o diagrama ER em `docs/ERD.md`.

## Produção

Antes de publicar, altere `JWT_SECRET_KEY`, restrinja `ALLOWED_ORIGINS`, use HTTPS, configure backup do SQLite ou migre para PostgreSQL, e proteja a pasta de uploads com política de retenção e antivírus.

