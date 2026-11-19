import { useForm } from "react-hook-form";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { HeartPulse, LogIn } from "lucide-react";
import { useAuth } from "../../lib/auth";
import { Button, Card, FieldError, Input, Label } from "../../components/ui";

interface LoginForm {
  email: string;
  password: string;
}

export function homeForRoles(roles: string[]) {
  if (roles.includes("admin")) return "/admin";
  if (roles.includes("hospital_staff")) return "/hospital";
  if (roles.some((r) => ["manager", "receptionist", "classifier", "operator"].includes(r)))
    return "/upa";
  return "/";
}

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: string } };
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<LoginForm>();

  const onSubmit = async (data: LoginForm) => {
    try {
      await login(data.email, data.password);
      const stored = localStorage.getItem("sf_user");
      const roles = stored ? (JSON.parse(stored).roles as string[]) : [];
      navigate(location.state?.from || homeForRoles(roles), { replace: true });
    } catch (error) {
      setError("root", { message: (error as Error).message });
    }
  };

  return (
    <div className="mx-auto flex max-w-md flex-col px-4 py-12">
      <div className="mb-6 text-center">
        <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600 text-white">
          <HeartPulse className="h-7 w-7" />
        </span>
        <h1 className="mt-4 text-2xl font-bold text-slate-900">Entrar no SaúdeFlow</h1>
        <p className="mt-1 text-sm text-slate-500">Acesse para acompanhar solicitações e pré-alertas.</p>
      </div>

      <Card>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label htmlFor="email">E-mail</Label>
            <Input id="email" type="email" {...register("email", { required: "Informe o e-mail" })} />
            <FieldError message={errors.email?.message} />
          </div>
          <div>
            <Label htmlFor="password">Senha</Label>
            <Input
              id="password"
              type="password"
              {...register("password", { required: "Informe a senha" })}
            />
            <FieldError message={errors.password?.message} />
          </div>
          <FieldError message={errors.root?.message} />
          <Button type="submit" loading={isSubmitting} className="w-full">
            <LogIn className="h-4 w-4" /> Entrar
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500">
          Não tem conta?{" "}
          <Link to="/cadastro" className="font-semibold text-brand-600 hover:underline">
            Cadastre-se
          </Link>
        </p>
      </Card>

      <div className="mt-6 rounded-2xl border border-slate-100 bg-slate-50 p-4 text-xs text-slate-500">
        <p className="font-semibold text-slate-600">Contas de demonstração</p>
        <p>paciente@saudeflow.com.br / Paciente@123</p>
        <p>recepcao.upa@saudeflow.com.br / Upa@123</p>
        <p>hospital@saudeflow.com.br / Hosp@123</p>
        <p>admin@saudeflow.com.br / Admin@123</p>
      </div>
    </div>
  );
}
