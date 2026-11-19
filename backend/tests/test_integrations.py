"""Testes dos adaptadores de integração (sem dependência de rede no teste padrão)."""

from app.integrations.adapters import (
    CNESAdapter,
    DatasusHospitaisLeitosAdapter,
    IbgeAdapter,
    classify_unit_type,
)


def test_classify_unit_type():
    assert classify_unit_type("HOSPITAL GERAL") == "hospital"
    assert classify_unit_type("UNIDADE DE PRONTO ATENDIMENTO") == "upa"
    assert classify_unit_type("CENTRO DE SAUDE/UNIDADE BASICA") == "ubs"
    assert classify_unit_type("POSTO DE SAUDE") == "ubs"
    assert classify_unit_type("TIPO DESCONHECIDO") == "emergency"


def test_cnes_mapping():
    adapter = CNESAdapter()
    record = {
        "codigo_cnes": 1234567,
        "nome_fantasia": "UBS TESTE",
        "nome_razao_social": "PREFEITURA TESTE",
        "codigo_tipo_unidade": 2,
        "endereco_estabelecimento": "RUA TESTE",
        "numero_estabelecimento": "10",
        "bairro_estabelecimento": "CENTRO",
        "codigo_cep_estabelecimento": "01001000",
        "latitude_estabelecimento_decimo_grau": -23.55,
        "longitude_estabelecimento_decimo_grau": -46.63,
        "numero_telefone_estabelecimento": "1133334444",
        "codigo_municipio": 3550308,
    }
    mapped = adapter.map_record(record, {"2": "CENTRO DE SAUDE/UNIDADE BASICA"})
    assert mapped["source"] == "cnes"
    assert mapped["external_id"] == "1234567"
    assert mapped["cnes_code"] == "1234567"
    assert mapped["type_code"] == "2"
    assert mapped["latitude"] == -23.55
    assert classify_unit_type(mapped["type_name"]) == "ubs"


def test_datasus_mapping():
    adapter = DatasusHospitaisLeitosAdapter()
    record = {
        "nome_do_hospital": "HOSPITAL TESTE",
        "enderco_do_hospital": "RUA X",
        "numero_do_endereco_do_hospital": "1",
        "nome_do_bairro_do_endereco_do_hosptial": "CENTRO",
        "numero_do_cep_do_hospital": "01001000",
        "nome_do_municipio_onde_fica_o_hospital": "São Paulo",
        "unidade_da_federacao_onde_fica_o_hospital": "SP",
        "quantidade_total_de_leitos_do_hosptial": 120.0,
        "quantidade_total_de_leitos_sus_do_hosptial": 100.0,
        "codigo_do_tipo_da_unidade": "05",
        "descricao_do_tipo_da_unidade": "HOSPITAL GERAL",
    }
    mapped = adapter.map_record(record)
    assert mapped["source"] == "datasus_leitos"
    assert mapped["beds_total"] == 120
    assert mapped["beds_sus"] == 100
    assert mapped["state"] == "SP"
    assert mapped["external_id"]


def test_ibge_mapping(monkeypatch):
    adapter = IbgeAdapter()

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return [
                {
                    "id": 3550308,
                    "nome": "São Paulo",
                    "microrregiao": {
                        "nome": "São Paulo",
                        "mesorregiao": {
                            "nome": "Metropolitana de São Paulo",
                            "UF": {"sigla": "SP", "regiao": {"nome": "Sudeste"}},
                        },
                    },
                }
            ]

    class FakeClient:
        def get(self, url, params=None):
            return FakeResponse()

    adapter.client = FakeClient()
    adapter.limiter = type("L", (), {"wait": lambda self: None})()
    result = adapter.fetch_municipios("SP")
    assert result[0]["nome"] == "São Paulo"
    assert result[0]["uf"] == "SP"
    assert result[0]["regiao"] == "Sudeste"


def test_viacep_invalid_cep():
    import pytest

    from app.integrations.adapters import IntegrationError, ViaCepAdapter

    with pytest.raises(IntegrationError):
        ViaCepAdapter().fetch("123")
