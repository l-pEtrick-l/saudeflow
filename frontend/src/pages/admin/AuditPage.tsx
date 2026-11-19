import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Shield } from "lucide-react";
import { api } from "../../lib/api";
import type { Paginated } from "../../lib/types";
import { formatDateTime } from "../../lib/format";
import { Input, Label, PageHeader, Table } from "../../components/ui";

interface AuditItem {
  id: string;
  actor_user_id?: string | null;
  action: string;
  entity_type?: string | null;
  entity_id?: string | null;
  details?: unknown;
  ip_address?: string | null;
  created_at: string;
}

export default function AdminAudit() {
  const [action, setAction] = useState("");

  const { data, isLoading } = useQuery<Paginated<AuditItem>>({
    queryKey: ["audit", action],
    queryFn: () =>
      api.get(`/api/v1/audit-logs?page=1&page_size=100${action ? `&action=${action}` : ""}`),
    refetchInterval: 10000,
  });

  return (
    <div>
      <PageHeader
        title="Auditoria"
        subtitle="Histórico de ações relevantes (acesso, alterações e integrações)"
        actions={
          <div className="w-64">
            <Label>Filtrar por ação</Label>
            <Input
              placeholder="ex.: request.status"
              value={action}
              onChange={(e) => setAction(e.target.value)}
            />
          </div>
        }
      />

      {isLoading ? (
        <p className="text-sm text-slate-500">Carregando...</p>
      ) : (
        <Table>
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Data</th>
              <th className="px-4 py-3">Ação</th>
              <th className="px-4 py-3">Entidade</th>
              <th className="px-4 py-3">Usuário</th>
              <th className="px-4 py-3">IP</th>
              <th className="px-4 py-3">Detalhes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {(data?.data ?? []).map((item) => (
              <tr key={item.id}>
                <td className="px-4 py-3 text-slate-500">{formatDateTime(item.created_at)}</td>
                <td className="px-4 py-3 font-medium">{item.action}</td>
                <td className="px-4 py-3 text-slate-500">
                  {item.entity_type || "—"} {item.entity_id ? `· ${item.entity_id.slice(0, 8)}` : ""}
                </td>
                <td className="px-4 py-3 text-slate-500">
                  {item.actor_user_id ? item.actor_user_id.slice(0, 8) : "sistema"}
                </td>
                <td className="px-4 py-3 text-slate-500">{item.ip_address || "—"}</td>
                <td className="max-w-xs px-4 py-3 text-xs text-slate-400">
                  {item.details ? JSON.stringify(item.details) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
      <p className="mt-4 flex items-center gap-2 text-xs text-slate-400">
        <Shield className="h-3.5 w-3.5" /> Logs não contêm relatos de saúde nem credenciais.
      </p>
    </div>
  );
}
