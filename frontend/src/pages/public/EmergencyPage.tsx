import { Link } from "react-router-dom";
import { PhoneCall, Siren, Ambulance, ArrowRight, Info } from "lucide-react";
import { Alert, Card } from "../../components/ui";
import { useAuth } from "../../lib/auth";
import { demoLogin } from "../../lib/demo";

export default function EmergencyPage() {
  const { user } = useAuth();
  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <div className="rounded-3xl bg-gradient-to-br from-red-600 to-red-700 p-8 text-white shadow-soft">
        <div className="flex items-center gap-3">
          <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/15">
            <Siren className="h-8 w-8" />
          </span>
          <div>
            <h1 className="text-3xl font-extrabold">Emergência</h1>
            <p className="text-white/85">Se é uma emergência grave, ligue agora para o SAMU 192.</p>
          </div>
        </div>
        <a
          href="tel:192"
          className="mt-6 flex items-center justify-center gap-3 rounded-2xl bg-white px-6 py-5 text-2xl font-extrabold text-red-700 hover:bg-red-50"
        >
          <PhoneCall className="h-7 w-7" /> 192
        </a>
        <p className="mt-3 text-center text-sm text-white/85">
          A ligação é necessária para solicitar atendimento. O sistema não aciona ambulância nem simula
          o serviço oficial.
        </p>
      </div>

      <div className="mt-8 grid gap-5 md:grid-cols-2">
        <Card>
          <h2 className="flex items-center gap-2 text-lg font-bold text-slate-900">
            <PhoneCall className="h-5 w-5 text-red-600" /> Preciso de socorro imediato
          </h2>
          <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-slate-600">
            <li>Ligue para o SAMU 192.</li>
            <li>Informe o local, o que aconteceu e o estado da pessoa.</li>
            <li>Siga as orientações do atendente.</li>
            <li>Não se desloque sozinho se estiver em risco.</li>
          </ol>
          <a href="tel:192" className="btn-danger mt-4 w-full">
            <PhoneCall className="h-4 w-4" /> Ligar SAMU 192
          </a>
        </Card>

        <Card>
          <h2 className="flex items-center gap-2 text-lg font-bold text-slate-900">
            <Ambulance className="h-5 w-5 text-brand-600" /> Já estou a caminho de uma unidade
          </h2>
          <p className="mt-3 text-sm text-slate-600">
            Você pode enviar um pré-alerta digital com informações preliminares para a unidade. Isso
            não substitui o SAMU nem garante atendimento.
          </p>
          <Link to="/paciente/pre-alerta" className="btn-primary mt-4 w-full">
            Enviar pré-alerta <ArrowRight className="h-4 w-4" />
          </Link>
          {!user && (
            <button
              type="button"
              onClick={() => demoLogin("patient", "/paciente/pre-alerta")}
              className="mt-2 w-full rounded-xl border-2 border-dashed border-mint-300 bg-mint-50 px-4 py-3 text-sm font-bold text-mint-700 transition hover:bg-mint-100"
            >
              Entrar como usuário teste (sem cadastro)
            </button>
          )}
        </Card>
      </div>

      <Alert variant="warning" className="mt-6">
        <p className="font-semibold">O que o sistema não faz</p>
        <p>
          Não substitui o serviço de emergência, não aciona ambulância, não define destino hospitalar e
          não oferece fila virtual como alternativa ao socorro. A regulação médica decide sobre ambulância
          e unidade de destino.
        </p>
      </Alert>

      <Card className="mt-6">
        <h3 className="flex items-center gap-2 font-semibold text-slate-900">
          <Info className="h-5 w-5 text-brand-600" /> Sinais que exigem socorro imediato
        </h3>
        <div className="mt-3 flex flex-wrap gap-2">
          {[
            "Ferimento por arma branca ou de fogo",
            "Sangramento intenso",
            "Perda de consciência",
            "Convulsão",
            "Suspeita de AVC",
            "Dor torácica com suspeita de evento grave",
            "Dificuldade respiratória grave",
            "Acidente grave",
          ].map((item) => (
            <span key={item} className="badge bg-red-50 text-red-700">
              {item}
            </span>
          ))}
        </div>
      </Card>
    </div>
  );
}
