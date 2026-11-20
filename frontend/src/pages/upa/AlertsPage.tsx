import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCircle2, Clock, MapPin } from "lucide-react";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import type { Alert, Paginated } from "../../lib/types";
import { SIGNAL_LABEL, YES_NO_LABEL, ALERT_STATUS, formatDateTime } from "../../lib/format";
import { Badge, Button, Card, EmptyState, Loading, PageHeader, Select, Table } from "../../components/ui";

export default function UpaAlerts() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState("");

  const { data, isLoading } = useQuery<Paginated<Alert>>({
    queryKey: ["unit-alerts", status],
    queryFn: () =>
      api.get(`/api/v1/alerts?page=1&page_size=50${status ? `&status=${status}` : ""}`),
    refetchInterval: 6000,
  });

  const update = useMutation({
    mutationFn: ({ id, value }: { id: string; value: string }) =>
      api.patch(`/api/v1/alerts/${id}`, { status: value }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["unit-alerts"] }),
  });

  const items = data?.data ?? [];

  return (
    <div>
      <PageHeader
        title="Avisos de chegada recebidos"
        subtitle="Leia os avisos de quem está a caminho. Confirme o recebimento e registre quando a pessoa chegar."
        actions={
          <Select value={status} onChange={(e) => setStatus(e.target.value)} className="w-52">
            <option value="">Todos</option>
            {Object.entries(ALERT_STATUS).map(([value, item]) => (
              <option key={value} value={value}>
                {item.label}
              </option>
            ))}
          </Select>
        }
      />

      {isLoading ? (
        <Loading />
      ) : items.length === 0 ? (
        <EmptyState title="Nenhum aviso de chegada" description="Avisos de chegada de pacientes a caminho aparecerão aqui." />
      ) : (
        <div className="space-y-4">
          {items.map((alert) => (
            <Card key={alert.id}>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <Bell className="h-5 w-5 text-red-500" />
                    <p className="font-semibold text-slate-900">{alert.alert_code}</p>
                    <Badge className={ALERT_STATUS[alert.status]?.tone}>{alert.status_label}</Badge>
                  </div>
                  {alert.description && (
                    <p className="mt-2 text-sm text-slate-600">{alert.description}</p>
                  )}
                  <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5" /> {formatDateTime(alert.created_at)}
                    </span>
                    {alert.eta_minutes != null && (
                      <span className="flex items-center gap-1">
                        <MapPin className="h-3.5 w-3.5" /> previsão: {alert.eta_minutes} min
                      </span>
                    )}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {alert.alert_flags.map((flag) => (
                      <Badge key={SIGNAL_LABEL[flag] ?? flag} className="bg-amber-50 text-amber-700">
                        {SIGNAL_LABEL[flag] ?? flag}
                      </Badge>
                    ))}
                  </div>
                  <p className="mt-2 text-xs text-slate-400">
                    Consciente: {YES_NO_LABEL[alert.patient_conscious] ?? "Não informado"} · Respirando: {YES_NO_LABEL[alert.patient_breathing] ?? "Não informado"} ·
                    Sangramento: {YES_NO_LABEL[alert.bleeding] ?? "Não informado"}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {alert.status === "new" && (
                    <Button variant="secondary" size="sm" onClick={() => update.mutate({ id: alert.id, value: "received" })}>
                      Marcar recebido
                    </Button>
                  )}
                  {["new", "received"].includes(alert.status) && (
                    <Button size="sm" onClick={() => update.mutate({ id: alert.id, value: "confirmed" })}>
                      <CheckCircle2 className="h-4 w-4" /> Confirmar leitura
                    </Button>
                  )}
                  {alert.status === "confirmed" && (
                    <Button variant="success" size="sm" onClick={() => update.mutate({ id: alert.id, value: "arrived" })}>
                      Registrar chegada
                    </Button>
                  )}
                  {["confirmed", "arrived"].includes(alert.status) && (
                    <Button variant="ghost" size="sm" onClick={() => update.mutate({ id: alert.id, value: "closed" })}>
                      Encerrar
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
      <p className="mt-4 text-xs text-slate-400">
        Confirmar significa apenas que a equipe recebeu o aviso. Não reserva leito nem garante atendimento.
      </p>
    </div>
  );
}
