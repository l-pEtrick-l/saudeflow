import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { Clock, MapPin, Search, ShieldAlert } from "lucide-react";
import { PatientNav } from "../../components/PatientNav";
import { api } from "../../lib/api";
import { estimateText, formatDateTime } from "../../lib/format";
import { Alert, Badge, Button, Card, Input, Loading } from "../../components/ui";
import { REQUEST_STATUS } from "../../lib/format";

interface Tracking {
  queue: {
    position: number | null;
    people_ahead: number | null;
    arrival_window_start: string | null;
    arrival_window_end: string | null;
    expected_arrival_start: string | null;
    expected_arrival_end: string | null;
    updated_at: string;
    message: string;
  };
  protocol: string;
  status: string;
  status_label: string;
  unit_name: string | null;
  unit_city: string | null;
  category: string;
  created_at: string;
  updated_at: string;
  estimate: {
    is_reliable: boolean;
    low_minutes?: number | null;
    high_minutes?: number | null;
    message?: string;
  };
}

export default function TrackingPage() {
  const params = useParams<{ protocol: string }>();
  const [input, setInput] = useState(params?.protocol ?? "");
  const [protocol, setProtocol] = useState(params?.protocol ?? "");

  const { data, isLoading, error } = useQuery<Tracking>({
    queryKey: ["tracking", protocol],
    queryFn: () => api.get(`/api/v1/requests/track/${protocol}`),
    enabled: !!protocol,
    refetchInterval: 5000, // fallback de polling quando o WebSocket não está disponível
  });

  const status = data ? REQUEST_STATUS[data.status] : undefined;

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <PatientNav />
      <h1 className="text-2xl font-bold text-slate-900">Acompanhar meu pedido</h1>
      <p className="mt-1 text-sm text-slate-500">
        Digite o número do seu pedido, chamado protocolo (ex.: SF-2026-000125). Você verá a fila e as novidades aqui.
      </p>

      <form
        className="mt-5 flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          setProtocol(input.trim().toUpperCase());
        }}
      >
        <Input
          aria-label="Número do protocolo"
          placeholder="SF-2026-000125"
          value={input}
          onChange={(event) => setInput(event.target.value)}
        />
        <Button type="submit">
          <Search className="h-4 w-4" /> Buscar
        </Button>
      </form>

      {isLoading && protocol && <Loading />}
      {error && (
        <Alert variant="danger" className="mt-6">
          Protocolo não encontrado. Confira o número recebido ao enviar seu pedido.
        </Alert>
      )}

      {data && (
        <>
          <Card className="mt-6">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400">Protocolo</p>
                <p className="text-2xl font-extrabold text-brand-700">{data.protocol}</p>
              </div>
              <Badge className={status?.tone ?? "bg-slate-100 text-slate-600"}>
                {data.status_label}
              </Badge>
            </div>
            <div className="mt-5 grid gap-3 text-sm text-slate-600 sm:grid-cols-2">
              <p className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-slate-400" />
                {data.unit_name || "—"} {data.unit_city ? `· ${data.unit_city}` : ""}
              </p>
              <p className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-slate-400" />
                <span
                  className={
                    data.estimate.is_reliable ? "font-medium text-mint-700" : "text-amber-700"
                  }
                >
                  {estimateText(data.estimate)}
                </span>
              </p>
              <p>Enviado em: {formatDateTime(data.created_at)}</p>
              <p>Última atualização: {formatDateTime(data.updated_at)}</p>
            </div>
          </Card>

          {data.queue && !["finished", "cancelled"].includes(data.status) && (
            <Card className="mt-6 border-brand-100 bg-brand-50/40">
              <h2 className="text-xl font-bold text-brand-800">Sua fila online</h2>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div><p className="text-sm text-slate-500">Sua posição na fila online</p><p className="text-3xl font-extrabold text-brand-700">{data.queue.position ? `${data.queue.position}º` : "Em andamento"}</p>{data.queue.people_ahead !== null && <p className="text-sm text-slate-600">{data.queue.people_ahead} pedido(s) à sua frente</p>}</div>
                <div><p className="text-sm text-slate-500">Horário de chegada que você escolheu</p><p className="font-semibold text-slate-800">{data.queue.arrival_window_start ? `${formatDateTime(data.queue.arrival_window_start)} – ${formatDateTime(data.queue.arrival_window_end!)}` : "Pedido sem horário escolhido"}</p></div>
              </div>
              {data.queue.expected_arrival_start && <div className="mt-4 rounded-xl bg-white p-4"><p className="text-sm text-slate-600">Previsão de chegada agora</p><p className="mt-1 text-lg font-bold text-brand-700">{formatDateTime(data.queue.expected_arrival_start)} – {formatDateTime(data.queue.expected_arrival_end!)}</p><p className="mt-2 text-xs text-slate-500">Horário do seu celular ou computador · atualizado às {formatDateTime(data.queue.updated_at)}</p></div>}
              <p className="mt-4 text-sm text-slate-600" role="status">{data.queue.message}</p>
              <ol className="mt-4 list-inside list-decimal space-y-2 text-sm text-slate-700"><li>Guarde este protocolo e confira a previsão antes de sair.</li><li>Ao chegar, apresente o protocolo para registrar sua presença.</li><li>A equipe vai avaliar seu caso e orientar o atendimento.</li></ol>
              <p className="mt-4 text-sm font-medium text-amber-800">Se houver piora ou emergência, não espere pelo horário da fila. Procure atendimento; em emergência, ligue 192.</p>
            </Card>
          )}

          <div className="mt-6 rounded-2xl border border-slate-100 bg-white p-5 shadow-soft">
            <p className="mb-3 text-sm font-semibold text-slate-700">O que aconteceu até agora</p>
            <ol className="relative space-y-4 border-l border-slate-200 pl-5">
              <li>
                <span className="absolute -left-[5px] mt-1 h-2.5 w-2.5 rounded-full bg-brand-500" />
                <p className="text-sm font-medium text-slate-800">Pedido enviado</p>
                <p className="text-xs text-slate-500">{formatDateTime(data.created_at)}</p>
              </li>
              <li>
                <span
                  className={`absolute -left-[5px] mt-1 h-2.5 w-2.5 rounded-full ${
                    data.status === "sent" ? "bg-slate-300" : "bg-brand-500"
                  }`}
                />
                <p className="text-sm font-medium text-slate-800">{data.status_label}</p>
                <p className="text-xs text-slate-500">{formatDateTime(data.updated_at)}</p>
              </li>
            </ol>
          </div>

          <Alert variant="info" className="mt-6">
            A página se atualiza sozinha a cada 5 segundos. O protocolo é o número do seu pedido. Ele não garante atendimento com hora marcada nem muda a prioridade definida pela equipe de saúde.
          </Alert>
        </>
      )}

      <div className="mt-6 text-center">
        <Link to="/atendimento" className="btn-primary">
          Fazer um novo pedido
        </Link>
      </div>
    </div>
  );
}
