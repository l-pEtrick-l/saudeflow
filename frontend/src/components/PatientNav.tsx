import { Link } from "react-router-dom";

export function PatientNav() {
  return <nav aria-label="Ajuda e navegação" className="mb-5 flex flex-wrap gap-4 text-sm text-brand-700">
    <Link to="/" className="underline">Início</Link>
    <Link to="/como-usar" className="underline">Como usar</Link>
    <Link to="/paciente/conta" className="underline">Meus pedidos</Link>
  </nav>;
}
