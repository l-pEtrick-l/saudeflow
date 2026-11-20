import { useState } from "react";
import { useForm } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2, Pencil, Plus, Power } from "lucide-react";
import { api } from "../../lib/api";
import type { Paginated, Unit } from "../../lib/types";
import { formatDateTime } from "../../lib/format";
import { Alert, Badge, Button, Card, FieldError, Input, Label, Modal, PageHeader, Select, Table, Textarea } from "../../components/ui";

interface UnitForm {
  name: string;
  type: "ubs" | "upa" | "hospital" | "emergency";
  cnes_code: string;
  city: string;
  state: string;
  street: string;
  number: string;
  neighborhood: string;
  postal_code: string;
  latitude: string;
  longitude: string;
  phone: string;
  is_simulated: boolean;
}

const emptyForm: UnitForm = {
  name: "",
  type: "upa",
  cnes_code: "",
  city: "",
  state: "",
  street: "",
  number: "",
  neighborhood: "",
  postal_code: "",
  latitude: "",
  longitude: "",
  phone: "",
  is_simulated: true,
};

export default function AdminUnits() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Unit | null>(null);
  const [error, setError] = useState("");
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<UnitForm>({ defaultValues: emptyForm });

  const { data, isLoading } = useQuery<Paginated<Unit>>({
    queryKey: ["admin-units"],
    queryFn: () => api.get("/api/v1/units?page=1&page_size=100"),
  });

  const create = useMutation({
    mutationFn: (values: UnitForm) =>
      api.post("/api/v1/units", {
        name: values.name,
        type: values.type,
        cnes_code: values.cnes_code || undefined,
        city: values.city || undefined,
        state: values.state || undefined,
        street: values.street || undefined,
        number: values.number || undefined,
        neighborhood: values.neighborhood || undefined,
        postal_code: values.postal_code || undefined,
        latitude: values.latitude ? Number(values.latitude) : undefined,
        longitude: values.longitude ? Number(values.longitude) : undefined,
        phone: values.phone || undefined,
        is_simulated: values.is_simulated,
        services: [],
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-units"] });
      setOpen(false);
      reset(emptyForm);
    },
    onError: (err: Error) => setError(err.message),
  });

  const toggle = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      api.post(`/api/v1/units/${id}/active?is_active=${active}`, {}),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-units"] }),
  });

  const items = data?.data ?? [];

  return (
    <div>
      <PageHeader
        title="Unidades"
        subtitle="Cadastro e configuração das unidades de saúde"
        actions={
          <Button
            onClick={() => {
              setEditing(null);
              reset(emptyForm);
              setOpen(true);
            }}
          >
            <Plus className="h-4 w-4" /> Nova unidade
          </Button>
        }
      />

      {isLoading ? (
        <p className="text-sm text-slate-500">Carregando...</p>
      ) : (
        <Table>
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Nome</th>
              <th className="px-4 py-3">Tipo</th>
              <th className="px-4 py-3">Cidade</th>
              <th className="px-4 py-3">Origem</th>
              <th className="px-4 py-3">Situação</th>
              <th className="px-4 py-3">Atualizada em</th>
              <th className="px-4 py-3 text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((unit) => (
              <tr key={unit.id}>
                <td className="px-4 py-3 font-semibold text-slate-900">{unit.name}</td>
                <td className="px-4 py-3 uppercase text-slate-600">{unit.type}</td>
                <td className="px-4 py-3 text-slate-500">
                  {unit.city || "—"} {unit.state ? `/ ${unit.state}` : ""}
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1">
                    <Badge className="bg-slate-100 text-slate-600">{unit.source}</Badge>
                    {unit.is_simulated && <Badge className="bg-amber-50 text-amber-700">simulada</Badge>}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <Badge className={unit.is_active ? "bg-mint-50 text-mint-700" : "bg-red-50 text-red-700"}>
                    {unit.is_active ? "Ativa" : "Inativa"}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-slate-500">{formatDateTime(unit.updated_at)}</td>
                <td className="px-4 py-3">
                  <div className="flex justify-end gap-1.5">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setEditing(unit);
                        reset({
                          name: unit.name,
                          type: unit.type,
                          cnes_code: unit.cnes_code ?? "",
                          city: unit.city ?? "",
                          state: unit.state ?? "",
                          street: unit.street ?? "",
                          number: unit.number ?? "",
                          neighborhood: unit.neighborhood ?? "",
                          postal_code: unit.postal_code ?? "",
                          latitude: unit.latitude != null ? String(unit.latitude) : "",
                          longitude: unit.longitude != null ? String(unit.longitude) : "",
                          phone: unit.phone ?? "",
                          is_simulated: unit.is_simulated,
                        });
                        setOpen(true);
                      }}
                    >
                      <Pencil className="h-3.5 w-3.5" /> Editar
                    </Button>
                    <Button
                      variant={unit.is_active ? "ghost" : "secondary"}
                      size="sm"
                      onClick={() => toggle.mutate({ id: unit.id, active: !unit.is_active })}
                    >
                      <Power className="h-3.5 w-3.5" />
                      {unit.is_active ? "Desativar" : "Ativar"}
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title={editing ? `Editar ${editing.name}` : "Nova unidade"}
      >
        <form
          className="space-y-4"
          onSubmit={handleSubmit((values) => {
            if (editing) {
              setError("Edição detalhada disponível na API; use a criação para novas unidades.");
              return;
            }
            create.mutate(values);
          })}
        >
          <div>
            <Label>Nome</Label>
            <Input {...register("name", { required: "Informe o nome" })} />
            <FieldError message={errors.name?.message} />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <Label>Tipo</Label>
              <Select {...register("type")}>
                <option value="ubs">UBS</option>
                <option value="upa">UPA</option>
                <option value="hospital">Hospital</option>
                <option value="emergency">Pronto-socorro</option>
              </Select>
            </div>
            <div>
              <Label>Código CNES (opcional)</Label>
              <Input {...register("cnes_code")} />
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <Label>Rua</Label>
              <Input {...register("street")} />
            </div>
            <div>
              <Label>Número</Label>
              <Input {...register("number")} />
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <Label>Bairro</Label>
              <Input {...register("neighborhood")} />
            </div>
            <div>
              <Label>Cidade</Label>
              <Input {...register("city")} />
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <Label>UF</Label>
              <Input {...register("state")} placeholder="SP" />
            </div>
            <div>
              <Label>CEP</Label>
              <Input {...register("postal_code")} />
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <Label>Latitude</Label>
              <Input {...register("latitude")} placeholder="-23.5505" />
            </div>
            <div>
              <Label>Longitude</Label>
              <Input {...register("longitude")} placeholder="-46.6333" />
            </div>
          </div>
          <div>
            <Label>Telefone</Label>
            <Input {...register("phone")} />
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" className="h-4 w-4 rounded border-slate-300 text-brand-600" {...register("is_simulated")} />
            Unidade simulada (demonstração)
          </label>
          {error && <Alert variant="danger">{error}</Alert>}
          <Button type="submit" loading={isSubmitting} className="w-full">
            <Building2 className="h-4 w-4" /> Salvar
          </Button>
        </form>
      </Modal>
    </div>
  );
}
