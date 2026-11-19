"""Adaptadores de integração externa.

Cada adaptador conhece um endpoint e converte o payload para o formato interno.
Nenhuma chamada externa é feita a cada requisição do usuário: os dados ficam em
cache no PostgreSQL (tabelas external_units / integration_settings).
"""

import hashlib
import time
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings


class IntegrationError(Exception):
    def __init__(self, source: str, message: str, status_code: Optional[int] = None):
        self.source = source
        self.status_code = status_code
        super().__init__(f"[{source}] {message}")


class RateLimiter:
    """Token bucket simples por adaptador (respeita limites das APIs)."""

    def __init__(self, rpm: int):
        self.min_interval = 60.0 / max(rpm, 1)
        self._last = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        wait = self.min_interval - (now - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()


class BaseAdapter:
    code = "base"
    rpm = 60

    def __init__(self, client: Optional[httpx.Client] = None):
        self.client = client or httpx.Client(timeout=20.0, follow_redirects=True)
        self.limiter = RateLimiter(self.rpm)

    def _get(self, url: str, params: Optional[dict] = None) -> Any:
        self.limiter.wait()
        try:
            response = self.client.get(url, params=params or {})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise IntegrationError(
                self.code, f"HTTP {exc.response.status_code}", exc.response.status_code
            )
        except httpx.HTTPError as exc:
            raise IntegrationError(self.code, f"Falha de rede: {exc}")

    def fetch(self, **params) -> List[Dict[str, Any]]:
        raise NotImplementedError


def classify_unit_type(type_name: str) -> str:
    """Classificação conservadora do tipo de unidade a partir do nome oficial."""
    from app.utils import normalize_text

    name = normalize_text(type_name or "")
    if any(k in name for k in ["hospital", "maternidade", "pronto-socorro", "pronto socorro"]):
        return "hospital"
    if any(k in name for k in ["upa", "unidade de pronto atendimento", "pronto atendimento", "atendimento de urgencia", "urgencia"]):
        return "upa"
    if any(
        k in name
        for k in [
            "basica",
            "posto de saude",
            "centro de saude",
            "ubs",
            "consultorio",
            "clinica",
            "ambulator",
            "saude da familia",
        ]
    ):
        return "ubs"
    return "emergency"


class CNESAdapter(BaseAdapter):
    code = "cnes"
    rpm = 60

    # códigos IBGE das UF (a API do CNES espera o código numérico, não a sigla)
    UF_IBGE = {
        "RO": 11, "AC": 12, "AM": 13, "RR": 14, "PA": 15, "AP": 16, "TO": 17,
        "MA": 21, "PI": 22, "CE": 23, "RN": 24, "PB": 25, "PE": 26, "AL": 27,
        "SE": 28, "BA": 29, "MG": 31, "ES": 32, "RJ": 33, "SP": 35, "PR": 41,
        "SC": 42, "RS": 43, "MS": 50, "MT": 51, "GO": 52, "DF": 53,
    }

    def __init__(self, client: Optional[httpx.Client] = None):
        super().__init__(client)
        self.base_url = settings.CNES_BASE_URL

    def _uf_code(self, uf: str) -> Optional[int]:
        if not uf:
            return None
        digits = "".join(c for c in uf if c.isdigit())
        if digits:
            return int(digits)
        return self.UF_IBGE.get(uf.upper())

    def fetch_unit_types(self) -> Dict[str, str]:
        data = self._get(f"{self.base_url}/cnes/tipounidades", {"limit": 200})
        items = data.get("tipos_unidade", []) if isinstance(data, dict) else data
        return {
            str(item.get("codigo_tipo_unidade")): item.get("descricao_tipo_unidade", "")
            for item in items
        }

    def fetch(
        self,
        uf: Optional[str] = None,
        municipio_ibge: Optional[int] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        page_size = 20  # máximo aceito pela API
        fetched = 0
        while fetched < limit:
            params = {"limit": min(page_size, limit - fetched), "offset": offset + fetched}
            uf_code = self._uf_code(uf) if uf else None
            if uf_code:
                params["codigo_uf"] = uf_code
            if municipio_ibge:
                params["codigo_municipio"] = municipio_ibge
            data = self._get(f"{self.base_url}/cnes/estabelecimentos", params)
            items = data.get("estabelecimentos", []) if isinstance(data, dict) else []
            if not items:
                break
            results.extend(items)
            fetched += len(items)
            if len(items) < page_size:
                break
        return results

    def map_record(
        self, record: Dict[str, Any], unit_types: Dict[str, str]
    ) -> Dict[str, Any]:
        type_code = str(record.get("codigo_tipo_unidade") or "")
        type_name = unit_types.get(type_code, record.get("descricao_tipo_unidade", ""))
        name = record.get("nome_fantasia") or record.get("nome_razao_social") or "Estabelecimento sem nome"
        return {
            "source": "cnes",
            "external_id": str(
                record.get("codigo_cnes")
                or record.get("codigo_estabelecimento_saude")
                or hashlib.sha1(name.encode()).hexdigest()[:12]
            ),
            "source_data": record,
            "name": name,
            "type_code": type_code,
            "type_name": type_name,
            "street": record.get("endereco_estabelecimento"),
            "number": record.get("numero_estabelecimento"),
            "neighborhood": record.get("bairro_estabelecimento"),
            "postal_code": record.get("codigo_cep_estabelecimento"),
            "latitude": record.get("latitude_estabelecimento_decimo_grau"),
            "longitude": record.get("longitude_estabelecimento_decimo_grau"),
            "phone": record.get("numero_telefone_estabelecimento"),
            "cnes_code": str(record.get("codigo_cnes") or "") or None,
            "ibge_code": str(record.get("codigo_municipio") or "") or None,
        }


class DatasusHospitaisLeitosAdapter(BaseAdapter):
    code = "datasus_leitos"
    rpm = 60

    def __init__(self, client: Optional[httpx.Client] = None):
        super().__init__(client)
        self.base_url = settings.DATASUS_BASE_URL

    def fetch(
        self, uf: Optional[str] = None, limit: int = 200, offset: int = 0
    ) -> List[Dict[str, Any]]:
        params = {"limit": min(limit, 1000), "offset": offset}
        if uf:
            params["uf"] = uf
        data = self._get(f"{self.base_url}/assistencia-a-saude/hospitais-e-leitos", params)
        items = data.get("hospitais_leitos", []) if isinstance(data, dict) else []
        return items

    def map_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        name = record.get("nome_do_hospital") or "Hospital sem nome"
        cep = record.get("numero_do_cep_do_hospital") or ""
        cidade = record.get("nome_do_municipio_onde_fica_o_hospital") or ""
        external_id = hashlib.sha1(
            f"{name}|{cep}|{cidade}".encode()
        ).hexdigest()[:16]
        return {
            "source": "datasus_leitos",
            "external_id": external_id,
            "source_data": record,
            "name": name,
            "type_code": str(record.get("codigo_do_tipo_da_unidade") or ""),
            "type_name": record.get("descricao_do_tipo_da_unidade") or "Hospital",
            "street": record.get("enderco_do_hospital"),
            "number": record.get("numero_do_endereco_do_hospital"),
            "neighborhood": record.get("nome_do_bairro_do_endereco_do_hosptial"),
            "city": cidade,
            "state": record.get("unidade_da_federacao_onde_fica_o_hospital"),
            "postal_code": cep,
            "beds_total": _to_int(record.get("quantidade_total_de_leitos_do_hosptial")),
            "beds_sus": _to_int(record.get("quantidade_total_de_leitos_sus_do_hosptial")),
        }


class IbgeAdapter(BaseAdapter):
    code = "ibge"
    rpm = 120

    def __init__(self, client: Optional[httpx.Client] = None):
        super().__init__(client)
        self.base_url = settings.IBGE_BASE_URL

    def fetch_municipios(self, uf: str) -> List[Dict[str, Any]]:
        data = self._get(f"{self.base_url}/localidades/estados/{uf.upper()}/municipios")
        result = []
        for item in data if isinstance(data, list) else []:
            micro = (item.get("microrregiao") or {}).get("nome")
            meso = ((item.get("microrregiao") or {}).get("mesorregiao") or {}).get("nome")
            uf_info = ((item.get("microrregiao") or {}).get("mesorregiao") or {}).get("UF") or {}
            regiao = (uf_info.get("regiao") or {}).get("nome")
            result.append(
                {
                    "id": item.get("id"),
                    "nome": item.get("nome"),
                    "microrregiao": micro,
                    "mesorregiao": meso,
                    "uf": uf_info.get("sigla") or uf.upper(),
                    "regiao": regiao,
                }
            )
        return result


class ViaCepAdapter(BaseAdapter):
    code = "viacep"
    rpm = 60

    def __init__(self, client: Optional[httpx.Client] = None):
        super().__init__(client)
        self.base_url = settings.VIACEP_BASE_URL

    def fetch(self, cep: str) -> Dict[str, Any]:
        digits = "".join(c for c in cep if c.isdigit())
        if len(digits) != 8:
            raise IntegrationError(self.code, "CEP inválido")
        data = self._get(f"{self.base_url}/{digits}/json/")
        if data.get("erro"):
            raise IntegrationError(self.code, "CEP não encontrado")
        return data


class OsrmAdapter(BaseAdapter):
    code = "osrm"
    rpm = 120

    def __init__(self, client: Optional[httpx.Client] = None):
        super().__init__(client)
        self.base_url = settings.OSRM_BASE_URL

    def fetch(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> Dict[str, Any]:
        coords = f"{lon1},{lat1};{lon2},{lat2}"
        data = self._get(f"{self.base_url}/route/v1/driving/{coords}", {"overview": "false"})
        routes = data.get("routes") or []
        if not routes:
            raise IntegrationError(self.code, "Rota não encontrada")
        route = routes[0]
        return {
            "distance_km": round(route.get("distance", 0) / 1000.0, 2),
            "duration_minutes": round(route.get("duration", 0) / 60.0, 1),
        }


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(float(value)) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None
