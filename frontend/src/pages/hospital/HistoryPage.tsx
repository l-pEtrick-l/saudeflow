import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import type { Alert, Paginated } from "../../lib/types";
import { ALERT_STATUS, formatDateTime } from "../../lib/format";
import { Badge, Card, EmptyState, Loading, PageHeader, Select, Table } from "../../components/ui";

export default function HospitalHistory() {
  const [status, setStatus] = useState("");

  const { data, isLoading } = useQuery<Paginated<Alert>>({
    queryKey: ["hospital-history", status],
    queryFn: () =>
      api.get(`/api/v1/alerts?page=1&page_size=100${status ? `&status=${status}` : ""}`),
    refetchInterval: 10000,
  });

  const items = data?.data ?? [];

  return (
    <div>
      <PageHeader
        title="Histórico de ocorrências"
        subtitle="Registro administrativo dos pré-alertas recebidos"
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
        <EmptyState title="Sem ocorrências" />
      ) : (
        <Table>
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Código</th>
              <th className="px-4 py-3">Registrada em</th>
              <th className="px-4 py-3">Relato</th>
              <th className="px-4 py-3">Consciente</th>
              <th className="px-4 py-3">Respiração</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((alert) => (
              <tr key={alert.id}>
                <td className="px-4 py-3 font-semibold text-brand-700">{alert.alert_code}</td>
                <td className="px-4 py-3 text-slate-500">{formatDateTime(alert.created_at)}</td>
                <td className="max-w-sm px-4 py-3 text-sm">{alert.description || "—"}</td>
                <td className="px-4 py-3">{alert.patient_conscious}</td>
                <td className="px-4 py-3">{alert.patient_breathing}</td>
                <td className="px-4 py-3">
                  <Badge className={ALERT_STATUS[alert.status]?.tone}>{alert.status_label}</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </div>
  );
}
