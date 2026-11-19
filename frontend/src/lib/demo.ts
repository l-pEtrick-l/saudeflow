/**
 * Acesso rápido de demonstração: login automático com contas de teste.
 * Usado na home, no topo do portal público e na tela de login.
 */

export type DemoRole = "patient" | "upa" | "hospital" | "admin";

export const DEMO_ACCOUNTS: Record<
  DemoRole,
  { email: string; password: string; label: string; home: string }
> = {
  patient: {
    email: "paciente@saudeflow.com.br",
    password: "Paciente@123",
    label: "Paciente",
    home: "/",
  },
  upa: {
    email: "recepcao.upa@saudeflow.com.br",
    password: "Upa@123",
    label: "UPA",
    home: "/upa",
  },
  hospital: {
    email: "hospital@saudeflow.com.br",
    password: "Hosp@123",
    label: "Visão Hospital",
    home: "/hospital",
  },
  admin: {
    email: "admin@saudeflow.com.br",
    password: "Admin@123",
    label: "Admin",
    home: "/admin",
  },
};

export async function demoLogin(role: DemoRole, redirectTo?: string): Promise<void> {
  const account = DEMO_ACCOUNTS[role];
  const response = await fetch("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: account.email, password: account.password }),
  });
  const data = await response.json();
  if (!response.ok || !data.access_token) {
    throw new Error(data?.error?.message || "Não foi possível entrar com a conta de demonstração.");
  }
  localStorage.setItem("sf_token", data.access_token);
  localStorage.setItem("sf_user", JSON.stringify(data.user));
  window.location.href = redirectTo || account.home;
}
