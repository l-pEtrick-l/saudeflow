import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Loader2,
  PhoneCall,
  ShieldAlert,
} from "lucide-react";
import { api } from "../../lib/api";
import type { GuidanceResult, Question } from "../../lib/types";
import { Alert, Button, Card, Loading, Textarea } from "../../components/ui";
import { ScaleAnswer } from "../../components/ScaleAnswer";
import { PatientNav } from "../../components/PatientNav";

type Answers = Record<string, unknown>;

interface StartResponse {
  submission: { id: string; version_id: string };
  rule_set_version: string;
  questions: Question[];
}

export default function QuestionnairePage() {
  const navigate = useNavigate();
  const [start, setStart] = useState<StartResponse | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Answers>({});
  const [loading, setLoading] = useState(true);
  const [advancing, setAdvancing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<GuidanceResult | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<StartResponse>("/api/v1/questionnaires/active")
      .then((response) => {
        setStart(response);
        setQuestions(response.questions);
        setIndex(0);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const current = questions[index];
  const total = questions.length;
  const progress = total ? Math.round(((index + 1) / total) * 100) : 0;

  const visibleAnswered = useMemo(
    () => questions.filter((q) => answers[q.external_id] !== undefined).length,
    [questions, answers]
  );

  async function goNext(value: unknown) {
    if (!start || !current) return;
    const nextAnswers: Answers = { ...answers, [current.external_id]: value };
    setAnswers(nextAnswers);
    setAdvancing(true);
    setError("");
    try {
      const visible = await api.post<Question[]>(
        `/api/v1/questionnaires/versions/${start.submission.version_id}/next`,
        { answers: nextAnswers }
      );
      setQuestions(visible);
      const nextIndex = visible.findIndex(
        (q, i) => i > index && nextAnswers[q.external_id] === undefined
      );
      if (nextIndex === -1) {
        await finish(visible, nextAnswers);
      } else {
        setIndex(nextIndex);
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setAdvancing(false);
    }
  }

  async function finish(visible: Question[], nextAnswers: Answers) {
    if (!start) return;
    setSubmitting(true);
    try {
      const payload = visible
        .filter((q) => nextAnswers[q.external_id] !== undefined)
        .map((q) => ({ question_id: q.id, value: nextAnswers[q.external_id] }));
      await api.post(
        `/api/v1/questionnaires/submissions/${start.submission.id}/answers`,
        { answers: payload }
      );
      const guidance = await api.post<GuidanceResult>(
        `/api/v1/questionnaires/submissions/${start.submission.id}/complete`
      );
      setResult(guidance);
      if (!guidance.stop_flow) {
        navigate(`/paciente/resultado/${start.submission.id}`, { replace: true });
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  function goBack() {
    setIndex((value) => Math.max(0, value - 1));
  }

  if (loading) return <Loading label="Preparando o questionário..." />;
  if (error && !start) {
    return (
      <div className="mx-auto max-w-xl px-4 py-16">
        <Alert variant="danger">{error}</Alert>
      </div>
    );
  }

  if (result?.stop_flow) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-10">
        <div className="rounded-3xl bg-gradient-to-br from-red-600 to-red-700 p-8 text-white">
          <div className="flex items-center gap-3">
            <ShieldAlert className="h-10 w-10" />
            <h1 className="text-3xl font-extrabold">Procure socorro imediato</h1>
          </div>
          <p className="mt-4 text-white/90">{result.emergency_message}</p>
          <a
            href="tel:192"
            className="mt-6 flex items-center justify-center gap-3 rounded-2xl bg-white px-6 py-5 text-2xl font-extrabold text-red-700"
          >
            <PhoneCall className="h-7 w-7" /> Ligar SAMU 192
          </a>
          <p className="mt-3 text-center text-sm text-white/85">
            Não espere na fila online. A equipe do SAMU orienta qual ajuda procurar.
          </p>
          <Link to="/" className="mt-6 block text-center text-sm text-white/85 underline">
            Voltar ao início
          </Link>
        </div>
      </div>
    );
  }

  if (!current) return null;

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <PatientNav />
      <p className="mb-4 text-sm text-slate-600">Primeiro, conte o que está acontecendo. Depois, você verá onde buscar atendimento. As perguntas mudam conforme suas respostas.</p>
      <div className="mb-6">
        <div className="flex items-center justify-between text-sm text-slate-500">
          <span>
            Pergunta {index + 1} de {total}
          </span>
          <span>{progress}%</span>
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
          <div className="h-full rounded-full bg-brand-500 transition-all" style={{ width: `${progress}%` }} />
        </div>
      </div>

      <Alert variant="warning" className="mb-6">
        Situações graves exigem socorro imediato. Este formulário não é um serviço de emergência. Se
        houver risco de vida, ligue 192.
      </Alert>

      <Card>
        <h1 className="text-xl font-bold text-slate-900">{current.external_id === "description" ? "Quer contar um pouco mais? (opcional)" : current.text}</h1>
        {current.help_text && <p className="mt-1 text-sm text-slate-500">{current.help_text}</p>}

        <div className="mt-6">
          {current.type === "boolean" && (
            <div className="grid grid-cols-2 gap-3">
              <Button variant="success" size="lg" onClick={() => goNext(true)} disabled={advancing}>
                Sim
              </Button>
              <Button variant="secondary" size="lg" onClick={() => goNext(false)} disabled={advancing}>
                Não
              </Button>
            </div>
          )}

          {(current.type === "single_choice" || current.type === "body_region") && (
            <div className="space-y-2">
              {current.options.map((option) => (
                <button
                  key={option.id}
                  onClick={() => goNext(option.code)}
                  disabled={advancing}
                  className="flex w-full items-center justify-between rounded-xl border border-slate-200 px-4 py-3 text-left text-sm font-medium text-slate-700 transition hover:border-brand-300 hover:bg-brand-50 disabled:opacity-50"
                >
                  {option.label}
                  <ArrowRight className="h-4 w-4 text-slate-400" />
                </button>
              ))}
            </div>
          )}

          {current.type === "scale" && (
            <ScaleAnswer key={current.id} question={current} previous={answers[current.external_id]} disabled={advancing || submitting} onContinue={goNext} />
          )}

          {current.type === "text" && (
            <div>
              <Textarea
                id="free_text"
                rows={4}
                placeholder="Descreva brevemente, sem dados pessoais"
              />
              <Button
                className="mt-3"
                onClick={() => {
                  const el = document.getElementById("free_text") as HTMLTextAreaElement;
                  goNext(el.value);
                }}
                disabled={advancing}
              >
                Continuar
              </Button>
            </div>
          )}

          {(current.type === "number" || current.type === "time") && (
            <div>
              <input
                type={current.type === "number" ? "number" : "datetime-local"}
                id="value_input"
                className="input"
              />
              <Button
                className="mt-3"
                onClick={() => {
                  const el = document.getElementById("value_input") as HTMLInputElement;
                  goNext(el.value);
                }}
                disabled={advancing}
              >
                Continuar
              </Button>
            </div>
          )}
        </div>

        <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-4">
          <Button variant="ghost" onClick={goBack} disabled={index === 0 || advancing}>
            <ArrowLeft className="h-4 w-4" /> Voltar
          </Button>
          <span className="flex items-center gap-1.5 text-xs text-slate-400">
            <CheckCircle2 className="h-4 w-4" /> {visibleAnswered} resposta(s)
          </span>
        </div>
      </Card>

      {(advancing || submitting) && (
        <div className="mt-4 flex items-center justify-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" /> Processando...
        </div>
      )}
      {error && (
        <Alert variant="danger" className="mt-4">
          {error}
        </Alert>
      )}
    </div>
  );
}
