import { useForm } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2, Save } from "lucide-react";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import type { Capacity, Paginated } from "../../lib/types";
import { formatDateTime } from "../../lib/format";
import { Alert, Button, Card, FieldError, Input, Label, PageHeader, Table } from "../../components/ui";

interface CapacityForm {
  professionals_available: number;
  rooms_active: number;
  welcome_capacity: number;
  receiving_pre_registrations: boolean;
  exceptional_status: string;
  notes: string;
}

export default function UpaCapacity() {
  const { user } = useAuth();
  const unitId = user?.unit_ids?.[0];
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
    setError,
  } = useForm<CapacityForm>({
    defaultValues: {
      professionals_available: 0,
      rooms_active: 0,
      welcome_capacity: 0,
      receiving_pre_registrations: true,
      exceptional_status: "",
      notes: "",
    },
  });

  const { data } = useQuery<Paginated<Capacity>>({
    queryKey: ["capacity", unitId],
    queryFn: () => api.get(`/api/v1/units/${unitId}/capacity`),
    enabled: !!unitId,
  });

  const mutation = useMutation({
    mutationFn: (values: CapacityForm) =>
      api.post(`/api/v1/units/${unitId}/capacity`, {
        ...values,
        exceptional_status: values.exceptional_status || undefined,
        notes: values.notes || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["capacity"] });
      queryClient.invalidateQueries({ queryKey: ["queue-board"] });
      reset();
    },
    onError: (err: Error) => setError("root", { message: err.message }),
  });

  const history = data?.data ?? [];

  return (
    <div>
      <PageHeader
        title="Capacidade operacional"
        subtitle="Alterações afetam as estimativas exibidas ao paciente"
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="flex items-center gap-2 font-semibold text-slate-900">
            <Building2 className="h-5 w-5 text-brand-600" /> Nova capacidade
          </h2>
          <form
            className="mt-4 space-y-4"
            onSubmit={handleSubmit((values) => mutation.mutate(values))}
          >
            <div className="grid gap-3 sm:grid-cols-3">
              <div>
                <Label>Profissionais</Label>
                <Input
                  type="number"
                  min={0}
                  {...register("professionals_available", { required: true, min: 0 })}
                />
                <FieldError message={errors.professionals_available?.message} />
              </div>
              <div>
                <Label>Salas ativas</Label>
                <Input type="number" min={0} {...register("rooms_active", { required: true, min: 0 })} />
              </div>
              <div>
                <Label>Acolhimento</Label>
                <Input
                  type="number"
                  min={0}
                  {...register("welcome_capacity", { required: true, min: 0 })}
                />
              </div>
            </div>
            <div>
              <Label>Situação excepcional</Label>
              <Input placeholder="Ex.: pico de demanda, greve, manutenção" {...register("exceptional_status")} />
            </div>
            <div>
              <Label>Observações</Label>
              <Input {...register("notes")} />
            </div>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-slate-300 text-brand-600"
                {...register("receiving_pre_registrations")}
              />
              Recebendo pré-cadastros digitais
            </label>
            <FieldError message={errors.root?.message} />
            <Button type="submit" loading={isSubmitting}>
              <Save className="h-4 w-4" /> Salvar capacidade
            </Button>
          </form>
          {mutation.isSuccess && (
            <Alert variant="success" className="mt-4">
              Capacidade atualizada. As estimativas foram recalculadas.
            </Alert>
          )}
        </Card>

        <Card>
          <h2 className="font-semibold text-slate-900">Histórico</h2>
          {history.length === 0 ? (
            <p className="mt-3 text-sm text-slate-500">Sem registros.</p>
          ) : (
            <div className="mt-4">
              <Table>
                <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Data</th>
                    <th className="px-4 py-3">Prof.</th>
                    <th className="px-4 py-3">Salas</th>
                    <th className="px-4 py-3">Acolh.</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {history.map((item) => (
                    <tr key={item.id}>
                      <td className="px-4 py-3 text-slate-500">{formatDateTime(item.created_at)}</td>
                      <td className="px-4 py-3">{item.professionals_available}</td>
                      <td className="px-4 py-3">{item.rooms_active}</td>
                      <td className="px-4 py-3">{item.welcome_capacity}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
