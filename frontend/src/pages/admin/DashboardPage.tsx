import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Building2, ClipboardList, Siren, Users } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../../lib/api";
import { formatMinutes } from "../../lib/format";
import { Card, Loading, PageHeader, StatCard } from "../../components/ui";

interface Overview {
  total_units: number;
  units_by_type: Record<string, number>;
  total_users: number;
  total_requests: number;
  requests_by_status: Record<string, number>;
  active_requests: number;
  total_alerts: number;
  alerts_by_status: Record<string, number>;
  average_attendance_minutes: number | null;
  last_24h_requests: number;
}

export default function AdminDashboard() {
  const { data, isLoading } = useQuery<Overview>({
    queryKey: ["admin-overview"],
    queryFn: () => api.get("/api/v1/analytics/overview"),
    refetchInterval: 15000,
  });

  if (isLoading) return <Loading />;
  if (!data) return null;

  const chart = Object.entries(data.units_by_type).map(([name, value]) => ({ name, value }));

  return (
    <div>
      <PageHeader title="Administração" subtitle="Indicadores gerais do sistema (dados de demonstração)" />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Unidades" value={data.total_units} tone="brand" />
        <StatCard label="Usuários" value={data.total_users} tone="violet" />
        <StatCard label="Solicitações ativas" value={data.active_requests} tone="amber" />
        <StatCard label="Pré-alertas" value={data.total_alerts} tone="red" />
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total de solicitações" value={data.total_requests} tone="brand" />
        <StatCard label="Últimas 24h" value={data.last_24h_requests} tone="mint" />
        <StatCard
          label="Tempo médio de atendimento"
          value={data.average_attendance_minutes ? formatMinutes(data.average_attendance_minutes) : "—"}
          tone="violet"
        />
        <StatCard label="Alertas confirmados" value={data.alerts_by_status.confirmed ?? 0} tone="amber" />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <h2 className="font-semibold text-slate-900">Unidades por tipo</h2>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chart}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" fill="#1b6ef5" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <h2 className="font-semibold text-slate-900">Atalhos</h2>
          <div className="mt-4 space-y-3">
            <Link to="/admin/unidades" className="flex items-center gap-3 rounded-xl border border-slate-100 p-3 hover:border-brand-200">
              <Building2 className="h-5 w-5 text-brand-600" />
              <span className="text-sm font-medium">Gerenciar unidades</span>
            </Link>
            <Link to="/admin/usuarios" className="flex items-center gap-3 rounded-xl border border-slate-100 p-3 hover:border-brand-200">
              <Users className="h-5 w-5 text-brand-600" />
              <span className="text-sm font-medium">Gerenciar usuários e papéis</span>
            </Link>
            <Link to="/admin/integracoes" className="flex items-center gap-3 rounded-xl border border-slate-100 p-3 hover:border-brand-200">
              <ClipboardList className="h-5 w-5 text-brand-600" />
              <span className="text-sm font-medium">Integrações externas</span>
            </Link>
            <Link to="/admin/auditoria" className="flex items-center gap-3 rounded-xl border border-slate-100 p-3 hover:border-brand-200">
              <Siren className="h-5 w-5 text-brand-600" />
              <span className="text-sm font-medium">Auditoria</span>
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}
