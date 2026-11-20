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
    title: "Área do paciente",
    text: "Descubra onde procurar ajuda, entre na fila online e acompanhe seu pedido.",
  },
  {
    role: "upa",
    icon: <Building2 className="h-6 w-6" />,
    title: "Área da UPA",
    text: "Receba pedidos, organize a fila e registre a chegada e o atendimento.",
  },
  {
    role: "hospital",
    icon: <Hospital className="h-6 w-6" />,
    title: "Área do hospital",
    text: "Veja quem está a caminho, confirme os avisos e consulte o histórico.",
  },
  {
    role: "admin",
    icon: <Shield className="h-6 w-6" />,
    title: "Administração",
    text: "Cuide dos cadastros, escolha quem pode acessar cada área e acompanhe as alterações.",
  },
];

const features = [
  {
    icon: <HeartPulse className="h-6 w-6" />,
    title: "Descubra onde buscar ajuda",
    text: "Conte o que está acontecendo. Suas respostas ajudam a indicar um tipo de unidade para procurar.",
  },
  {
    icon: <Building2 className="h-6 w-6" />,
    title: "Compare as unidades",
    text: "Veja os serviços, o endereço e a espera aproximada de cada unidade.",
  },
  {
    icon: <ClipboardList className="h-6 w-6" />,
    title: "Fila online e chegada planejada",
    text: "Na UPA, escolha uma faixa de chegada quando disponível, receba seu protocolo e acompanhe a posição e a previsão atualizada.",
  },
  {
    icon: <ShieldAlert className="h-6 w-6" />,
    title: "Avisar que estou a caminho",
    text: "Já está indo ao hospital? Conte à equipe o que aconteceu e quando pretende chegar. Isso não chama ambulância.",
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
            Encontre atendimento e acompanhe sua vez
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
          <p className="mt-4 max-w-2xl text-sm text-white/80">O horário é aproximado. Na unidade, a equipe de saúde avalia quem precisa ser atendido primeiro.</p>
          <div className="mt-8 flex flex-wrap gap-4 text-sm text-white/80">
            <Link to="/acompanhar" className="underline decoration-white/40 hover:decoration-white">
              Acompanhar meu pedido
            </Link>
            <Link to="/login" className="underline decoration-white/40 hover:decoration-white">
              Entrar na minha conta
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-14">
        <h2 className="text-2xl font-bold text-slate-900">O que você pode fazer aqui</h2>
        <p className="mt-2 text-slate-600">
          Comece em “Preciso de atendimento”. Responda às perguntas, escolha a unidade e acompanhe seu pedido.
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
            <li><p className="font-bold text-brand-700">1. Conte o que precisa</p><p className="mt-2 text-sm text-slate-600">As respostas ajudam a indicar onde buscar ajuda. Em sinais de emergência, siga a orientação imediata.</p></li>
            <li><p className="font-bold text-brand-700">2. Escolha a UPA e o horário</p><p className="mt-2 text-sm text-slate-600">Veja as unidades indicadas e, quando houver previsão, escolha uma faixa de chegada. Você recebe um protocolo: o número para acompanhar seu pedido.</p></li>
            <li><p className="font-bold text-brand-700">3. Acompanhe antes de sair</p><p className="mt-2 text-sm text-slate-600">Confira posição e previsão atualizadas. Na unidade, mostre o protocolo à recepção para registrar sua chegada.</p></li>
          </ol>
          <details className="mt-6 border-t border-brand-100 pt-4"><summary className="cursor-pointer font-semibold text-brand-800">O horário e a posição são garantidos?</summary><p className="mt-2 text-sm text-slate-600">Não. A faixa organiza a chegada à recepção, e não uma consulta marcada. O movimento, a equipe disponível e as urgências podem alterar a previsão. A posição mostra a ordem dos pedidos. Pessoas com maior urgência podem ser atendidas antes. Este site é uma demonstração acadêmica, sem reserva real em unidades de saúde.</p></details>
          <details className="mt-4"><summary className="cursor-pointer font-semibold text-brand-800">E se não aparecer nenhum horário?</summary><p className="mt-2 text-sm text-slate-600">A unidade pode ainda não ter informações suficientes para prever a espera. Você ainda pode consultar as unidades e, quando permitido, enviar um pedido sem escolher horário. Para UBS, consulte o agendamento diretamente na unidade.</p></details>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-14">
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-brand-100 p-6"><div><h2 className="text-xl font-bold text-slate-900">Primeira vez por aqui?</h2><p className="mt-1 text-sm text-slate-600">Veja para que serve cada opção e como usar, passo a passo.</p></div><Link to="/como-usar" className="btn-secondary">Conhecer todas as funções <ArrowRight className="h-4 w-4" /></Link></div>
        <h2 className="text-2xl font-bold text-slate-900">Acesso rápido de demonstração</h2>
        <p className="mt-2 text-slate-600">
          Escolha uma área para testar com dados de exemplo. Não precisa criar uma conta.
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
            Este é um projeto de demonstração. As orientações ajudam a entender os próximos passos, mas não substituem a avaliação de um profissional. Em emergência, ligue 192.
          </p>
        </div>
      </section>
    </div>
  );
}
