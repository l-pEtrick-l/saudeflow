import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, Megaphone, Users } from "lucide-react";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { estimateText, formatDateTime } from "../../lib/format";
import { Alert, Badge, Button, Card, EmptyState, Loading, PageHeader, StatCard, Table } from "../../components/ui";

interface Ticket {
  arrival_window_start?: string | null;
  arrival_window_end?: string | null;
  request_status?: string;
  id: string;
  request_id: string;
  position: number;
  status: string;
  protocol?: string | null;
  patient_name?: string | null;
  category?: string | null;
  created_at: string;
}

interface Board {
  unit_id: string;
  unit_name: string;
  capacity: { professionals_available: number; rooms_active: number; welcome_capacity: number };
  estimate: { is_reliable: boolean; low_minutes?: number | null; high_minutes?: number | null; message?: string };
  tickets: Ticket[];
}

const TICKET_TONE: Record<string, string> = {
  waiting: "bg-amber-100 text-amber-700",
  called: "bg-brand-100 text-brand-700",
  attending: "bg-violet-100 text-violet-700",
  done: "bg-mint-100 text-mint-700",
  cancelled: "bg-red-100 text-red-700",
  absent: "bg-slate-100 text-slate-600",
};

export default function UpaQueue() {
  const { user } = useAuth();
  const unitId = user?.unit_ids?.[0];
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery<Board>({
    queryKey: ["queue-board", unitId],
    queryFn: () => api.get(`/api/v1/units/${unitId}/queue/board`),
    enabled: !!unitId,
    refetchInterval: 5000,
  });

  const callNext = useMutation({
    mutationFn: () => api.post(`/api/v1/units/${unitId}/queue/call-next`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["queue-board"] }),
  });

  if (!unitId) return <EmptyState title="Nenhuma unidade vinculada" />;
  if (isLoading) return <Loading />;
  if (!data) return null;

  const waiting = data.tickets.filter((t) => t.status === "waiting");
  const ready = waiting.filter(t => !t.arrival_window_start || t.request_status === "patient_arrived");

  return (
    <div>
      <PageHeader
        title="Fila digital"
        subtitle={`${data.unit_name} · ordem administrativa, não clínica`}
        actions={
          <Button onClick={() => callNext.mutate()} disabled={callNext.isPending || ready.length === 0}>
            <Megaphone className="h-4 w-4" /> Chamar próximo
          </Button>
        }
      />
      <Alert className="mb-5" variant="info">A fila reúne pré-cadastros e chegadas planejadas. Confirme o recebimento e registre a chegada em Solicitações. Quem escolheu uma faixa só pode ser chamado após chegar. A classificação de risco continua presencial.</Alert>
      {callNext.error && <Alert variant="danger" className="mb-4">{callNext.error.message}</Alert>}

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Aguardando" value={waiting.length} tone="amber" />
        <StatCard label="Profissionais ativos" value={data.capacity.professionals_available} tone="brand" />
        <StatCard
          label="Estimativa"
          value={data.estimate.is_reliable ? estimateText(data.estimate) : "Sem dados suficientes"}
          tone={data.estimate.is_reliable ? "mint" : "amber"}
        />
      </div>

      <Card className="mt-6">
        <h2 className="flex items-center gap-2 font-semibold text-slate-900">
          <Activity className="h-5 w-5 text-brand-600" /> Posições
        </h2>
        {data.tickets.length === 0 ? (
          <p className="mt-3 text-sm text-slate-500">Nenhuma solicitação ativa na fila.</p>
        ) : (
          <div className="mt-4">
            <Table>
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">Posição</th>
                  <th className="px-4 py-3">Protocolo</th>
                  <th className="px-4 py-3">Paciente</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Chegada planejada</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.tickets.map((ticket) => (
                  <tr key={ticket.id}>
                    <td className="px-4 py-3 font-bold text-brand-700">{ticket.status === "waiting" ? waiting.findIndex(t => t.id === ticket.id) + 1 : "—"}</td>
                    <td className="px-4 py-3 font-semibold">{ticket.protocol || "—"}</td>
                    <td className="px-4 py-3">{ticket.patient_name || "—"}</td>
                    <td className="px-4 py-3">
                      <Badge className={TICKET_TONE[ticket.status] ?? "bg-slate-100 text-slate-600"}>
                        {({ waiting: "Aguardando", called: "Chamado", attending: "Em acolhimento", done: "Concluído", cancelled: "Cancelado", absent: "Ausente" } as Record<string, string>)[ticket.status] || ticket.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-sm">{ticket.arrival_window_start ? <>{formatDateTime(ticket.arrival_window_start)} – {formatDateTime(ticket.arrival_window_end!)}<p className="text-xs text-slate-500">{ticket.request_status === "patient_arrived" ? "Presença registrada" : "A confirmar presencialmente"}</p></> : "Sem horário"}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </div>
        )}
      </Card>

      <p className="mt-4 flex items-center gap-2 text-xs text-slate-400">
        <Users className="h-3.5 w-3.5" /> A posição digital não representa prioridade clínica. A
        classificação de risco é presencial.
      </p>
    </div>
  );
}
