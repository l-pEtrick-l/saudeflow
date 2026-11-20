import { useState } from "react";
import { Building2, HeartPulse, Hospital, Menu, Shield, UserRound } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { DEMO_ACCOUNTS, demoLogin, type DemoRole } from "../../lib/demo";

export function PublicLayout() {
  const [loading, setLoading] = useState<DemoRole | null>(null);
  const [error, setError] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);

  async function quickLogin(role: DemoRole) {
    setLoading(role);
    setError("");
    try {
      await demoLogin(role);
    } catch (err) {
      setError((err as Error).message);
      setLoading(null);
    }
  }

  const quickButtons: { role: DemoRole; icon: React.ReactNode }[] = [
    { role: "patient", icon: <UserRound className="h-3.5 w-3.5" /> },
    { role: "upa", icon: <Building2 className="h-3.5 w-3.5" /> },
    { role: "hospital", icon: <Hospital className="h-3.5 w-3.5" /> },
    { role: "admin", icon: <Shield className="h-3.5 w-3.5" /> },
  ];

  return (
    <div className="min-h-full bg-white">
      <div className="bg-slate-900 text-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-1.5 px-4 py-1.5 text-xs">
          <span className="mr-1 text-white/60">Acesso rápido (demonstração):</span>
          {quickButtons.map(({ role, icon }) => (
            <button
              key={role}
              onClick={() => quickLogin(role)}
              disabled={loading !== null}
              className="inline-flex items-center gap-1 rounded-full bg-white/10 px-2.5 py-1 font-medium text-white/90 transition hover:bg-white/20 disabled:opacity-50"
            >
              {icon}
              {DEMO_ACCOUNTS[role].label}
            </button>
          ))}
        </div>
        {error && (
          <p className="mx-auto max-w-6xl px-4 pb-1.5 text-xs text-red-300">{error}</p>
        )}
      </div>

      <header className="sticky top-0 z-30 border-b border-slate-100 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <NavLink to="/" className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white">
              <HeartPulse className="h-5 w-5" />
            </span>
            <span className="text-lg font-bold text-slate-900">SaúdeFlow</span>
          </NavLink>
          <nav className="hidden items-center gap-1 sm:flex">
            <NavLink to="/como-usar" className="rounded-lg px-3 py-2 text-sm font-medium text-brand-700 hover:bg-brand-50">Como usar</NavLink>
            <NavLink to="/unidades" className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100">
              Unidades
            </NavLink>
            <button
              onClick={() => quickLogin("hospital")}
              className="inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-violet-700 hover:bg-violet-50"
            >
              <Hospital className="h-4 w-4" /> Área do hospital
            </button>
            <NavLink to="/emergencia" className="rounded-lg px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50">
              Emergência
            </NavLink>
            <NavLink to="/login" className="btn-primary ml-2">
              Entrar
            </NavLink>
          </nav>
          <button type="button" className="rounded-lg p-2 sm:hidden" aria-label="Menu" aria-expanded={menuOpen} aria-controls="public-menu" onClick={() => setMenuOpen(!menuOpen)}><Menu className="h-6 w-6" /></button>
        </div>
        {menuOpen && <nav id="public-menu" aria-label="Menu principal" className="flex flex-col gap-1 border-t border-slate-100 px-4 pb-3 sm:hidden">
          {[["/como-usar", "Como usar"], ["/unidades", "Unidades de saúde"], ["/acompanhar", "Acompanhar meu pedido"], ["/paciente/pre-alerta", "Avisar que estou a caminho"], ["/emergencia", "Emergência"], ["/login", "Entrar"]].map(([to, label]) => <NavLink key={to} to={to} onClick={() => setMenuOpen(false)} className="rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">{label}</NavLink>)}
        </nav>}
      </header>
      <main>
        <Outlet />
      </main>
      <footer className="border-t border-slate-100 bg-slate-50 py-6 text-center text-xs text-slate-500">
        <p className="font-semibold text-slate-600">SaúdeFlow — demonstração acadêmica</p>
        <p className="mx-auto mt-1 max-w-2xl px-4">
          Este projeto é uma demonstração. Não envia pedidos para unidades reais nem substitui atendimento médico ou o SAMU 192.
        </p>
        <NavLink to="/como-usar" className="mt-2 inline-block text-brand-700 underline">Entenda cada função do site</NavLink>
      </footer>
    </div>
  );
}
