from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from backend.app import models
from backend.app.core.security import hash_password, now_utc


def seed_database(db: Session) -> None:
    if db.query(models.User).count() > 0:
        return

    owner_user = models.User(
        nome="Ana Proprietária",
        email="proprietario@demo.com",
        role="proprietario",
        password_hash=hash_password("Senha@123"),
    )
    resident_user = models.User(
        nome="Bruno Morador",
        email="morador@demo.com",
        role="morador",
        password_hash=hash_password("Senha@123"),
    )
    db.add_all([owner_user, resident_user])
    db.flush()

    owner = models.Proprietario(
        user_id=owner_user.id,
        nome="Ana Proprietária",
        cpf_cnpj="12345678000190",
        telefone="(11) 99999-1000",
        endereco="Av. Paulista, 1000 - São Paulo/SP",
    )
    db.add(owner)
    db.flush()

    condo = models.Condominio(
        nome="Residencial Esmeralda",
        cnpj="98765432000110",
        endereco="Rua das Palmeiras, 480",
        cidade="São Paulo",
        estado="SP",
        cep="01310-000",
        sindico="Marina Alves",
        telefone="(11) 3333-4444",
    )
    db.add(condo)
    db.flush()

    bloco = models.Bloco(condominio_id=condo.id, nome="Torre A", descricao="Torre principal")
    db.add(bloco)
    db.flush()

    unidade = models.Unidade(
        condominio_id=condo.id,
        bloco_id=bloco.id,
        codigo="A-1204",
        tipo="apartamento",
        area_m2=72,
        quartos=2,
        banheiros=2,
        vagas=1,
        status="ocupada",
    )
    db.add(unidade)
    db.flush()

    morador = models.Morador(
        user_id=resident_user.id,
        unidade_id=unidade.id,
        nome="Bruno Morador",
        email="morador@demo.com",
        cpf="12345678900",
        telefone="(11) 98888-2000",
        data_nascimento=date(1992, 5, 20),
        ocupacao="Designer",
        status="ativo",
    )
    db.add(morador)
    db.flush()

    imovel = models.Imovel(
        proprietario_id=owner.id,
        unidade_id=unidade.id,
        tipo="apartamento",
        titulo="Apartamento A-1204 - Residencial Esmeralda",
        endereco="Rua das Palmeiras, 480 - A-1204",
        cidade="São Paulo",
        estado="SP",
        valor=3200.00,
        area_m2=72,
        status="alugado",
        descricao="Apartamento mobiliado com varanda e vaga coberta.",
    )
    db.add(imovel)
    db.flush()

    contrato = models.Contrato(
        imovel_id=imovel.id,
        morador_id=morador.id,
        proprietario_id=owner.id,
        inicio=date.today().replace(day=1),
        fim=date.today().replace(year=date.today().year + 1),
        valor_aluguel=3200.00,
        status="ativo",
        reajuste_indice="IPCA",
        deposito_garantia=6400.00,
    )
    db.add(contrato)
    db.flush()

    boleto_pendente = models.Boleto(
        contrato_id=contrato.id,
        morador_id=morador.id,
        imovel_id=imovel.id,
        numero="BOL-2026-0001",
        valor=3200.00,
        vencimento=date.today() + timedelta(days=8),
        status="pendente",
        linha_digitavel="34191.79001 01043.510047 91020.150008 7 98760000320000",
    )
    boleto_pago = models.Boleto(
        contrato_id=contrato.id,
        morador_id=morador.id,
        imovel_id=imovel.id,
        numero="BOL-2026-0000",
        valor=3200.00,
        vencimento=date.today() - timedelta(days=23),
        status="pago",
        pago_em=date.today() - timedelta(days=20),
        linha_digitavel="34191.79001 01043.510047 91020.150008 7 98750000320000",
    )
    db.add_all([boleto_pendente, boleto_pago])
    db.flush()

    aluguel = models.Aluguel(
        contrato_id=contrato.id,
        competencia=date.today().strftime("%Y-%m"),
        valor=3200.00,
        vencimento=date.today() + timedelta(days=8),
        status="pendente",
    )
    db.add(aluguel)

    aviso = models.Aviso(
        autor_id=owner_user.id,
        titulo="Manutenção preventiva dos elevadores",
        mensagem="A manutenção ocorrerá das 9h às 12h. O acesso pela escada estará sinalizado.",
        categoria="manutencao",
        status="publicado",
        prioridade="alta",
        publicado_em=now_utc(),
    )
    db.add(aviso)

    ocorrencia = models.Ocorrencia(
        morador_id=morador.id,
        imovel_id=imovel.id,
        titulo="Lâmpada queimada no corredor",
        descricao="A lâmpada próxima ao elevador do 12º andar precisa de troca.",
        tipo="manutencao",
        status="aberta",
        prioridade="media",
    )
    db.add(ocorrencia)

    db.add_all(
        [
            models.LancamentoFinanceiro(
                proprietario_id=owner.id,
                contrato_id=contrato.id,
                boleto_id=boleto_pago.id,
                tipo="receita",
                categoria="Aluguel",
                descricao="Aluguel recebido",
                valor=3200.00,
                data=date.today() - timedelta(days=20),
            ),
            models.LancamentoFinanceiro(
                proprietario_id=owner.id,
                tipo="despesa",
                categoria="Manutenção",
                descricao="Revisão hidráulica preventiva",
                valor=680.00,
                data=date.today() - timedelta(days=12),
            ),
        ]
    )

    db.commit()
