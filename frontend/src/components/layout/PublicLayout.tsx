import { HeartPulse, Menu } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

export function PublicLayout() {
  return (
    <div className="min-h-full bg-white">
      <header className="sticky top-0 z-30 border-b border-slate-100 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <NavLink to="/" className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white">
              <HeartPulse className="h-5 w-5" />
            </span>
            <span className="text-lg font-bold text-slate-900">SaúdeFlow</span>
          </NavLink>
          <nav className="hidden items-center gap-1 sm:flex">
            <NavLink to="/unidades" className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100">
              Unidades
            </NavLink>
            <NavLink to="/emergencia" className="rounded-lg px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50">
              Emergência
            </NavLink>
            <NavLink to="/login" className="btn-primary ml-2">
              Entrar
            </NavLink>
          </nav>
          <Menu className="h-6 w-6 sm:hidden" />
        </div>
      </header>
      <main>
        <Outlet />
      </main>
      <footer className="border-t border-slate-100 bg-slate-50 py-6 text-center text-xs text-slate-500">
        <p className="font-semibold text-slate-600">SaúdeFlow — demonstração acadêmica</p>
        <p className="mx-auto mt-1 max-w-2xl px-4">
          Não substitui atendimento médico, SAMU 192, regulação ou prontuários oficiais.
          Dados de demonstração; integrações externas exibidas como cache.
        </p>
      </footer>
    </div>
  );
}
