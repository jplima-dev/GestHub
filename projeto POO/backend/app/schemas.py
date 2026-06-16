from __future__ import annotations

from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(ORMModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class CsrfToken(ORMModel):
    csrf_token: str


class UserBase(ORMModel):
    nome: str = Field(min_length=2, max_length=140)
    email: str = Field(min_length=5, max_length=255)
    role: str = Field(pattern="^(proprietario|morador)$")
    ativo: bool = True


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRead(UserBase):
    id: int
    ultimo_login: datetime | None = None
    criado_em: datetime


class Token(ORMModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ProprietarioBase(ORMModel):
    nome: str = Field(min_length=2, max_length=140)
    cpf_cnpj: str = Field(min_length=8, max_length=32)
    telefone: str | None = None
    endereco: str | None = None
    observacoes: str | None = None


class ProprietarioCreate(ProprietarioBase):
    user: UserCreate | None = None


class ProprietarioUpdate(ORMModel):
    nome: str | None = None
    cpf_cnpj: str | None = None
    telefone: str | None = None
    endereco: str | None = None
    observacoes: str | None = None


class ProprietarioRead(ProprietarioBase):
    id: int
    user_id: int
    criado_em: datetime
    atualizado_em: datetime


class CondominioBase(ORMModel):
    nome: str = Field(min_length=2, max_length=160)
    cnpj: str | None = None
    endereco: str = Field(min_length=3, max_length=255)
    cidade: str = Field(min_length=2, max_length=100)
    estado: str = Field(min_length=2, max_length=2)
    cep: str | None = None
    sindico: str | None = None
    telefone: str | None = None
    ativo: bool = True


class CondominioCreate(CondominioBase):
    pass


class CondominioUpdate(ORMModel):
    nome: str | None = None
    cnpj: str | None = None
    endereco: str | None = None
    cidade: str | None = None
    estado: str | None = Field(default=None, min_length=2, max_length=2)
    cep: str | None = None
    sindico: str | None = None
    telefone: str | None = None
    ativo: bool | None = None


class CondominioRead(CondominioBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime


class BlocoBase(ORMModel):
    condominio_id: int
    nome: str = Field(min_length=1, max_length=80)
    descricao: str | None = None


class BlocoCreate(BlocoBase):
    pass


class BlocoRead(BlocoBase):
    id: int


class UnidadeBase(ORMModel):
    condominio_id: int
    bloco_id: int | None = None
    codigo: str = Field(min_length=1, max_length=40)
    tipo: str = "apartamento"
    area_m2: float = 0
    quartos: int = 0
    banheiros: int = 0
    vagas: int = 0
    status: str = "disponivel"


class UnidadeCreate(UnidadeBase):
    pass


class UnidadeUpdate(ORMModel):
    bloco_id: int | None = None
    codigo: str | None = None
    tipo: str | None = None
    area_m2: float | None = None
    quartos: int | None = None
    banheiros: int | None = None
    vagas: int | None = None
    status: str | None = None


class UnidadeRead(UnidadeBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime


class MoradorBase(ORMModel):
    unidade_id: int | None = None
    nome: str = Field(min_length=2, max_length=140)
    email: str = Field(min_length=5, max_length=255)
    cpf: str = Field(min_length=8, max_length=20)
    telefone: str | None = None
    data_nascimento: date | None = None
    ocupacao: str | None = None
    status: str = "ativo"
    observacoes: str | None = None


class MoradorCreate(MoradorBase):
    user: UserCreate | None = None


class MoradorUpdate(ORMModel):
    unidade_id: int | None = None
    nome: str | None = None
    email: str | None = None
    cpf: str | None = None
    telefone: str | None = None
    data_nascimento: date | None = None
    ocupacao: str | None = None
    status: str | None = None
    observacoes: str | None = None


class MoradorRead(MoradorBase):
    id: int
    user_id: int | None = None
    criado_em: datetime
    atualizado_em: datetime


class ImovelBase(ORMModel):
    proprietario_id: int
    unidade_id: int | None = None
    tipo: str = Field(pattern="^(casa|apartamento|terreno|sala_comercial|loja|galpao)$")
    titulo: str = Field(min_length=2, max_length=160)
    endereco: str = Field(min_length=3, max_length=255)
    cidade: str = Field(min_length=2, max_length=100)
    estado: str = Field(min_length=2, max_length=2)
    valor: float = Field(ge=0)
    area_m2: float = Field(default=0, ge=0)
    status: str = "disponivel"
    descricao: str | None = None


class ImovelCreate(ImovelBase):
    pass


class ImovelUpdate(ORMModel):
    proprietario_id: int | None = None
    unidade_id: int | None = None
    tipo: str | None = None
    titulo: str | None = None
    endereco: str | None = None
    cidade: str | None = None
    estado: str | None = Field(default=None, min_length=2, max_length=2)
    valor: float | None = Field(default=None, ge=0)
    area_m2: float | None = Field(default=None, ge=0)
    status: str | None = None
    descricao: str | None = None


class ImovelRead(ImovelBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime


class ContratoBase(ORMModel):
    imovel_id: int
    morador_id: int
    proprietario_id: int
    inicio: date
    fim: date
    valor_aluguel: float = Field(gt=0)
    status: str = "ativo"
    reajuste_indice: str | None = "IGP-M"
    deposito_garantia: float = Field(default=0, ge=0)
    documento_url: str | None = None
    encerrado_em: date | None = None


class ContratoCreate(ContratoBase):
    pass


class ContratoUpdate(ORMModel):
    fim: date | None = None
    valor_aluguel: float | None = Field(default=None, gt=0)
    status: str | None = None
    reajuste_indice: str | None = None
    deposito_garantia: float | None = Field(default=None, ge=0)
    documento_url: str | None = None
    encerrado_em: date | None = None


class ContratoRead(ContratoBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime


class AluguelBase(ORMModel):
    contrato_id: int
    competencia: str = Field(pattern=r"^\d{4}-\d{2}$")
    valor: float = Field(gt=0)
    vencimento: date
    status: str = "pendente"
    pago_em: date | None = None
    observacoes: str | None = None


class AluguelCreate(AluguelBase):
    pass


class AluguelUpdate(ORMModel):
    competencia: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    valor: float | None = Field(default=None, gt=0)
    vencimento: date | None = None
    status: str | None = None
    pago_em: date | None = None
    observacoes: str | None = None


class AluguelRead(AluguelBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime


class BoletoBase(ORMModel):
    contrato_id: int | None = None
    morador_id: int
    imovel_id: int
    numero: str = Field(min_length=3, max_length=60)
    valor: float = Field(gt=0)
    vencimento: date
    status: str = "pendente"
    linha_digitavel: str | None = None
    pdf_path: str | None = None
    comprovante_path: str | None = None
    pago_em: date | None = None


class BoletoCreate(BoletoBase):
    pass


class BoletoUpdate(ORMModel):
    valor: float | None = Field(default=None, gt=0)
    vencimento: date | None = None
    status: str | None = None
    linha_digitavel: str | None = None
    pdf_path: str | None = None
    comprovante_path: str | None = None
    pago_em: date | None = None


class BoletoRead(BoletoBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime


class AvisoBase(ORMModel):
    titulo: str = Field(min_length=2, max_length=180)
    mensagem: str = Field(min_length=3)
    categoria: str = "geral"
    status: str = "rascunho"
    prioridade: str = "normal"
    anexo_path: str | None = None
    expira_em: datetime | None = None


class AvisoCreate(AvisoBase):
    pass


class AvisoUpdate(ORMModel):
    titulo: str | None = None
    mensagem: str | None = None
    categoria: str | None = None
    status: str | None = None
    prioridade: str | None = None
    anexo_path: str | None = None
    expira_em: datetime | None = None


class AvisoRead(AvisoBase):
    id: int
    autor_id: int
    publicado_em: datetime | None = None
    criado_em: datetime
    atualizado_em: datetime
    lido: bool = False


class OcorrenciaBase(ORMModel):
    morador_id: int | None = None
    imovel_id: int | None = None
    titulo: str = Field(min_length=2, max_length=180)
    descricao: str = Field(min_length=3)
    tipo: str = "solicitacao"
    status: str = "aberta"
    prioridade: str = "media"
    resolvido_em: datetime | None = None


class OcorrenciaCreate(OcorrenciaBase):
    pass


class OcorrenciaUpdate(ORMModel):
    imovel_id: int | None = None
    titulo: str | None = None
    descricao: str | None = None
    tipo: str | None = None
    status: str | None = None
    prioridade: str | None = None
    resolvido_em: datetime | None = None


class OcorrenciaRead(OcorrenciaBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime


class DocumentoBase(ORMModel):
    contrato_id: int | None = None
    imovel_id: int | None = None
    titulo: str = Field(min_length=2, max_length=180)
    categoria: str = "geral"


class DocumentoCreate(DocumentoBase):
    file_path: str
    mime_type: str | None = None
    tamanho: int = 0


class DocumentoRead(DocumentoBase):
    id: int
    owner_user_id: int
    file_path: str
    mime_type: str | None = None
    tamanho: int
    criado_em: datetime
    atualizado_em: datetime


class LancamentoBase(ORMModel):
    proprietario_id: int
    contrato_id: int | None = None
    boleto_id: int | None = None
    tipo: str = Field(pattern="^(receita|despesa)$")
    categoria: str
    descricao: str
    valor: float = Field(gt=0)
    data: date
    status: str = "realizado"


class LancamentoCreate(LancamentoBase):
    pass


class LancamentoUpdate(ORMModel):
    contrato_id: int | None = None
    boleto_id: int | None = None
    tipo: str | None = None
    categoria: str | None = None
    descricao: str | None = None
    valor: float | None = Field(default=None, gt=0)
    data: date | None = None
    status: str | None = None


class LancamentoRead(LancamentoBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime


class DashboardSummary(ORMModel):
    moradores: int
    imoveis: int
    boletos_pendentes: int
    boletos_pagos: int
    alugueis_ativos: int
    avisos_recentes: int
    ocorrencias_abertas: int
    receitas_mes: float
    despesas_mes: float
    saldo_mes: float
    financeiro_por_mes: list[dict[str, float | str]]
    boletos_por_status: list[dict[str, int | str]]
    avisos: list[AvisoRead]


class ReportRequest(ORMModel):
    tipo: str = Field(pattern="^(moradores|boletos|financeiro|contratos|ocorrencias)$")
    formato: str = Field(pattern="^(csv|xlsx|pdf)$")
