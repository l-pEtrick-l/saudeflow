import { useState } from "react";
import type { Question } from "../lib/types";
import { Button } from "./ui";

export function ScaleAnswer({ question, previous, disabled, onContinue }: {
  question: Question;
  previous?: unknown;
  disabled: boolean;
  onContinue: (value: number | undefined) => void;
}) {
  const temperature = question.external_id === "febre_temperatura";
  const min = Number(question.options[0]?.code ?? 0);
  const max = Number(question.options[question.options.length - 1]?.code ?? 10);
  const [value, setValue] = useState(typeof previous === "number" ? previous : min);
  const [chosen, setChosen] = useState(typeof previous === "number");
  const label = temperature ? `${value.toFixed(1).replace(".", ",")} °C` : `${value} de ${max}`;
  const id = `scale-${question.id}`;

  return <div>
    <label htmlFor={id} className="label">{temperature ? "Temperatura medida no termômetro" : "Quanto está doendo?"}</label>
    <output htmlFor={id} className="my-4 block text-center text-4xl font-extrabold text-brand-700" aria-live="polite">{label}</output>
    <input id={id} type="range" min={min} max={max} step={temperature ? 0.1 : 1}
      value={value} disabled={disabled} aria-valuetext={label} className="w-full accent-brand-600"
      onChange={event => { setValue(Number(event.target.value)); setChosen(true); }} />
    <div className="mt-1 flex justify-between text-sm text-slate-500"><span>{min}{temperature ? " °C" : " · Sem dor"}</span><span>{max}{temperature ? " °C" : " · Dor muito forte"}</span></div>
    <p className="mt-3 text-sm text-slate-600">{temperature ? "Arraste a barra até o valor que você mediu. O número acima acompanha sua escolha." : "Arraste a barra. Quanto maior o número, mais forte a dor."}</p>
    <div className="mt-4 flex flex-wrap gap-3">
      <Button disabled={disabled || (temperature && !chosen)} onClick={() => onContinue(value)}>Continuar</Button>
      {temperature && <Button variant="secondary" disabled={disabled} onClick={() => onContinue(undefined)}>Não medi a temperatura</Button>}
    </div>
  </div>;
}
