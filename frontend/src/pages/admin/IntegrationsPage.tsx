import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Cloud, Database, Play, RefreshCw, Search } from "lucide-react";
import { api } from "../../lib/api";
import type { ExternalUnit, Paginated, SyncLog } from "../../lib/types";
import { formatDateTime } from "../../lib/format";
import { Alert, Badge, Button, Card, Input, Label, PageHeader, Select, Table } from "../../components/ui";

interface Source {
  id: string;
  code: string;
  name: string;
  enabled: boolean;
  rate_limit_rpm: number;
  description?: string | null;
}

const SOURCE_LABEL: Record<string, string> = {
  cnes: "CNES — Estabelecimentos (MS/DATASUS)",
  datasus_leitos: "DATASUS — Hospitais e Leitos",
  ibge: "IBGE — Localidades",
  viacep: "ViaCEP",
  osrm: "OSRM — Rotas",
};

const SYNC_LABEL: Record<string, string> = { success: "Concluída", failed: "Falhou", running: "Em andamento", pending: "Aguardando" };

export default function AdminIntegrations() {
  const queryClient = useQueryClient();
  const [source, setSource] = useState("cnes");
  const [uf, setUf] = useState("SP");
  const [limit, setLimit] = useState(200);
  const [cep, setCep] = useState("");
  const [cepResult, setCepResult] = useState<Record<string, string> | null>(null);
  const [municipios, setMunicipios] = useState<{ id: number; nome: string }[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const sources = useQuery<Source[]>({
    queryKey: ["integration-sources"],
    queryFn: () => api.get("/api/v1/integrations/sources"),
  });

  const logs = useQuery<Paginated<SyncLog>>({
    queryKey: ["sync-logs"],
    queryFn: () => api.get("/api/v1/integrations/sync-logs?page=1&page_size=20"),
    refetchInterval: 8000,
  });

  const external = useQuery<Paginated<ExternalUnit>>({
    queryKey: ["external-units"],
    queryFn: () => api.get("/api/v1/integrations/external-units?page=1&page_size=20"),
  });

  const sync = useMutation({
    mutationFn: () => api.post<SyncLog>("/api/v1/integrations/sync", { source, uf, limit }),
    onSuccess: (data) => {
      setNotice(`Atualização de ${SOURCE_LABEL[source] ?? source}: ${SYNC_LABEL[data.status] ?? data.status}. ${data.records_fetched} registros encontrados, ${data.records_inserted} adicionados e ${data.records_updated} atualizados.`);
      queryClient.invalidateQueries({ queryKey: ["sync-logs"] });
      queryClient.invalidateQueries({ queryKey: ["external-units"] });
    },
    onError: (err: Error) => setError(err.message),
  });

  const lookupCep = () => {
    if (cep.replace(/\D/g, "").length !== 8) {
      setError("Informe um CEP válido com 8 dígitos.");
      return;
    }
    api
      .get<Record<string, string>>(`/api/v1/integrations/viacep/${cep}`)
      .then(setCepResult)
      .catch((err: Error) => setError(err.message));
  };

  const lookupIbge = () => {
    api
      .get<{ id: number; nome: string }[]>(`/api/v1/integrations/ibge/municipios?uf=${uf}`)
      .then(setMunicipios)
      .catch((err: Error) => setError(err.message));
  };

  return (
    <div>
      <PageHeader
        title="Dados de outras fontes"
        subtitle="Consulte e atualize as informações de outras fontes. A data de atualização mostra quando cada informação foi buscada."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="flex items-center gap-2 font-semibold text-slate-900">
            <Cloud className="h-5 w-5 text-brand-600" /> De onde vêm os dados
          </h2>
          <ul className="mt-4 space-y-3 text-sm">
            {(sources.data ?? []).map((item) => (
              <li key={item.id} className="flex items-center justify-between rounded-xl border border-slate-100 p-3">
                <div>
                  <p className="font-medium text-slate-800">{SOURCE_LABEL[item.code] ?? item.name}</p>
                  <p className="text-xs text-slate-500">
                    Limite de {item.rate_limit_rpm} consultas por minuto
                  </p>
                </div>
                <Badge className={item.enabled ? "bg-mint-50 text-mint-700" : "bg-slate-100 text-slate-500"}>
                  {item.enabled ? "ativa" : "inativa"}
                </Badge>
              </li>
            ))}
          </ul>
        </Card>

        <Card>
          <h2 className="flex items-center gap-2 font-semibold text-slate-900">
            <RefreshCw className="h-5 w-5 text-brand-600" /> Buscar atualizações
          </h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <div>
              <Label>Fonte</Label>
              <Select value={source} onChange={(e) => setSource(e.target.value)}>
                <option value="cnes">CNES</option>
                <option value="datasus_leitos">DATASUS Hospitais e Leitos</option>
                <option value="ibge">IBGE</option>
              </Select>
            </div>
            <div>
              <Label>Estado (sigla)</Label>
              <Input value={uf} onChange={(e) => setUf(e.target.value.toUpperCase())} maxLength={2} />
            </div>
            <div>
              <Label>Máximo de registros</Label>
              <Input type="number" min={1} max={1000} value={limit} onChange={(e) => setLimit(Number(e.target.value))} />
            </div>
          </div>
          {error && <Alert variant="danger" className="mt-3">{error}</Alert>}
          {notice && <Alert variant="success" className="mt-3">{notice}</Alert>}
          <Button className="mt-4 w-full" onClick={() => sync.mutate()} disabled={sync.isPending}>
            <Play className="h-4 w-4" /> Atualizar dados
          </Button>
        </Card>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <h3 className="font-semibold text-slate-900">Buscar endereço pelo CEP</h3>
          <div className="mt-3 flex gap-2">
            <Input placeholder="01001000" value={cep} onChange={(e) => setCep(e.target.value)} />
            <Button variant="secondary" onClick={lookupCep}>
              <Search className="h-4 w-4" /> Buscar
            </Button>
          </div>
          {cepResult && (
            <div className="mt-3 rounded-xl bg-slate-50 p-3 text-sm">
              <p>{cepResult.logradouro}, {cepResult.bairro}</p>
              <p>{cepResult.localidade}/{cepResult.uf} · IBGE {cepResult.ibge}</p>
            </div>
          )}
        </Card>

        <Card>
          <h3 className="font-semibold text-slate-900">Consultar cidades por estado</h3>
          <div className="mt-3 flex gap-2">
            <Input value={uf} onChange={(e) => setUf(e.target.value.toUpperCase())} maxLength={2} />
            <Button variant="secondary" onClick={lookupIbge}>
              <Database className="h-4 w-4" /> Carregar
            </Button>
          </div>
          {municipios.length > 0 && (
            <p className="mt-3 text-sm text-slate-600">
              {municipios.length} município(s). Ex.: {municipios[0].nome}
            </p>
          )}
        </Card>
      </div>

      <Card className="mt-6">
        <h3 className="font-semibold text-slate-900">Histórico das atualizações</h3>
        <div className="mt-4">
          <Table>
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Fonte</th>
                <th className="px-4 py-3">Situação</th>
                <th className="px-4 py-3">Início</th>
                <th className="px-4 py-3">Encontrados</th>
                <th className="px-4 py-3">Adicionados</th>
                <th className="px-4 py-3">Atualizados</th>
                <th className="px-4 py-3">Erro</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {(logs.data?.data ?? []).map((log) => (
                <tr key={log.id}>
                  <td className="px-4 py-3 font-medium">{SOURCE_LABEL[log.source] ?? log.source}</td>
                  <td className="px-4 py-3">
                    <Badge className={log.status === "success" ? "bg-mint-50 text-mint-700" : log.status === "failed" ? "bg-red-50 text-red-700" : "bg-amber-50 text-amber-700"}>
                      {SYNC_LABEL[log.status] ?? log.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-slate-500">{formatDateTime(log.started_at)}</td>
                  <td className="px-4 py-3">{log.records_fetched}</td>
                  <td className="px-4 py-3">{log.records_inserted}</td>
                  <td className="px-4 py-3">{log.records_updated}</td>
                  <td className="max-w-xs px-4 py-3 text-xs text-red-600">{log.error || "—"}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      </Card>

      <Card className="mt-6">
        <h3 className="font-semibold text-slate-900">Unidades encontradas em outras fontes</h3>
        <p className="mt-1 text-xs text-slate-500">
          São cópias dos cadastros do CNES/DATASUS. A data mostra quando foram buscadas; elas não indicam vagas ou leitos livres agora.
        </p>
        <div className="mt-4">
          <Table>
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Fonte</th>
                <th className="px-4 py-3">Nome</th>
                <th className="px-4 py-3">Tipo</th>
                <th className="px-4 py-3">Município/UF</th>
                <th className="px-4 py-3">CNES</th>
                <th className="px-4 py-3">Leitos</th>
                <th className="px-4 py-3">Atualizado em</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {(external.data?.data ?? []).map((unit) => (
                <tr key={unit.id}>
                  <td className="px-4 py-3">{SOURCE_LABEL[unit.source] ?? unit.source}</td>
                  <td className="max-w-xs px-4 py-3 font-medium">{unit.name || "—"}</td>
                  <td className="px-4 py-3 text-slate-500">{unit.type_name || "—"}</td>
                  <td className="px-4 py-3 text-slate-500">
                    {unit.city || "—"}/{unit.state || ""}
                  </td>
                  <td className="px-4 py-3 text-slate-500">{unit.cnes_code || "—"}</td>
                  <td className="px-4 py-3">{unit.beds_total ?? "—"}</td>
                  <td className="px-4 py-3 text-slate-500">{formatDateTime(unit.fetched_at)}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      </Card>
    </div>
  );
}
