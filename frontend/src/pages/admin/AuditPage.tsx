import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Shield } from "lucide-react";
import { api } from "../../lib/api";
import type { Paginated } from "../../lib/types";
import { formatDateTime } from "../../lib/format";
import { Label, PageHeader, Select, Table } from "../../components/ui";

const ACTION_LABEL: Record<string, string> = {
  "request.create": "Pedido enviado", "request.status": "Situação do pedido alterada",
  "request.cancel": "Pedido cancelado", "request.risk_classified": "Prioridade avaliada pela equipe",
  "alert.create": "Aviso de chegada enviado", "alert.status": "Situação do aviso alterada",
  "integration.sync": "Dados de outra fonte atualizados", "integration.promote": "Unidade importada",
};
const ITEM_LABEL: Record<string, string> = {
  care_request: "Pedido", emergency_alert: "Aviso de chegada", integration_source: "Fonte de dados", external_unit: "Unidade importada",
};

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
        title="Histórico de alterações"
        subtitle="Confira quando cada alteração aconteceu. Escolha uma ação para filtrar a lista."
        actions={
          <div className="w-64">
            <Label htmlFor="audit-action">Filtrar por ação</Label>
            <Select
              id="audit-action"
              value={action}
              onChange={(e) => setAction(e.target.value)}
            ><option value="">Todas as ações</option>{Object.entries(ACTION_LABEL).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</Select>
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
              <th className="px-4 py-3">Item alterado</th>
              <th className="px-4 py-3">Código do usuário</th>
              <th className="px-4 py-3">Endereço de rede</th>
              <th className="px-4 py-3">Detalhes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {(data?.data ?? []).map((item) => (
              <tr key={item.id}>
                <td className="px-4 py-3 text-slate-500">{formatDateTime(item.created_at)}</td>
                <td className="px-4 py-3 font-medium">{ACTION_LABEL[item.action] ?? item.action}</td>
                <td className="px-4 py-3 text-slate-500">
                  {ITEM_LABEL[item.entity_type ?? ""] ?? item.entity_type ?? "—"} {item.entity_id ? `· ${item.entity_id.slice(0, 8)}` : ""}
                </td>
                <td className="px-4 py-3 text-slate-500">
                  {item.actor_user_id ? item.actor_user_id.slice(0, 8) : "sistema"}
                </td>
                <td className="px-4 py-3 text-slate-500">{item.ip_address || "—"}</td>
                <td className="max-w-xs px-4 py-3 text-xs text-slate-400">
                  {item.details ? <details><summary className="cursor-pointer">Ver registro técnico</summary><pre className="mt-2 whitespace-pre-wrap break-all">{JSON.stringify(item.details, null, 2)}</pre></details> : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
      <p className="mt-4 flex items-center gap-2 text-xs text-slate-400">
        <Shield className="h-3.5 w-3.5" /> Este histórico não inclui relatos de saúde nem senhas.
      </p>
    </div>
  );
}
