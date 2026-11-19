import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Building2, Clock, MapPin, Phone, Search } from "lucide-react";
import { api } from "../../lib/api";
import type { Paginated, Unit } from "../../lib/types";
import { estimateText } from "../../lib/format";
import { Badge, Button, Card, Input, Loading, Select } from "../../components/ui";
import { UnitMap } from "../../components/UnitMap";

const TYPE_LABEL: Record<string, string> = {
  all: "Todas",
  ubs: "UBS",
  upa: "UPA",
  hospital: "Hospital",
  emergency: "Pronto-socorro",
};

export default function UnitsPage() {
  const [type, setType] = useState("all");
  const [q, setQ] = useState("");
  const [city, setCity] = useState("");

  const { data, isLoading } = useQuery<Paginated<Unit>>({
    queryKey: ["units", type, q, city],
    queryFn: () => {
      const params = new URLSearchParams({ page: "1", page_size: "50" });
      if (type !== "all") params.set("type", type);
      if (q) params.set("q", q);
      if (city) params.set("city", city);
      return api.get(`/api/v1/units?${params.toString()}`);
    },
  });

  const units = useMemo(() => data?.data ?? [], [data]);

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Unidades de saúde</h1>
          <p className="mt-1 text-sm text-slate-500">
            Unidades cadastradas no ambiente de demonstração. Distância em linha reta, quando disponível.
          </p>
        </div>
        <Badge className="bg-brand-50 text-brand-700">
          {units.length} unidade(s)
        </Badge>
      </div>

      <Card className="mt-6">
        <div className="grid gap-3 sm:grid-cols-4">
          <div>
            <label className="label">Tipo</label>
            <Select value={type} onChange={(e) => setType(e.target.value)}>
              {Object.entries(TYPE_LABEL).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <label className="label">Buscar</label>
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
              <Input className="pl-9" placeholder="Nome da unidade" value={q} onChange={(e) => setQ(e.target.value)} />
            </div>
          </div>
          <div>
            <label className="label">Cidade</label>
            <Input placeholder="São Paulo" value={city} onChange={(e) => setCity(e.target.value)} />
          </div>
          <div className="flex items-end">
            <Link to="/atendimento" className="btn-primary w-full">
              Quero atendimento
            </Link>
          </div>
        </div>
      </Card>

      {isLoading ? (
        <Loading />
      ) : (
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <div className="space-y-4">
            {units.map((unit) => (
              <Card key={unit.id}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
                        <Building2 className="h-5 w-5" />
                      </span>
                      <div>
                        <p className="font-semibold text-slate-900">{unit.name}</p>
                        <p className="text-xs text-slate-500">
                          {TYPE_LABEL[unit.type]} · {unit.neighborhood || "—"}, {unit.city}
                        </p>
                      </div>
                    </div>
                  </div>
                  {unit.is_simulated && <Badge className="bg-slate-100 text-slate-600">Simulada</Badge>}
                </div>

                <div className="mt-4 grid gap-2 text-sm text-slate-600 sm:grid-cols-2">
                  <p className="flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-slate-400" />
                    {unit.street || "Endereço não informado"}
                    {unit.number ? `, ${unit.number}` : ""}
                  </p>
                  {unit.phone && (
                    <p className="flex items-center gap-2">
                      <Phone className="h-4 w-4 text-slate-400" /> {unit.phone}
                    </p>
                  )}
                  <p className="flex items-center gap-2 sm:col-span-2">
                    <Clock className="h-4 w-4 text-slate-400" />
                    <span
                      className={
                        unit.estimate?.is_reliable ? "font-medium text-mint-700" : "text-amber-700"
                      }
                    >
                      {estimateText(unit.estimate)}
                    </span>
                    {unit.digital_queue_count != null && unit.digital_queue_count > 0 && (
                      <Badge className="bg-brand-50 text-brand-700">
                        {unit.digital_queue_count} na fila digital
                      </Badge>
                    )}
                  </p>
                </div>

                {unit.services.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {unit.services.map((service) => (
                      <Badge key={service.id} className="bg-slate-50 text-slate-600">
                        {service.service_name}
                      </Badge>
                    ))}
                  </div>
                )}

                <div className="mt-4 flex gap-2">
                  {(unit.type === "upa" || unit.type === "hospital" || unit.type === "emergency") && (
                    <Link to={`/atendimento?unit=${unit.id}`} className="btn-primary btn-sm">
                      Solicitar atendimento
                    </Link>
                  )}
                  {unit.source === "cnes" && <Badge className="bg-mint-50 text-mint-700">CNES</Badge>}
                </div>
              </Card>
            ))}
          </div>
          <div className="lg:sticky lg:top-20 lg:self-start">
            <UnitMap units={units} height={560} />
            <p className="mt-2 text-xs text-slate-500">
              Mapa com OpenStreetMap/Leaflet. Marcadores de demonstração.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
