from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from backend.app.core.database import Base
from backend.app.core.security import now_utc


class TimestampMixin:
    criado_em = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    atualizado_em = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


class User(Base, TimestampMixin):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(140), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, index=True)
    ativo = Column(Boolean, default=True, nullable=False)
    avatar_path = Column(String(255))
    ultimo_login = Column(DateTime(timezone=True))

    proprietario = relationship("Proprietario", back_populates="user", uselist=False, cascade="all, delete-orphan")
    morador = relationship("Morador", back_populates="user", uselist=False, cascade="all, delete-orphan")
    avisos_autoria = relationship("Aviso", back_populates="autor")
    propriedades = relationship("PropriedadeUsuario", back_populates="user", cascade="all, delete-orphan")


class Proprietario(Base, TimestampMixin):
    __tablename__ = "proprietarios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=False)
    nome = Column(String(140), nullable=False)
    cpf_cnpj = Column(String(32), unique=True, nullable=False)
    telefone = Column(String(32))
    endereco = Column(String(255))
    observacoes = Column(Text)

    user = relationship("User", back_populates="proprietario")
    imoveis = relationship("Imovel", back_populates="proprietario")
    contratos = relationship("Contrato", back_populates="proprietario")
    lancamentos = relationship("LancamentoFinanceiro", back_populates="proprietario")


class Condominio(Base, TimestampMixin):
    __tablename__ = "condominios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(160), nullable=False)
    cnpj = Column(String(32), unique=True)
    endereco = Column(String(255), nullable=False)
    cidade = Column(String(100), nullable=False)
    estado = Column(String(2), nullable=False)
    cep = Column(String(16))
    sindico = Column(String(140))
    telefone = Column(String(32))
    ativo = Column(Boolean, default=True, nullable=False)

    blocos = relationship("Bloco", back_populates="condominio", cascade="all, delete-orphan")
    unidades = relationship("Unidade", back_populates="condominio", cascade="all, delete-orphan")


class Bloco(Base, TimestampMixin):
    __tablename__ = "blocos"

    id = Column(Integer, primary_key=True, index=True)
    condominio_id = Column(Integer, ForeignKey("condominios.id"), nullable=False)
    nome = Column(String(80), nullable=False)
    descricao = Column(Text)

    condominio = relationship("Condominio", back_populates="blocos")
    unidades = relationship("Unidade", back_populates="bloco")


class Unidade(Base, TimestampMixin):
    __tablename__ = "unidades"
    __table_args__ = (UniqueConstraint("condominio_id", "codigo", name="uq_unidade_condominio_codigo"),)

    id = Column(Integer, primary_key=True, index=True)
    condominio_id = Column(Integer, ForeignKey("condominios.id"), nullable=False)
    bloco_id = Column(Integer, ForeignKey("blocos.id"))
    codigo = Column(String(40), nullable=False)
    tipo = Column(String(60), nullable=False, default="apartamento")
    area_m2 = Column(Float, default=0)
    quartos = Column(Integer, default=0)
    banheiros = Column(Integer, default=0)
    vagas = Column(Integer, default=0)
    status = Column(String(40), default="disponivel", nullable=False)

    condominio = relationship("Condominio", back_populates="unidades")
    bloco = relationship("Bloco", back_populates="unidades")
    moradores = relationship("Morador", back_populates="unidade")
    imovel = relationship("Imovel", back_populates="unidade", uselist=False)


