import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Building2,
  CheckCircle2,
  Clock,
  Loader2,
  MapPin,
  PhoneCall,
  ShieldAlert,
} from "lucide-react";
import { api } from "../../lib/api";
import type { GuidanceResult, Paginated, Unit } from "../../lib/types";
import { estimateText } from "../../lib/format";
import { Alert, Badge, Button, Card, Loading } from "../../components/ui";

export default function ResultPage() {
  const { submissionId } = useParams<{ submissionId: string }>();
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState("");

  const result = useQuery<GuidanceResult>({
    queryKey: ["guidance", submissionId],
    queryFn: () => api.get(`/api/v1/questionnaires/submissions/${submissionId}/result`),
    enabled: !!submissionId,
  });

  const units = useQuery<Paginated<Unit>>({
    queryKey: ["units-for-guidance", result.data?.recommended_unit_types],
    queryFn: () => {
      const types = result.data?.recommended_unit_types ?? ["upa"];
      const params = new URLSearchParams({ page: "1", page_size: "50" });
      params.set("type", types[0]);
      return api.get(`/api/v1/units?${params.toString()}`);
    },
    enabled: !!result.data && !result.data.stop_flow,
  });

  const createRequest = useMutation({
    mutationFn: (unitId: string) =>
      api.post<{ protocol: string }>("/api/v1/requests", {
        submission_id: submissionId,
        unit_id: unitId,
        patient_name: "Paciente SaúdeFlow",
        patient_phone: "",
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["requests"] });
      window.location.href = `/paciente/protocolo/${data.protocol}`;
    },
    onError: (err: Error) => setError(err.message),
  });

  const unitList = useMemo(() => units.data?.data ?? [], [units.data]);

  if (result.isLoading) return <Loading label="Gerando orientação..." />;
  if (result.error) {
    return (
      <div className="mx-auto max-w-xl px-4 py-16">
        <Alert variant="danger">Não foi possível carregar a orientação.</Alert>
      </div>
    );
  }
  const guidance = result.data!;

  if (guidance.stop_flow) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-10">
        <div className="rounded-3xl bg-gradient-to-br from-red-600 to-red-700 p-8 text-white">
          <ShieldAlert className="h-10 w-10" />
          <h1 className="mt-4 text-3xl font-extrabold">Procure socorro imediato</h1>
          <p className="mt-3 text-white/90">{guidance.emergency_message}</p>
          <a
            href="tel:192"
            className="mt-6 flex items-center justify-center gap-3 rounded-2xl bg-white px-6 py-5 text-2xl font-extrabold text-red-700"
          >
            <PhoneCall className="h-7 w-7" /> Ligar SAMU 192
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div
        className={`rounded-3xl p-6 text-white ${
          guidance.category === "A"
            ? "bg-gradient-to-br from-mint-600 to-mint-700"
            : guidance.category === "B"
            ? "bg-gradient-to-br from-brand-600 to-brand-700"
            : "bg-gradient-to-br from-violet-600 to-violet-700"
        }`}
      >
        <Badge className="bg-white/15 text-white">Categoria {guidance.category}</Badge>
        <h1 className="mt-3 text-3xl font-extrabold">{guidance.category_label}</h1>
        <p className="mt-2 text-white/90">{guidance.service_label}</p>
      </div>

      <Card className="mt-6">
        <h2 className="font-semibold text-slate-900">O que consideramos</h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">{guidance.justification}</p>
        <div className="mt-4 flex flex-wrap gap-2">
          {guidance.alert_flags.map((flag) => (
            <Badge key={flag} className="bg-amber-50 text-amber-700">
              {flag}
            </Badge>
          ))}
        </div>
        <div className="mt-4 grid gap-2 text-xs text-slate-500 sm:grid-cols-3">
          <p>
            Confiança operacional: <strong>{Math.round(guidance.confidence * 100)}%</strong>
          </p>
          <p>
            Avaliação profissional:{" "}
            <strong>{guidance.needs_professional ? "necessária" : "não obrigatória"}</strong>
          </p>
          <p>
            Versão das regras: <strong>{guidance.rule_set_version}</strong>
          </p>
        </div>
        {guidance.matched_rule_name && (
          <p className="mt-2 text-xs text-slate-400">Regra aplicada: {guidance.matched_rule_name}</p>
        )}
      </Card>

      <Alert variant="warning" className="mt-6">
        Esta orientação é auxiliar e conservadora. A prioridade do atendimento é definida por
        profissionais de saúde. O protocolo digital não garante horário nem prioridade clínica.
      </Alert>

      {unitList.length > 0 && (
        <>
          <h2 className="mt-8 text-xl font-bold text-slate-900">Unidades compatíveis</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {unitList.map((unit) => (
              <Card
                key={unit.id}
                className={selected === unit.id ? "ring-2 ring-brand-400" : ""}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-semibold text-slate-900">{unit.name}</p>
                    <p className="mt-1 flex items-center gap-1 text-xs text-slate-500">
                      <MapPin className="h-3.5 w-3.5" /> {unit.neighborhood || "—"}, {unit.city}
                      {unit.distance_km != null && ` · ${unit.distance_km} km`}
                    </p>
                  </div>
                  {unit.is_simulated && <Badge className="bg-slate-100 text-slate-500">Simulada</Badge>}
                </div>
                <p className="mt-3 flex items-center gap-2 text-sm">
                  <Clock className="h-4 w-4 text-slate-400" />
                  <span
                    className={
                      unit.estimate?.is_reliable ? "font-medium text-mint-700" : "text-amber-700"
                    }
                  >
                    {estimateText(unit.estimate)}
                  </span>
                </p>
                <div className="mt-4 flex gap-2">
                  <Button
                    variant={selected === unit.id ? "primary" : "secondary"}
                    onClick={() => setSelected(unit.id)}
                  >
                    {selected === unit.id ? "Selecionada" : "Selecionar"}
                  </Button>
                </div>
              </Card>
            ))}
          </div>

          <div className="sticky bottom-4 mt-6">
            <Button
              size="lg"
              className="w-full shadow-lg"
              disabled={!selected || createRequest.isPending}
              onClick={() => selected && createRequest.mutate(selected)}
            >
              {createRequest.isPending ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <CheckCircle2 className="h-5 w-5" />
              )}
              Gerar protocolo na unidade selecionada
            </Button>
            {error && <p className="mt-2 text-center text-sm text-red-600">{error}</p>}
          </div>
        </>
      )}

      <div className="mt-6 text-center">
        <Link to="/" className="text-sm text-slate-500 underline">
          Voltar ao início
        </Link>
      </div>
    </div>
  );
}
