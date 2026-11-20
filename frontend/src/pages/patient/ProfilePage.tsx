import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Bell, ClipboardList, User as UserIcon } from "lucide-react";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import type { Paginated, Request } from "../../lib/types";
import { formatDateTime, REQUEST_STATUS, ROLE_LABEL } from "../../lib/format";
import { Badge, Button, Card, EmptyState, Input, Label, PageHeader, Select, Table } from "../../components/ui";

interface NotificationItem {
  id: string;
  title: string;
  body?: string | null;
  type: string;
  is_read: boolean;
  created_at: string;
}

export default function ProfilePage() {
  const { user } = useAuth();
  const [search, setSearch] = useState("");

  const requests = useQuery<Paginated<Request>>({
    queryKey: ["my-requests", search],
    queryFn: () =>
      api.get(`/api/v1/requests?page=1&page_size=20${search ? `&status=${search}` : ""}`),
  });

  const notifications = useQuery<Paginated<NotificationItem>>({
    queryKey: ["my-notifications"],
    queryFn: () => api.get("/api/v1/notifications?page=1&page_size=20"),
  });

  const items = requests.data?.data ?? [];
  const notificationsItems = notifications.data?.data ?? [];

  return (
    <div>
      <PageHeader
        title="Minha conta"
        subtitle={user?.email}
        actions={
          <Link to="/atendimento" className="btn-primary">
            Novo pedido
          </Link>
        }
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card>
          <div className="flex items-center gap-3">
            <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
              <UserIcon className="h-6 w-6" />
            </span>
            <div>
              <p className="font-semibold text-slate-900">{user?.full_name}</p>
              <p className="text-sm text-slate-500">{user?.phone || "Sem telefone"}</p>
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {user?.roles.map((role) => (
              <Badge key={role} className="bg-brand-50 text-brand-700">
                {ROLE_LABEL[role] ?? role}
              </Badge>
            ))}
          </div>
          {user?.unit_ids?.length ? (
            <p className="mt-3 text-xs text-slate-500">
              Unidades vinculadas: {user.unit_ids.length}
            </p>
          ) : null}
        </Card>

        <Card className="lg:col-span-2">
          <h2 className="flex items-center gap-2 font-semibold text-slate-900">
            <Bell className="h-5 w-5 text-brand-600" /> Notificações
          </h2>
          {notificationsItems.length === 0 ? (
            <p className="mt-3 text-sm text-slate-500">Nenhuma notificação por aqui.</p>
          ) : (
            <ul className="mt-3 space-y-3">
              {notificationsItems.map((notification) => (
                <li
                  key={notification.id}
                  className="rounded-xl border border-slate-100 p-3 text-sm"
                >
                  <p className="font-medium text-slate-800">{notification.title}</p>
                  {notification.body && <p className="text-slate-500">{notification.body}</p>}
                  <p className="mt-1 text-xs text-slate-400">
                    {formatDateTime(notification.created_at)}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Card className="mt-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="flex items-center gap-2 font-semibold text-slate-900">
            <ClipboardList className="h-5 w-5 text-brand-600" /> Meus pedidos
          </h2>
          <div className="flex gap-2">
            <Select
              aria-label="Filtrar pedidos pela situação"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-60"
            ><option value="">Todas as situações</option>{Object.entries(REQUEST_STATUS).map(([value, item]) => <option key={value} value={value}>{item.label}</option>)}</Select>
          </div>
        </div>

        {items.length === 0 ? (
          <div className="mt-4">
            <EmptyState
              title="Nenhum pedido"
              description="Inicie pelo botão Novo pedido."
            />
          </div>
        ) : (
          <div className="mt-4">
            <Table>
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">Protocolo</th>
                  <th className="px-4 py-3">Unidade</th>
                  <th className="px-4 py-3">Situação</th>
                  <th className="px-4 py-3">Enviado em</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((request) => (
                  <tr key={request.id}>
                    <td className="px-4 py-3 font-semibold text-brand-700">{request.protocol}</td>
                    <td className="px-4 py-3">{request.unit_name || "—"}</td>
                    <td className="px-4 py-3">
                      <Badge className={REQUEST_STATUS[request.status]?.tone}>
                        {request.status_label}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-slate-500">
                      {formatDateTime(request.created_at)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link to={`/paciente/protocolo/${request.protocol}`} className="text-sm font-semibold text-brand-600 hover:underline">
                        Acompanhar
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </div>
        )}
      </Card>
    </div>
  );
}