class Morador(Base, TimestampMixin):
    __tablename__ = "moradores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), unique=True)
    unidade_id = Column(Integer, ForeignKey("unidades.id"))
    nome = Column(String(140), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    cpf = Column(String(20), unique=True, nullable=False)
    telefone = Column(String(32))
    data_nascimento = Column(Date)
    ocupacao = Column(String(120))
    status = Column(String(40), default="ativo", nullable=False)
    observacoes = Column(Text)

    user = relationship("User", back_populates="morador")
    unidade = relationship("Unidade", back_populates="moradores")
    contratos = relationship("Contrato", back_populates="morador")
    boletos = relationship("Boleto", back_populates="morador")
    ocorrencias = relationship("Ocorrencia", back_populates="morador")
    leituras = relationship("AvisoLeitura", back_populates="morador", cascade="all, delete-orphan")


class Imovel(Base, TimestampMixin):
    __tablename__ = "imoveis"

    id = Column(Integer, primary_key=True, index=True)
    proprietario_id = Column(Integer, ForeignKey("proprietarios.id"), nullable=False)
    unidade_id = Column(Integer, ForeignKey("unidades.id"))
    tipo = Column(String(60), nullable=False)
    titulo = Column(String(160), nullable=False)
    endereco = Column(String(255), nullable=False)
    cidade = Column(String(100), nullable=False)
    estado = Column(String(2), nullable=False)
    valor = Column(Float, default=0, nullable=False)
    area_m2 = Column(Float, default=0)
    status = Column(String(40), default="disponivel", nullable=False)
    descricao = Column(Text)

    proprietario = relationship("Proprietario", back_populates="imoveis")
    unidade = relationship("Unidade", back_populates="imovel")
    contratos = relationship("Contrato", back_populates="imovel")
    boletos = relationship("Boleto", back_populates="imovel")
    ocorrencias = relationship("Ocorrencia", back_populates="imovel")
    documentos = relationship("Documento", back_populates="imovel")
    usuarios = relationship("PropriedadeUsuario", back_populates="imovel", cascade="all, delete-orphan")


class PropriedadeUsuario(Base, TimestampMixin):
    __tablename__ = "propriedades_usuarios"
    __table_args__ = (UniqueConstraint("user_id", "imovel_id", name="uq_usuario_imovel"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    imovel_id = Column(Integer, ForeignKey("imoveis.id"), nullable=False)
    role = Column(String(30), default="viewer", nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="propriedades")
    imovel = relationship("Imovel", back_populates="usuarios")


class Contrato(Base, TimestampMixin):
    __tablename__ = "contratos"

    id = Column(Integer, primary_key=True, index=True)
    imovel_id = Column(Integer, ForeignKey("imoveis.id"), nullable=False)
    morador_id = Column(Integer, ForeignKey("moradores.id"), nullable=False)
    proprietario_id = Column(Integer, ForeignKey("proprietarios.id"), nullable=False)
    inicio = Column(Date, nullable=False)
    fim = Column(Date, nullable=False)
    valor_aluguel = Column(Float, nullable=False)
    status = Column(String(40), default="ativo", nullable=False)
    reajuste_indice = Column(String(40), default="IGP-M")
    deposito_garantia = Column(Float, default=0)
    documento_url = Column(String(255))
    encerrado_em = Column(Date)

    imovel = relationship("Imovel", back_populates="contratos")
    morador = relationship("Morador", back_populates="contratos")
    proprietario = relationship("Proprietario", back_populates="contratos")
    alugueis = relationship("Aluguel", back_populates="contrato")
    boletos = relationship("Boleto", back_populates="contrato")
    documentos = relationship("Documento", back_populates="contrato")
    lancamentos = relationship("LancamentoFinanceiro", back_populates="contrato")


class Aluguel(Base, TimestampMixin):
    __tablename__ = "alugueis"

    id = Column(Integer, primary_key=True, index=True)
    contrato_id = Column(Integer, ForeignKey("contratos.id"), nullable=False)
    competencia = Column(String(7), nullable=False)
    valor = Column(Float, nullable=False)
    vencimento = Column(Date, nullable=False)
    status = Column(String(40), default="pendente", nullable=False)
    pago_em = Column(Date)
    observacoes = Column(Text)

    contrato = relationship("Contrato", back_populates="alugueis")


class Boleto(Base, TimestampMixin):
    __tablename__ = "boletos"

    id = Column(Integer, primary_key=True, index=True)
    contrato_id = Column(Integer, ForeignKey("contratos.id"))
    morador_id = Column(Integer, ForeignKey("moradores.id"), nullable=False)
    imovel_id = Column(Integer, ForeignKey("imoveis.id"), nullable=False)
    numero = Column(String(60), unique=True, index=True, nullable=False)
    valor = Column(Float, nullable=False)
    vencimento = Column(Date, nullable=False)
    status = Column(String(40), default="pendente", nullable=False)
    linha_digitavel = Column(String(120))
    pdf_path = Column(String(255))
    comprovante_path = Column(String(255))
    pago_em = Column(Date)

    contrato = relationship("Contrato", back_populates="boletos")
    morador = relationship("Morador", back_populates="boletos")
    imovel = relationship("Imovel", back_populates="boletos")
    lancamentos = relationship("LancamentoFinanceiro", back_populates="boleto")


class Aviso(Base, TimestampMixin):
    __tablename__ = "avisos"

    id = Column(Integer, primary_key=True, index=True)
    autor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    imovel_id = Column(Integer, ForeignKey("imoveis.id"))
    titulo = Column(String(180), nullable=False)
    mensagem = Column(Text, nullable=False)
    categoria = Column(String(60), default="geral", nullable=False)
    status = Column(String(40), default="rascunho", nullable=False)
    prioridade = Column(String(40), default="normal", nullable=False)
    anexo_path = Column(String(255))
    publicado_em = Column(DateTime(timezone=True))
    expira_em = Column(DateTime(timezone=True))

    autor = relationship("User", back_populates="avisos_autoria")
    imovel = relationship("Imovel")
    leituras = relationship("AvisoLeitura", back_populates="aviso", cascade="all, delete-orphan")


class AvisoLeitura(Base):
    __tablename__ = "avisos_leituras"
    __table_args__ = (UniqueConstraint("aviso_id", "morador_id", name="uq_aviso_morador_lido"),)

    id = Column(Integer, primary_key=True, index=True)
    aviso_id = Column(Integer, ForeignKey("avisos.id"), nullable=False)
    morador_id = Column(Integer, ForeignKey("moradores.id"), nullable=False)
    lido_em = Column(DateTime(timezone=True), default=now_utc, nullable=False)

    aviso = relationship("Aviso", back_populates="leituras")
    morador = relationship("Morador", back_populates="leituras")


class Ocorrencia(Base, TimestampMixin):
    __tablename__ = "ocorrencias"

    id = Column(Integer, primary_key=True, index=True)
    morador_id = Column(Integer, ForeignKey("moradores.id"), nullable=False)
    imovel_id = Column(Integer, ForeignKey("imoveis.id"))
    titulo = Column(String(180), nullable=False)
    descricao = Column(Text, nullable=False)
    tipo = Column(String(60), nullable=False, default="solicitacao")
    status = Column(String(40), default="aberta", nullable=False)
    prioridade = Column(String(40), default="media", nullable=False)
    resolvido_em = Column(DateTime(timezone=True))

    morador = relationship("Morador", back_populates="ocorrencias")
    imovel = relationship("Imovel", back_populates="ocorrencias")


class Documento(Base, TimestampMixin):
    __tablename__ = "documentos"

    id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    contrato_id = Column(Integer, ForeignKey("contratos.id"))
    imovel_id = Column(Integer, ForeignKey("imoveis.id"))
    titulo = Column(String(180), nullable=False)
    categoria = Column(String(80), default="geral", nullable=False)
    file_path = Column(String(255), nullable=False)
    mime_type = Column(String(120))
    tamanho = Column(Integer, default=0)

    owner = relationship("User")
    contrato = relationship("Contrato", back_populates="documentos")
    imovel = relationship("Imovel", back_populates="documentos")


class LancamentoFinanceiro(Base, TimestampMixin):
    __tablename__ = "lancamentos_financeiros"

    id = Column(Integer, primary_key=True, index=True)
    proprietario_id = Column(Integer, ForeignKey("proprietarios.id"), nullable=False)
    contrato_id = Column(Integer, ForeignKey("contratos.id"))
    boleto_id = Column(Integer, ForeignKey("boletos.id"))
    tipo = Column(String(30), nullable=False)
    categoria = Column(String(80), nullable=False)
    descricao = Column(String(220), nullable=False)
    valor = Column(Float, nullable=False)
    data = Column(Date, nullable=False)
    status = Column(String(40), default="realizado", nullable=False)

    proprietario = relationship("Proprietario", back_populates="lancamentos")
    contrato = relationship("Contrato", back_populates="lancamentos")
    boleto = relationship("Boleto", back_populates="lancamentos")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"))
    acao = Column(String(80), nullable=False)
    recurso = Column(String(80), nullable=False)
    recurso_id = Column(Integer)
    ip = Column(String(80))
    detalhes = Column(Text)
    criado_em = Column(DateTime(timezone=True), default=now_utc, nullable=False)

    user = relationship("User")
