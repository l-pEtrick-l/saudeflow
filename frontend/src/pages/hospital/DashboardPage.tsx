import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Ambulance, Bell, CheckCircle2, Clock } from "lucide-react";
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
import { useAuth } from "../../lib/auth";
import { ALERT_STATUS, formatMinutes } from "../../lib/format";
import { Card, EmptyState, Loading, PageHeader, StatCard } from "../../components/ui";

interface HospitalStats {
  unit_id: string;
  unit_name: string;
  alerts_total: number;
  alerts_by_status: Record<string, number>;
  patients_on_the_way: number;
  average_confirmation_minutes: number | null;
  by_day: { date: string; count: number }[];
  by_city: { city: string; count: number }[];
}

export default function HospitalDashboard() {
  const { user } = useAuth();
  const unitId = user?.unit_ids?.[0];

  const { data, isLoading } = useQuery<HospitalStats>({
    queryKey: ["hospital-stats", unitId],
    queryFn: () => api.get(`/api/v1/analytics/hospitals/${unitId}`),
    enabled: !!unitId,
    refetchInterval: 10000,
  });

  if (!unitId) return <EmptyState title="Nenhuma unidade vinculada" />;
  if (isLoading) return <Loading />;
  if (!data) return null;

  return (
    <div>
      <PageHeader
        title={data.unit_name}
        subtitle="Veja quem avisou que está a caminho. Abra os avisos para ler o relato e confirmar o recebimento."
        actions={
          <Link to="/hospital/alertas" className="btn-primary">
            <Bell className="h-4 w-4" /> Avisos de chegada
          </Link>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Avisos de chegada recebidos" value={data.alerts_total} tone="brand" />
        <StatCard label="Pacientes a caminho" value={data.patients_on_the_way} tone="amber" />
        <StatCard
          label="Tempo médio de confirmação"
          value={data.average_confirmation_minutes ? formatMinutes(data.average_confirmation_minutes) : "—"}
          tone="mint"
        />
        <StatCard label="Avisos confirmados" value={data.alerts_by_status.confirmed ?? 0} tone="violet" />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <h2 className="font-semibold text-slate-900">Avisos de chegada por dia</h2>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.by_day}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar name="Avisos" dataKey="count" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <h2 className="font-semibold text-slate-900">Situação dos avisos</h2>
          <ul className="mt-4 space-y-2 text-sm">
            {Object.entries(data.alerts_by_status).map(([status, count]) => (
              <li key={status} className="flex items-center justify-between">
                <span className="capitalize text-slate-600">{ALERT_STATUS[status]?.label ?? status}</span>
                <span className="font-semibold">{count}</span>
              </li>
            ))}
          </ul>
          <Link to="/hospital/historico" className="btn-secondary mt-5 w-full">
            <Clock className="h-4 w-4" /> Ver histórico
          </Link>
        </Card>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <Card>
          <Ambulance className="h-6 w-6 text-brand-600" />
          <p className="mt-2 font-semibold text-slate-900">Recebimento em tempo real</p>
          <p className="text-sm text-slate-500">
            Novos avisos de chegada aparecem automaticamente no painel da unidade.
          </p>
        </Card>
        <Card>
          <CheckCircle2 className="h-6 w-6 text-mint-600" />
          <p className="mt-2 font-semibold text-slate-900">Confirmar que o aviso foi lido</p>
          <p className="text-sm text-slate-500">
            Confirmar recebimento não gera reserva de leito nem garantia de atendimento.
          </p>
        </Card>
      </div>
    </div>
  );
}
