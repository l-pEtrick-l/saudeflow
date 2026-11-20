export function formatDateTime(value?: string | null) {
  if (!value) return "—";
  // SQLite returns UTC timestamps without an offset; PostgreSQL includes it.
  const normalized = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(value) && !/(Z|[+-]\d{2}:\d{2})$/i.test(value) ? `${value}Z` : value;
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatMinutes(minutes?: number | null) {
  if (minutes === null || minutes === undefined) return "—";
  if (minutes < 60) return `${Math.round(minutes)} min`;
  const hours = Math.floor(minutes / 60);
  const rest = Math.round(minutes % 60);
  return rest ? `${hours}h${rest}min` : `${hours}h`;
}

export function estimateText(estimate?: {
  is_reliable: boolean;
  low_minutes?: number | null;
  p50_minutes?: number | null;
  high_minutes?: number | null;
  message?: string;
  updated_at?: string;
} | null) {
  if (!estimate) return "Sem estimativa";
  if (!estimate.is_reliable) return "Sem dados suficientes para estimar";
  if (estimate.low_minutes === 0 && estimate.high_minutes === 0)
    return "Nenhuma pessoa aguardando";
  return `Estimativa: ${Math.round(estimate.low_minutes ?? 0)}–${Math.round(
    estimate.high_minutes ?? 0
  )} min`;
}

export function cepMask(value: string) {
  return value
    .replace(/\D/g, "")
    .slice(0, 8)
    .replace(/(\d{5})(\d)/, "$1-$2");
}

export function cpfMask(value: string) {
  return value
    .replace(/\D/g, "")
    .slice(0, 11)
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
}

export function phoneMask(value: string) {
  const digits = value.replace(/\D/g, "").slice(0, 11);
  if (digits.length <= 10) {
    return digits.replace(/(\d{2})(\d)/, "($1) $2").replace(/(\d{4})(\d)/, "$1-$2");
  }
  return digits.replace(/(\d{2})(\d)/, "($1) $2").replace(/(\d{5})(\d)/, "$1-$2");
}

export const REQUEST_STATUS: Record<string, { label: string; tone: string }> = {
  sent: { label: "Enviada", tone: "bg-slate-100 text-slate-700" },
  awaiting_confirmation: { label: "Aguardando confirmação", tone: "bg-amber-100 text-amber-700" },
  pre_register_confirmed: { label: "Pré-cadastro confirmado", tone: "bg-brand-100 text-brand-700" },
  patient_arrived: { label: "Paciente chegou", tone: "bg-brand-100 text-brand-700" },
  awaiting_welcome: { label: "Aguardando acolhimento", tone: "bg-violet-100 text-violet-700" },
  awaiting_care: { label: "Aguardando atendimento", tone: "bg-violet-100 text-violet-700" },
  in_care: { label: "Em atendimento", tone: "bg-mint-100 text-mint-700" },
  finished: { label: "Finalizado", tone: "bg-mint-100 text-mint-700" },
  cancelled: { label: "Cancelado", tone: "bg-red-100 text-red-700" },
};

export const ALERT_STATUS: Record<string, { label: string; tone: string }> = {
  new: { label: "Novo", tone: "bg-red-100 text-red-700" },
  received: { label: "Recebido", tone: "bg-amber-100 text-amber-700" },
  confirmed: { label: "Confirmado", tone: "bg-brand-100 text-brand-700" },
  arrived: { label: "Chegada registrada", tone: "bg-mint-100 text-mint-700" },
  closed: { label: "Encerrado", tone: "bg-slate-100 text-slate-700" },
  cancelled: { label: "Cancelado", tone: "bg-red-100 text-red-700" },
};
