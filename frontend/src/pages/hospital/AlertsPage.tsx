import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Ambulance, Bell, CheckCircle2 } from "lucide-react";
import { api } from "../../lib/api";
import type { Alert, Paginated } from "../../lib/types";
import { ALERT_STATUS, formatDateTime } from "../../lib/format";
import { Badge, Button, Card, EmptyState, Loading, PageHeader, Select, Table } from "../../components/ui";

export default function HospitalAlerts() {
  const [status, setStatus] = useState("");
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery<Paginated<Alert>>({
    queryKey: ["hospital-alerts", status],
    queryFn: () =>
      api.get(`/api/v1/alerts?page=1&page_size=50${status ? `&status=${status}` : ""}`),
    refetchInterval: 5000,
  });

  const update = useMutation({
    mutationFn: ({ id, value }: { id: string; value: string }) =>
      api.patch(`/api/v1/alerts/${id}`, { status: value }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["hospital-alerts"] }),
  });

  const items = data?.data ?? [];

  return (
    <div>
      <PageHeader
        title="Pré-alertas"
        subtitle="Pacientes que informaram estar a caminho deste hospital"
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
        <EmptyState title="Nenhum pré-alerta" />
      ) : (
        <Table>
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Código</th>
              <th className="px-4 py-3">Horário</th>
              <th className="px-4 py-3">Relato</th>
              <th className="px-4 py-3">Sinais</th>
              <th className="px-4 py-3">Previsão</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((alert) => (
              <tr key={alert.id}>
                <td className="px-4 py-3 font-semibold text-brand-700">{alert.alert_code}</td>
                <td className="px-4 py-3 text-slate-500">{formatDateTime(alert.created_at)}</td>
                <td className="max-w-xs px-4 py-3">
                  <p className="line-clamp-2 text-sm">{alert.description || "—"}</p>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {alert.alert_flags.map((flag) => (
                      <Badge key={flag} className="bg-amber-50 text-amber-700">
                        {flag}
                      </Badge>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3 text-slate-500">
                  {alert.eta_minutes != null ? `${alert.eta_minutes} min` : "—"}
                </td>
                <td className="px-4 py-3">
                  <Badge className={ALERT_STATUS[alert.status]?.tone}>{alert.status_label}</Badge>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap justify-end gap-1.5">
                    {["new", "received"].includes(alert.status) && (
                      <Button size="sm" onClick={() => update.mutate({ id: alert.id, value: "confirmed" })}>
                        <CheckCircle2 className="h-3.5 w-3.5" /> Confirmar
                      </Button>
                    )}
                    {alert.status === "confirmed" && (
                      <Button variant="success" size="sm" onClick={() => update.mutate({ id: alert.id, value: "arrived" })}>
                        <Ambulance className="h-3.5 w-3.5" /> Chegada
                      </Button>
                    )}
                    {["confirmed", "arrived"].includes(alert.status) && (
                      <Button variant="ghost" size="sm" onClick={() => update.mutate({ id: alert.id, value: "closed" })}>
                        Encerrar
                      </Button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
      <p className="mt-4 flex items-center gap-2 text-xs text-slate-400">
        <Bell className="h-3.5 w-3.5" /> As informações do pré-alerta não foram verificadas clinicamente.
      </p>
    </div>
  );
}
