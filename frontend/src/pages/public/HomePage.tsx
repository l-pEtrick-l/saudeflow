import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  Building2,
  ClipboardList,
  HeartPulse,
  Hospital,
  Loader2,
  MapPin,
  Shield,
  ShieldAlert,
  Siren,
  Sparkles,
  UserRound,
} from "lucide-react";
import { Card } from "../../components/ui";
import { DEMO_ACCOUNTS, demoLogin, type DemoRole } from "../../lib/demo";

const quickAccess: { role: DemoRole; icon: React.ReactNode; title: string; text: string }[] = [
  {
    role: "patient",
    icon: <UserRound className="h-6 w-6" />,
    title: "Visão Paciente",
    text: "Questionário, orientação, protocolo e acompanhamento em tempo real.",
  },
  {
    role: "upa",
    icon: <Building2 className="h-6 w-6" />,
    title: "Visão UPA",
    text: "Dashboard operacional, fila digital, solicitações, alertas e capacidade.",
  },
  {
    role: "hospital",
    icon: <Hospital className="h-6 w-6" />,
    title: "Visão Hospital",
    text: "Recebimento de pré-alertas, confirmações, histórico e indicadores.",
  },
  {
    role: "admin",
    icon: <Shield className="h-6 w-6" />,
    title: "Visão Admin",
    text: "Unidades, usuários e papéis, integrações externas e auditoria.",
  },
];

const features = [
  {
    icon: <HeartPulse className="h-6 w-6" />,
    title: "Orientação inteligente",
    text: "Responda a um questionário curto e adaptativo. O sistema indica o tipo de serviço potencialmente adequado — sem diagnosticar.",
  },
  {
    icon: <Building2 className="h-6 w-6" />,
    title: "Unidades compatíveis",
    text: "Compare UPAs, hospitais e UBS por serviços, distância aproximada e estimativa de espera operacional.",
  },
  {
    icon: <ClipboardList className="h-6 w-6" />,
    title: "Fila online e chegada planejada",
    text: "Na UPA, escolha uma faixa de chegada quando disponível, receba seu protocolo e acompanhe a posição e a previsão atualizada.",
  },
  {
    icon: <ShieldAlert className="h-6 w-6" />,
    title: "Pré-alerta de emergência",
    text: "Avise a unidade que você está a caminho, compartilhando informações preliminares — sem substituir o SAMU 192.",
  },
];

