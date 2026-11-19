import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Ambulance, CheckCircle2, Loader2, PhoneCall, Siren } from "lucide-react";
import { api } from "../../lib/api";
import type { Alert, Paginated, Unit } from "../../lib/types";
import { Alert as AlertBox, Badge, Button, Card, Input, Label, Select, Textarea } from "../../components/ui";

export default function PreAlertPage() {
  const queryClient = useQueryClient();
  const [unitId, setUnitId] = useState("");
  const [description, setDescription] = useState("");
  const [conscious, setConscious] = useState("unknown");
  const [breathing, setBreathing] = useState("unknown");
  const [bleeding, setBleeding] = useState("unknown");
  const [situation, setSituation] = useState("");
  const [eta, setEta] = useState("");
  const [error, setError] = useState("");

  const units = useQuery<Paginated<Unit>>({
    queryKey: ["units", "hospital-emergency"],
    queryFn: () => {
      const params = new URLSearchParams({ page: "1", page_size: "50", type: "hospital" });
      return api.get(`/api/v1/units?${params.toString()}`);
    },
  });

  const hospitals = (units.data?.data ?? []).filter((u) => u.type === "hospital" || u.type === "emergency");

  const mutation = useMutation({
    mutationFn: () =>
      api.post<Alert>("/api/v1/alerts", {
        destination_unit_id: unitId,
        description,
        patient_conscious: conscious,
        patient_breathing: breathing,
        bleeding,
        current_situation: situation || undefined,
        eta_minutes: eta ? Number(eta) : undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
    onError: (err: Error) => setError(err.message),
  });

  const created: Alert | null = mutation.data ?? null;

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="rounded-2xl bg-gradient-to-br from-red-600 to-red-700 p-5 text-white">
        <div className="flex items-center gap-3">
          <Siren className="h-7 w-7" />
          <div>
            <h1 className="text-xl font-bold">Pré-alerta de paciente a caminho</h1>
            <p className="text-sm text-white/85">
              Envie informações preliminares para a unidade. Não substitui o SAMU 192.
            </p>
          </div>
        </div>
        <a
          href="tel:192"
          className="mt-4 flex items-center justify-center gap-2 rounded-xl bg-white px-4 py-3 font-extrabold text-red-700"
        >
          <PhoneCall className="h-5 w-5" /> SAMU 192
        </a>
      </div>

      {created ? (
        <Card className="mt-6">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-8 w-8 text-mint-600" />
            <div>
              <h2 className="text-lg font-bold text-slate-900">Pré-alerta enviado</h2>
              <p className="text-sm text-slate-500">
                Código <strong>{created.alert_code}</strong> para {created.destination_unit_name}
              </p>
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {created.alert_flags.map((flag) => (
              <Badge key={flag} className="bg-amber-50 text-amber-700">
                {flag}
              </Badge>
            ))}
          </div>
          <p className="mt-4 text-sm text-slate-600">
            Status: <strong>{created.status_label}</strong>. A unidade pode confirmar o recebimento.
            Continue seguindo as orientações de emergência.
          </p>
          <div className="mt-5 flex gap-2">
            <Link to="/" className="btn-secondary">
              Voltar ao início
            </Link>
            <Button
              variant="secondary"
              onClick={() => {
                mutation.reset();
                setUnitId("");
                setDescription("");
                setConscious("unknown");
                setBreathing("unknown");
                setBleeding("unknown");
                setSituation("");
                setEta("");
              }}
            >
              Enviar outro pré-alerta
            </Button>
          </div>
        </Card>
      ) : (
        <Card className="mt-6">
          <div className="space-y-4">
            <div>
              <Label htmlFor="unit">Unidade de destino</Label>
              <Select id="unit" value={unitId} onChange={(e) => setUnitId(e.target.value)} required>
                <option value="">Selecione...</option>
                {hospitals.map((unit) => (
                  <option key={unit.id} value={unit.id}>
                    {unit.name} — {unit.city}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label htmlFor="description">O que aconteceu?</Label>
              <Textarea
                id="description"
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Descreva brevemente, sem dados pessoais"
              />
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <div>
                <Label>Consciente?</Label>
                <Select value={conscious} onChange={(e) => setConscious(e.target.value)}>
                  <option value="unknown">Não sei</option>
                  <option value="yes">Sim</option>
                  <option value="no">Não</option>
                </Select>
              </div>
              <div>
                <Label>Respirando normalmente?</Label>
                <Select value={breathing} onChange={(e) => setBreathing(e.target.value)}>
                  <option value="unknown">Não sei</option>
                  <option value="yes">Sim</option>
                  <option value="no">Não</option>
                </Select>
              </div>
              <div>
                <Label>Sangramento importante?</Label>
                <Select value={bleeding} onChange={(e) => setBleeding(e.target.value)}>
                  <option value="unknown">Não sei</option>
                  <option value="yes">Sim</option>
                  <option value="no">Não</option>
                </Select>
              </div>
            </div>
            <div>
              <Label htmlFor="situation">Situação atual</Label>
              <Input
                id="situation"
                value={situation}
                onChange={(e) => setSituation(e.target.value)}
                placeholder="Ex.: estável, acompanhado, piorando..."
              />
            </div>
            <div>
              <Label htmlFor="eta">Previsão de chegada (minutos)</Label>
              <Input
                id="eta"
                type="number"
                min={0}
                value={eta}
                onChange={(e) => setEta(e.target.value)}
              />
            </div>
            {error && <AlertBox variant="danger">{error}</AlertBox>}
            <Button
              className="w-full"
              disabled={!unitId || mutation.isPending}
              onClick={() => mutation.mutate()}
            >
              {mutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Ambulance className="h-4 w-4" />
              )}
              Enviar pré-alerta
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
