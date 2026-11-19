import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Shield, UserCheck, Users } from "lucide-react";
import { api } from "../../lib/api";
import type { Paginated } from "../../lib/types";
import { formatDateTime } from "../../lib/format";
import { Alert, Badge, Button, Card, Input, Label, Modal, PageHeader, Select, Table } from "../../components/ui";

interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  phone?: string | null;
  is_active: boolean;
  roles: string[];
  unit_ids: string[];
  created_at: string;
}

interface Role {
  id: string;
  name: string;
  description?: string | null;
}

export default function AdminUsers() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<AdminUser | null>(null);
  const [role, setRole] = useState("patient");
  const [unitId, setUnitId] = useState("");
  const [error, setError] = useState("");

  const { data, isLoading } = useQuery<Paginated<AdminUser>>({
    queryKey: ["admin-users", search],
    queryFn: () =>
      api.get(`/api/v1/users?page=1&page_size=50${search ? `&search=${encodeURIComponent(search)}` : ""}`),
  });

  const roles = useQuery<Role[]>({
    queryKey: ["roles"],
    queryFn: () => api.get("/api/v1/users/roles/list"),
  });

  const assign = useMutation({
    mutationFn: () =>
      api.post("/api/v1/users/roles", { user_id: selected?.id, role, unit_id: unitId || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      setSelected(null);
      setUnitId("");
    },
    onError: (err: Error) => setError(err.message),
  });

  const toggleActive = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      api.patch(`/api/v1/users/${id}`, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });

  const items = data?.data ?? [];

  return (
    <div>
      <PageHeader
        title="Usuários e papéis"
        subtitle="RBAC: admin, gestor, recepção, classificador, operador, hospital e paciente"
        actions={
          <Input
            placeholder="Buscar por nome ou e-mail"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-64"
          />
        }
      />

      {isLoading ? (
        <p className="text-sm text-slate-500">Carregando...</p>
      ) : (
        <Table>
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Nome</th>
              <th className="px-4 py-3">E-mail</th>
              <th className="px-4 py-3">Papéis</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Criado em</th>
              <th className="px-4 py-3 text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((user) => (
              <tr key={user.id}>
                <td className="px-4 py-3 font-semibold text-slate-900">{user.full_name}</td>
                <td className="px-4 py-3 text-slate-500">{user.email}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {user.roles.map((r) => (
                      <Badge key={r} className="bg-brand-50 text-brand-700">
                        {r}
                      </Badge>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <Badge className={user.is_active ? "bg-mint-50 text-mint-700" : "bg-red-50 text-red-700"}>
                    {user.is_active ? "Ativo" : "Inativo"}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-slate-500">{formatDateTime(user.created_at)}</td>
                <td className="px-4 py-3">
                  <div className="flex justify-end gap-1.5">
                    <Button variant="secondary" size="sm" onClick={() => setSelected(user)}>
                      <Shield className="h-3.5 w-3.5" /> Papéis
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleActive.mutate({ id: user.id, is_active: !user.is_active })}
                    >
                      <UserCheck className="h-3.5 w-3.5" />
                      {user.is_active ? "Desativar" : "Ativar"}
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      <Modal open={!!selected} onClose={() => setSelected(null)} title={`Papéis de ${selected?.full_name ?? ""}`}>
        <div className="space-y-4">
          <div className="flex flex-wrap gap-1.5">
            {selected?.roles.map((r) => (
              <Badge key={r} className="bg-brand-50 text-brand-700">
                {r}
              </Badge>
            ))}
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <Label>Papel</Label>
              <Select value={role} onChange={(e) => setRole(e.target.value)}>
                {(roles.data ?? []).map((r) => (
                  <option key={r.id} value={r.name}>
                    {r.name}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>Unidade (opcional)</Label>
              <Input
                placeholder="ID da unidade"
                value={unitId}
                onChange={(e) => setUnitId(e.target.value)}
              />
            </div>
          </div>
          {error && <Alert variant="danger">{error}</Alert>}
          <Button
            className="w-full"
            onClick={() => assign.mutate()}
            disabled={assign.isPending}
          >
            <Users className="h-4 w-4" /> Conceder papel
          </Button>
        </div>
      </Modal>
    </div>
  );
}