export default function HomePage() {
  const [loading, setLoading] = useState<DemoRole | null>(null);

  async function quickLogin(role: DemoRole) {
    setLoading(role);
    try {
      await demoLogin(role);
    } catch {
      setLoading(null);
    }
  }

  return (
    <div>
      <section className="bg-gradient-to-br from-brand-700 via-brand-600 to-mint-600 text-white">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:py-20">
          <span className="badge bg-white/15 text-white">
            <Sparkles className="h-3.5 w-3.5" /> Demonstração acadêmica — Global Solution FIAP
          </span>
          <h1 className="mt-5 max-w-3xl text-4xl font-extrabold leading-tight sm:text-5xl">
            Orientação inteligente para o atendimento de saúde
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-white/85">
            Encontre orientação, escolha uma unidade e entre na fila online. Nas UPAs com previsão disponível,
            planeje sua chegada e acompanhe pelo celular — para reduzir a espera presencial.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/atendimento" className="btn bg-white text-brand-700 hover:bg-brand-50 px-6 py-3.5 text-base">
              Preciso de atendimento <ArrowRight className="h-5 w-5" />
            </Link>
            <Link to="/unidades" className="btn bg-white/10 text-white border border-white/30 hover:bg-white/20 px-6 py-3.5 text-base">
              <MapPin className="h-5 w-5" /> Ver unidades próximas
            </Link>
            <Link to="/emergencia" className="btn bg-red-500 text-white hover:bg-red-600 px-6 py-3.5 text-base">
              <Siren className="h-5 w-5" /> Emergência
            </Link>
          </div>
          <p className="mt-4 max-w-2xl text-sm text-white/80">A chegada é aproximada e pode mudar. Urgências e a classificação de risco presencial definem a prioridade do atendimento.</p>
          <div className="mt-8 flex flex-wrap gap-4 text-sm text-white/80">
            <Link to="/acompanhar" className="underline decoration-white/40 hover:decoration-white">
              Acompanhar minha solicitação
            </Link>
            <Link to="/login" className="underline decoration-white/40 hover:decoration-white">
              Entrar na minha conta
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-14">
        <h2 className="text-2xl font-bold text-slate-900">Como funciona</h2>
        <p className="mt-2 text-slate-600">
          Comece em “Preciso de atendimento”. Responda ao questionário, escolha a unidade e acompanhe seu protocolo.
        </p>
        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((feature) => (
            <Card key={feature.title}>
              <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
                {feature.icon}
              </span>
              <h3 className="mt-4 font-semibold text-slate-900">{feature.title}</h3>
              <p className="mt-2 text-sm text-slate-600">{feature.text}</p>
            </Card>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-14">
        <div className="rounded-3xl border border-brand-100 bg-brand-50 p-6 sm:p-8">
          <h2 className="text-2xl font-bold text-slate-900">Sua chegada, passo a passo</h2>
          <ol className="mt-6 grid gap-5 sm:grid-cols-3">
            <li><p className="font-bold text-brand-700">1. Conte o que precisa</p><p className="mt-2 text-sm text-slate-600">O questionário orienta o tipo de serviço. Em sinais de emergência, siga a orientação imediata.</p></li>
            <li><p className="font-bold text-brand-700">2. Escolha a UPA e a faixa</p><p className="mt-2 text-sm text-slate-600">Veja as unidades compatíveis e, quando houver previsão, escolha uma faixa de chegada. Seu protocolo identifica a entrada na fila digital.</p></li>
            <li><p className="font-bold text-brand-700">3. Acompanhe antes de sair</p><p className="mt-2 text-sm text-slate-600">Confira posição e previsão atualizadas. Na unidade, mostre o protocolo à recepção para registrar sua chegada.</p></li>
          </ol>
          <details className="mt-6 border-t border-brand-100 pt-4"><summary className="cursor-pointer font-semibold text-brand-800">O horário e a posição são garantidos?</summary><p className="mt-2 text-sm text-slate-600">Não. A faixa organiza a chegada à recepção, e não uma consulta marcada. A demanda, a capacidade e as urgências podem alterar a previsão. A posição é administrativa; a avaliação presencial define a prioridade clínica. Este site é uma demonstração acadêmica, sem reserva real em unidades de saúde.</p></details>
          <details className="mt-4"><summary className="cursor-pointer font-semibold text-brand-800">E se não aparecer nenhum horário?</summary><p className="mt-2 text-sm text-slate-600">A unidade pode estar sem histórico suficiente ou com o planejamento temporariamente indisponível. Você ainda pode consultar as unidades e, quando permitido, gerar um pré-cadastro sem horário. Para UBS, consulte o agendamento diretamente na unidade.</p></details>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-14">
        <h2 className="text-2xl font-bold text-slate-900">Acesso rápido de demonstração</h2>
        <p className="mt-2 text-slate-600">
          Entre com um clique em qualquer portal — sem precisar de cadastro.
        </p>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {quickAccess.map(({ role, icon, title, text }) => (
            <Card key={role} className="flex flex-col">
              <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
                {icon}
              </span>
              <h3 className="mt-4 font-semibold text-slate-900">{title}</h3>
              <p className="mt-2 flex-1 text-sm text-slate-600">{text}</p>
              <button
                onClick={() => quickLogin(role)}
                disabled={loading !== null}
                className="btn-secondary mt-4 w-full disabled:opacity-50"
              >
                {loading === role ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ArrowRight className="h-4 w-4" />
                )}
                Entrar como {DEMO_ACCOUNTS[role].label}
              </button>
            </Card>
          ))}
        </div>
      </section>

      <section className="bg-amber-50 border-y border-amber-100">
        <div className="mx-auto max-w-6xl px-4 py-8 text-sm text-amber-900">
          <p className="font-semibold">Aviso importante</p>
          <p className="mt-1">
            O SaúdeFlow não substitui médicos, classificação de risco presencial, regulação médica ou
            o SAMU 192. As orientações são auxiliares, conservadoras e demonstrativas. Em emergência,
            ligue 192.
          </p>
        </div>
      </section>
    </div>
  );
}
