import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { UserPlus } from "lucide-react";
import { useAuth } from "../../lib/auth";
import { Button, Card, FieldError, Input, Label } from "../../components/ui";
import { homeForRoles } from "./LoginPage";

interface RegisterForm {
  full_name: string;
  email: string;
  phone: string;
  password: string;
  confirm: string;
}

export default function RegisterPage() {
  const { register: signup } = useAuth();
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<RegisterForm>();

  const onSubmit = async (data: RegisterForm) => {
    try {
      await signup({
        full_name: data.full_name,
        email: data.email,
        phone: data.phone || undefined,
        password: data.password,
      });
      localStorage.getItem("sf_user");
      navigate(homeForRoles(["patient"]), { replace: true });
    } catch (error) {
      setError("root", { message: (error as Error).message });
    }
  };

  return (
    <div className="mx-auto max-w-md px-4 py-12">
      <Card>
        <h1 className="text-2xl font-bold text-slate-900">Criar conta</h1>
        <p className="mt-1 text-sm text-slate-500">
          Você pode responder ao questionário sem cadastro. A conta serve para acompanhar solicitações.
        </p>
        <form onSubmit={handleSubmit(onSubmit)} className="mt-5 space-y-4">
          <div>
            <Label htmlFor="full_name">Nome completo</Label>
            <Input
              id="full_name"
              {...register("full_name", { required: "Informe seu nome", minLength: 3 })}
            />
            <FieldError message={errors.full_name?.message} />
          </div>
          <div>
            <Label htmlFor="email">E-mail</Label>
            <Input id="email" type="email" {...register("email", { required: "Informe o e-mail" })} />
            <FieldError message={errors.email?.message} />
          </div>
          <div>
            <Label htmlFor="phone">Telefone (opcional)</Label>
            <Input id="phone" {...register("phone")} />
          </div>
          <div>
            <Label htmlFor="password">Senha</Label>
            <Input
              id="password"
              type="password"
              {...register("password", {
                required: "Informe a senha",
                minLength: { value: 8, message: "Mínimo de 8 caracteres" },
              })}
            />
            <FieldError message={errors.password?.message} />
          </div>
          <div>
            <Label htmlFor="confirm">Confirmar senha</Label>
            <Input
              id="confirm"
              type="password"
              {...register("confirm", {
                required: "Confirme a senha",
                validate: (value) => value === watch("password") || "As senhas não conferem",
              })}
            />
            <FieldError message={errors.confirm?.message} />
          </div>
          <FieldError message={errors.root?.message} />
          <Button type="submit" loading={isSubmitting} className="w-full">
            <UserPlus className="h-4 w-4" /> Criar conta
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500">
          Já tem conta?{" "}
          <Link to="/login" className="font-semibold text-brand-600 hover:underline">
            Entrar
          </Link>
        </p>
      </Card>
    </div>
  );
}
