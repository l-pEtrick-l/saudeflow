import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { lazy, Suspense, type ReactNode } from "react";
import { AppLayout } from "./components/layout/AppLayout";
import { PublicLayout } from "./components/layout/PublicLayout";
import { useAuth } from "./lib/auth";
import { Loading } from "./components/ui";

const HomePage = lazy(() => import("./pages/public/HomePage"));
const HelpPage = lazy(() => import("./pages/public/HelpPage"));
const UnitsPage = lazy(() => import("./pages/public/UnitsPage"));
const EmergencyPage = lazy(() => import("./pages/public/EmergencyPage"));
const LoginPage = lazy(() => import("./pages/auth/LoginPage"));
const RegisterPage = lazy(() => import("./pages/auth/RegisterPage"));
const QuestionnairePage = lazy(() => import("./pages/patient/QuestionnairePage"));
const ResultPage = lazy(() => import("./pages/patient/ResultPage"));
const TrackingPage = lazy(() => import("./pages/patient/TrackingPage"));
const PreAlertPage = lazy(() => import("./pages/patient/PreAlertPage"));
const ProfilePage = lazy(() => import("./pages/patient/ProfilePage"));
const UpaDashboard = lazy(() => import("./pages/upa/DashboardPage"));
const UpaRequests = lazy(() => import("./pages/upa/RequestsPage"));
const UpaQueue = lazy(() => import("./pages/upa/QueuePage"));
const UpaAlerts = lazy(() => import("./pages/upa/AlertsPage"));
const UpaCapacity = lazy(() => import("./pages/upa/CapacityPage"));
const HospitalDashboard = lazy(() => import("./pages/hospital/DashboardPage"));
const HospitalAlerts = lazy(() => import("./pages/hospital/AlertsPage"));
const HospitalHistory = lazy(() => import("./pages/hospital/HistoryPage"));
const AdminDashboard = lazy(() => import("./pages/admin/DashboardPage"));
const AdminUnits = lazy(() => import("./pages/admin/UnitsPage"));
const AdminUsers = lazy(() => import("./pages/admin/UsersPage"));
const AdminIntegrations = lazy(() => import("./pages/admin/IntegrationsPage"));
const AdminAudit = lazy(() => import("./pages/admin/AuditPage"));

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
    <Suspense fallback={<Loading label="Carregando página..." />}><Routes>
      <Route element={<PublicLayout />}>
        <Route index element={<HomePage />} />
        <Route path="como-usar" element={<HelpPage />} />
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
    </Routes></Suspense>
  );
}
