import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import type { ReactNode } from "react";
import { AppLayout } from "./components/layout/AppLayout";
import { PublicLayout } from "./components/layout/PublicLayout";
import { useAuth } from "./lib/auth";
import { Loading } from "./components/ui";

import HomePage from "./pages/public/HomePage";
import UnitsPage from "./pages/public/UnitsPage";
import EmergencyPage from "./pages/public/EmergencyPage";
import LoginPage from "./pages/auth/LoginPage";
import RegisterPage from "./pages/auth/RegisterPage";
import QuestionnairePage from "./pages/patient/QuestionnairePage";
import ResultPage from "./pages/patient/ResultPage";
import TrackingPage from "./pages/patient/TrackingPage";
import PreAlertPage from "./pages/patient/PreAlertPage";
import ProfilePage from "./pages/patient/ProfilePage";
import UpaDashboard from "./pages/upa/DashboardPage";
import UpaRequests from "./pages/upa/RequestsPage";
import UpaQueue from "./pages/upa/QueuePage";
import UpaAlerts from "./pages/upa/AlertsPage";
import UpaCapacity from "./pages/upa/CapacityPage";
import HospitalDashboard from "./pages/hospital/DashboardPage";
import HospitalAlerts from "./pages/hospital/AlertsPage";
import HospitalHistory from "./pages/hospital/HistoryPage";
import AdminDashboard from "./pages/admin/DashboardPage";
import AdminUnits from "./pages/admin/UnitsPage";
import AdminUsers from "./pages/admin/UsersPage";
import AdminIntegrations from "./pages/admin/IntegrationsPage";
import AdminAudit from "./pages/admin/AuditPage";

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <Loading label="Verificando acesso..." />;
  if (!user) return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  return <>{children}</>;
}

function RequireRoles({ roles, children }: { roles: string[]; children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <Loading label="Verificando permissões..." />;
  if (!user) return <Navigate to="/login" replace />;
  if (!user.roles.some((role) => roles.includes(role))) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route index element={<HomePage />} />
        <Route path="unidades" element={<UnitsPage />} />
        <Route path="emergencia" element={<EmergencyPage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="cadastro" element={<RegisterPage />} />
        <Route path="acompanhar" element={<TrackingPage />} />
      </Route>

      <Route
        path="atendimento"
        element={
          <RequireAuth>
            <QuestionnairePage />
          </RequireAuth>
        }
      />
      <Route
        path="paciente/resultado/:submissionId"
        element={
          <RequireAuth>
            <ResultPage />
          </RequireAuth>
        }
      />
      <Route
        path="paciente/protocolo/:protocol"
        element={
          <RequireAuth>
            <TrackingPage />
          </RequireAuth>
        }
      />
      <Route
        path="paciente/pre-alerta"
        element={
          <RequireAuth>
            <PreAlertPage />
          </RequireAuth>
        }
      />

      <Route
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route path="paciente/conta" element={<ProfilePage />} />
        <Route
          path="upa/*"
          element={
            <RequireRoles roles={["manager", "receptionist", "classifier", "operator", "admin"]}>
              <Routes>
                <Route index element={<UpaDashboard />} />
                <Route path="solicitacoes" element={<UpaRequests />} />
                <Route path="fila" element={<UpaQueue />} />
                <Route path="alertas" element={<UpaAlerts />} />
                <Route path="capacidade" element={<UpaCapacity />} />
              </Routes>
            </RequireRoles>
          }
        />
        <Route
          path="hospital/*"
          element={
            <RequireRoles roles={["hospital_staff", "admin"]}>
              <Routes>
                <Route index element={<HospitalDashboard />} />
                <Route path="alertas" element={<HospitalAlerts />} />
                <Route path="historico" element={<HospitalHistory />} />
              </Routes>
            </RequireRoles>
          }
        />
        <Route
          path="admin/*"
          element={
            <RequireRoles roles={["admin"]}>
              <Routes>
                <Route index element={<AdminDashboard />} />
                <Route path="unidades" element={<AdminUnits />} />
                <Route path="usuarios" element={<AdminUsers />} />
                <Route path="integracoes" element={<AdminIntegrations />} />
                <Route path="auditoria" element={<AdminAudit />} />
              </Routes>
            </RequireRoles>
          }
        />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
