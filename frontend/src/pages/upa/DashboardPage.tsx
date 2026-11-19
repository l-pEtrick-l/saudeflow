import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Activity,
  Bell,
  Building2,
  CheckCircle2,
  Clock,
  Users,
} from "lucide-react";
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
import { estimateText, formatMinutes } from "../../lib/format";
import { Badge, Card, EmptyState, Loading, PageHeader, StatCard } from "../../components/ui";

interface UnitStats {
  unit_id: string;
  unit_name: string;
  requests_received: number;
  pre_registers_confirmed: number;
  patients_present: number;
  awaiting_welcome: number;
  in_care: number;
  finished: number;
  cancelled: number;
  average_wait_minutes: number | null;
  capacity: {
    professionals_available: number;
    rooms_active: number;
    welcome_capacity: number;
    receiving_pre_registrations: boolean;
  };
  estimate: { is_reliable: boolean; low_minutes?: number | null; high_minutes?: number | null; message?: string };
  alerts_received: number;
  by_day: { date: string; count: number }[];
}

export default function UpaDashboard() {
  const { user } = useAuth();
  const unitId = user?.unit_ids?.[0];

  const { data, isLoading } = useQuery<UnitStats>({
    queryKey: ["unit-stats", unitId],
    queryFn: () => api.get(`/api/v1/analytics/units/${unitId}`),
    enabled: !!unitId,
    refetchInterval: 10000,
  });

  if (!unitId) {
    return (
      <EmptyState
        title="Nenhuma unidade vinculada"
        description="Sua conta não possui vínculo com uma unidade. Solicite ao administrador."
      />
    );
  }
  if (isLoading) return <Loading />;
  if (!data) return null;

  return (
    <div>
      <PageHeader
        title={data.unit_name}
        subtitle="Visão operacional da unidade (dados de demonstração)"
        actions={
          <>
            <Link to="/upa/fila" className="btn-secondary">
              <Activity className="h-4 w-4" /> Fila
            </Link>
            <Link to="/upa/solicitacoes" className="btn-primary">
              Solicitações
            </Link>
          </>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Solicitações recebidas" value={data.requests_received} tone="brand" />
        <StatCard label="Pré-cadastros confirmados" value={data.pre_registers_confirmed} tone="mint" />
        <StatCard label="Pacientes presentes" value={data.patients_present} tone="violet" />
        <StatCard label="Em atendimento" value={data.in_care} tone="amber" />
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Aguardando acolhimento" value={data.awaiting_welcome} tone="violet" />
        <StatCard label="Finalizadas" value={data.finished} tone="mint" />
        <StatCard
          label="Tempo médio de atendimento"
          value={data.average_wait_minutes ? formatMinutes(data.average_wait_minutes) : "—"}
          tone="brand"
        />
        <StatCard label="Pré-alertas recebidos" value={data.alerts_received} tone="red" />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <h2 className="font-semibold text-slate-900">Solicitações por dia (14 dias)</h2>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.by_day}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#1b6ef5" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <h2 className="font-semibold text-slate-900">Capacidade e estimativa</h2>
          <dl className="mt-4 space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate-500">Profissionais</dt>
              <dd className="font-semibold">{data.capacity.professionals_available}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Salas ativas</dt>
              <dd className="font-semibold">{data.capacity.rooms_active}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Capacidade de acolhimento</dt>
              <dd className="font-semibold">{data.capacity.welcome_capacity}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Recebendo pré-cadastros</dt>
              <dd>
                <Badge className={data.capacity.receiving_pre_registrations ? "bg-mint-50 text-mint-700" : "bg-red-50 text-red-700"}>
                  {data.capacity.receiving_pre_registrations ? "Sim" : "Não"}
                </Badge>
              </dd>
            </div>
            <div className="border-t border-slate-100 pt-3">
              <dt className="text-slate-500">Estimativa operacional</dt>
              <dd className={`mt-1 font-semibold ${data.estimate.is_reliable ? "text-mint-700" : "text-amber-700"}`}>
                {estimateText(data.estimate)}
              </dd>
            </div>
          </dl>
          <Link to="/upa/capacidade" className="btn-secondary mt-4 w-full">
            <Building2 className="h-4 w-4" /> Alterar capacidade
          </Link>
        </Card>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <Link to="/upa/solicitacoes">
          <Card className="hover:border-brand-200">
            <Users className="h-6 w-6 text-brand-600" />
            <p className="mt-2 font-semibold text-slate-900">Gerenciar solicitações</p>
            <p className="text-sm text-slate-500">Confirmar, registrar chegada e atualizar status.</p>
          </Card>
        </Link>
        <Link to="/upa/fila">
          <Card className="hover:border-brand-200">
            <CheckCircle2 className="h-6 w-6 text-brand-600" />
            <p className="mt-2 font-semibold text-slate-900">Fila digital</p>
            <p className="text-sm text-slate-500">Chamar protocolos e acompanhar posições.</p>
          </Card>
        </Link>
        <Link to="/upa/alertas">
          <Card className="hover:border-brand-200">
            <Bell className="h-6 w-6 text-brand-600" />
            <p className="mt-2 font-semibold text-slate-900">Pré-alertas</p>
            <p className="text-sm text-slate-500">Pacientes que informaram estar a caminho.</p>
          </Card>
        </Link>
      </div>

      <p className="mt-6 flex items-center gap-2 text-xs text-slate-400">
        <Clock className="h-3.5 w-3.5" /> A fila digital é administrativa e não define prioridade clínica.
      </p>
    </div>
  );
}
