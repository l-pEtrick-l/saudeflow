import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Activity,
  Bell,
  Building2,
  ClipboardList,
  HeartPulse,
  CircleHelp,
  LayoutDashboard,
  LogOut,
  Menu,
  Siren,
  Users,
  X,
} from "lucide-react";
import { useState } from "react";
import { useAuth } from "../../lib/auth";
import { RealtimeBadge, useRealtime } from "../../lib/ws";
import { cn } from "../ui";

const navByRole: Record<string, { to: string; label: string; icon: React.ReactNode }[]> = {
  patient: [
    { to: "/", label: "Início", icon: <LayoutDashboard className="h-4 w-4" /> },
    { to: "/atendimento", label: "Preciso de atendimento", icon: <HeartPulse className="h-4 w-4" /> },
    { to: "/unidades", label: "Unidades", icon: <Building2 className="h-4 w-4" /> },
    { to: "/emergencia", label: "Emergência", icon: <Siren className="h-4 w-4" /> },
    { to: "/acompanhar", label: "Acompanhar meu pedido", icon: <ClipboardList className="h-4 w-4" /> },
  ],
  upa: [
    { to: "/upa", label: "Resumo do dia", icon: <LayoutDashboard className="h-4 w-4" /> },
    { to: "/upa/solicitacoes", label: "Pedidos de atendimento", icon: <ClipboardList className="h-4 w-4" /> },
    { to: "/upa/fila", label: "Fila online", icon: <Activity className="h-4 w-4" /> },
    { to: "/upa/alertas", label: "Avisos de chegada", icon: <Bell className="h-4 w-4" /> },
    { to: "/upa/capacidade", label: "Equipe e estrutura", icon: <Building2 className="h-4 w-4" /> },
  ],
  hospital: [
    { to: "/hospital", label: "Resumo do dia", icon: <LayoutDashboard className="h-4 w-4" /> },
    { to: "/hospital/alertas", label: "Avisos de chegada", icon: <Bell className="h-4 w-4" /> },
    { to: "/hospital/historico", label: "Histórico de avisos", icon: <ClipboardList className="h-4 w-4" /> },
  ],
  admin: [
    { to: "/admin", label: "Visão geral", icon: <LayoutDashboard className="h-4 w-4" /> },
    { to: "/admin/unidades", label: "Unidades", icon: <Building2 className="h-4 w-4" /> },
    { to: "/admin/usuarios", label: "Usuários e acessos", icon: <Users className="h-4 w-4" /> },
    { to: "/admin/integracoes", label: "Dados de outras fontes", icon: <Activity className="h-4 w-4" /> },
  ],
};

export function AppLayout() {
  const { user, logout, hasRole } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const { status } = useRealtime([], () => {});

  let group: keyof typeof navByRole = "patient";
  if (hasRole("admin")) group = "admin";
  else if (hasRole("hospital_staff")) group = "hospital";
  else if (hasRole("manager", "receptionist", "classifier", "operator")) group = "upa";

  const items = [...navByRole[group],
    ...(group === "admin" ? [{ to: "/admin/auditoria", label: "Histórico de alterações", icon: <ClipboardList className="h-4 w-4" /> }] : []),
    { to: "/como-usar", label: "Como usar", icon: <CircleHelp className="h-4 w-4" /> },
  ];

  return (
    <div className="min-h-full bg-slate-50">
      <header className="sticky top-0 z-30 border-b border-slate-100 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <button aria-label="Abrir menu" aria-expanded={open} className="rounded-lg p-2 hover:bg-slate-100 lg:hidden" onClick={() => setOpen(true)}>
              <Menu className="h-5 w-5" />
            </button>
            <NavLink to="/" className="flex items-center gap-2">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white">
                <HeartPulse className="h-5 w-5" />
              </span>
              <span className="text-lg font-bold text-slate-900">SaúdeFlow</span>
            </NavLink>
          </div>
          <div className="flex items-center gap-3">
            <RealtimeBadge status={status} />
            <span className="hidden text-sm text-slate-500 sm:block">{user?.full_name}</span>
            <button
              className="btn-ghost px-3 py-2"
              onClick={() => {
                logout();
                navigate("/login");
              }}
            >
              <LogOut className="h-4 w-4" /> Sair
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto flex max-w-7xl gap-6 px-4 py-6">
        <aside className="hidden w-60 shrink-0 lg:block">
          <nav className="sticky top-20 space-y-1">
            {items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition",
                    isActive
                      ? "bg-brand-50 text-brand-700"
                      : "text-slate-600 hover:bg-slate-100"
                  )
                }
              >
                {item.icon}
                {item.label}
              </NavLink>
            ))}
          </nav>
        </aside>

        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </div>

      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-slate-900/40" onClick={() => setOpen(false)} />
          <div className="absolute left-0 top-0 h-full w-64 bg-white p-4 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <span className="font-bold">Menu</span>
              <button aria-label="Fechar menu" onClick={() => setOpen(false)} className="rounded-lg p-1 hover:bg-slate-100">
                <X className="h-5 w-5" />
              </button>
            </div>
            <nav className="space-y-1">
              {items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-100"
                >
                  {item.icon}
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
        </div>
      )}
    </div>
  );
}
