import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, ClipboardList, Play, Search, StopCircle, UserCheck } from "lucide-react";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import type { Paginated, Request } from "../../lib/types";
import { formatDateTime, REQUEST_STATUS } from "../../lib/format";
import { Alert, Badge, Button, Card, EmptyState, Input, Loading, Modal, PageHeader, Select, Table, Textarea } from "../../components/ui";

export default function UpaRequests() {
  const { user } = useAuth();
  const unitId = user?.unit_ids?.[0];
  const queryClient = useQueryClient();
  const [status, setStatus] = useState("");
  const [selected, setSelected] = useState<Request | null>(null);
  const [cancelReason, setCancelReason] = useState("");
  const [error, setError] = useState("");

  const { data, isLoading } = useQuery<Paginated<Request>>({
    queryKey: ["unit-requests", unitId, status],
    queryFn: () =>
      api.get(`/api/v1/requests?page=1&page_size=50&unit_id=${unitId}${status ? `&status=${status}` : ""}`),
    enabled: !!unitId,
    refetchInterval: 8000,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["unit-requests"] });

  const confirm = useMutation({
    mutationFn: (id: string) => api.post(`/api/v1/requests/${id}/confirm-receipt`),
    onSuccess: invalidate,
  });
  const checkin = useMutation({
    mutationFn: (id: string) => api.post(`/api/v1/requests/${id}/checkin`, { method: "desk" }),
    onSuccess: invalidate,
  });
  const startCare = useMutation({
    mutationFn: (id: string) => api.post(`/api/v1/requests/${id}/care-start`, {}),
    onSuccess: invalidate,
  });
  const finishCare = useMutation({
    mutationFn: (id: string) => api.post(`/api/v1/requests/${id}/care-finish`, { outcome: "released" }),
    onSuccess: invalidate,
  });
  const cancel = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      api.post(`/api/v1/requests/${id}/cancel`, { reason }),
    onSuccess: () => {
      invalidate();
      setSelected(null);
      setCancelReason("");
    },
    onError: (err: Error) => setError(err.message),
  });

  const items = data?.data ?? [];

  return (
    <div>
      <PageHeader
        title="Solicitações"
        subtitle="Pré-cadastros digitais recebidos por esta unidade"
        actions={
          <Select value={status} onChange={(e) => setStatus(e.target.value)} className="w-56">
            <option value="">Todos os status</option>
            {Object.entries(REQUEST_STATUS).map(([value, item]) => (
              <option key={value} value={value}>
                {item.label}
              </option>
            ))}
          </Select>
        }
      />
      <Alert variant="info" className="mb-5">Confirme o pré-cadastro, registre a chegada quando o paciente estiver na unidade e então inicie o atendimento. A faixa escolhida ajuda a organizar a recepção e pode variar conforme a demanda.</Alert>
      {(confirm.error || checkin.error || startCare.error || finishCare.error) && <Alert variant="danger" className="mb-4">{(confirm.error || checkin.error || startCare.error || finishCare.error)?.message}</Alert>}

      {isLoading ? (
        <Loading />
      ) : items.length === 0 ? (
        <EmptyState title="Nenhuma solicitação" description="As solicitações digitais aparecerão aqui." />
      ) : (
        <Table>
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Protocolo</th>
              <th className="px-4 py-3">Paciente</th>
              <th className="px-4 py-3">Categoria</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Criada em</th>
              <th className="px-4 py-3 text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((request) => (
              <tr key={request.id}>
                <td className="px-4 py-3 font-semibold text-brand-700">{request.protocol}</td>
                <td className="px-4 py-3">{request.patient_name}</td>
                <td className="px-4 py-3">
                  <Badge className="bg-slate-100 text-slate-600">{request.category}</Badge>
                </td>
                <td className="px-4 py-3">
                  <Badge className={REQUEST_STATUS[request.status]?.tone}>
                    {request.status_label}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-slate-500">{formatDateTime(request.created_at)}{request.arrival_window_start && <p className="mt-1 text-xs text-brand-700">Chegada: {formatDateTime(request.arrival_window_start)} – {formatDateTime(request.arrival_window_end!)}</p>}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap justify-end gap-1.5">
                    <Button variant="ghost" size="sm" onClick={() => setSelected(request)}>
                      <Search className="h-3.5 w-3.5" /> Detalhes
                    </Button>
                    {["sent", "awaiting_confirmation"].includes(request.status) && (
                      <Button variant="secondary" size="sm" onClick={() => confirm.mutate(request.id)}>
                        <CheckCircle2 className="h-3.5 w-3.5" /> Confirmar
                      </Button>
                    )}
                    {request.status === "pre_register_confirmed" && (
                      <Button variant="secondary" size="sm" onClick={() => checkin.mutate(request.id)}>
                        <UserCheck className="h-3.5 w-3.5" /> Chegada
                      </Button>
                    )}
                    {["patient_arrived", "awaiting_welcome", "awaiting_care"].includes(request.status) && (
                      <Button variant="secondary" size="sm" onClick={() => startCare.mutate(request.id)}>
                        <Play className="h-3.5 w-3.5" /> Iniciar
                      </Button>
                    )}
                    {request.status === "in_care" && (
                      <Button variant="success" size="sm" onClick={() => finishCare.mutate(request.id)}>
                        <StopCircle className="h-3.5 w-3.5" /> Concluir
                      </Button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      <Modal open={!!selected} onClose={() => setSelected(null)} title={`Protocolo ${selected?.protocol ?? ""}`}>
        {selected && (
          <div className="space-y-3 text-sm">
            <p>
              <strong>Paciente:</strong> {selected.patient_name}
            </p>
            <p>
              <strong>Telefone:</strong> {selected.patient_phone || "—"}
            </p>
            <p>
              <strong>Status:</strong>{" "}
              <Badge className={REQUEST_STATUS[selected.status]?.tone}>{selected.status_label}</Badge>
            </p>
            <p>
              <strong>Categoria de orientação:</strong> {selected.category}
            </p>
            {selected.complaint_summary && (
              <p>
                <strong>Resumo:</strong> {selected.complaint_summary}
              </p>
            )}
            {selected.arrival_window_start && <p><strong>Faixa escolhida:</strong> {formatDateTime(selected.arrival_window_start)} – {formatDateTime(selected.arrival_window_end!)}</p>}
            {selected.ticket && (
              <p>
                <strong>Posição na fila digital:</strong> {selected.ticket.position} (
                {selected.ticket.status})
              </p>
            )}
            <p className="text-xs text-slate-400">
              As informações vieram de formulário digital e não foram verificadas clinicamente.
            </p>
            {error && <Alert variant="danger">{error}</Alert>}
            { ![
              "finished",
              "cancelled",
            ].includes(selected.status) && (
              <div className="border-t border-slate-100 pt-3">
                <label className="label">Cancelar solicitação</label>
                <Textarea
                  rows={2}
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  placeholder="Justificativa obrigatória"
                />
                <Button
                  variant="danger"
                  className="mt-2"
                  disabled={cancelReason.trim().length < 3 || cancel.isPending}
                  onClick={() => cancel.mutate({ id: selected.id, reason: cancelReason })}
                >
                  <ClipboardList className="h-4 w-4" /> Cancelar
                </Button>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
