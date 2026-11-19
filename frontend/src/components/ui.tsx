import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { AlertCircle, Loader2, X } from "lucide-react";
import type { ReactNode } from "react";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function Button({
  children,
  variant = "primary",
  size="md",
  className,
  loading,
  disabled,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger" | "ghost" | "success";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}) {
  const variants = {
    primary: "bg-brand-600 text-white hover:bg-brand-700 focus:ring-brand-400",
    secondary: "bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 focus:ring-slate-300",
    danger: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-400",
    success: "bg-mint-600 text-white hover:bg-mint-700 focus:ring-mint-400",
    ghost: "text-slate-600 hover:bg-slate-100 focus:ring-slate-300",
  };
  const sizes = { sm: "px-3 py-1.5 text-xs", md: "px-4 py-2.5 text-sm", lg: "px-6 py-3.5 text-base" };
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none",
        variants[variant],
        sizes[size],
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" />}
      {children}
    </button>
  );
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("rounded-2xl border border-slate-100 bg-white p-5 shadow-soft", className)}>{children}</div>;
}

export function Label({ children, htmlFor }: { children: ReactNode; htmlFor?: string }) {
  return (
    <label htmlFor={htmlFor} className="mb-1.5 block text-sm font-medium text-slate-700">
      {children}
    </label>
  );
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={cn("input", props.className)} />;
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={cn("input", props.className)} />;
}

export function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={cn("input", props.className)} />;
}

export function Badge({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <span className={cn("badge", className)}>{children}</span>;
}

export function Alert({
  children,
  variant = "info",
  className,
}: {
  children: ReactNode;
  variant?: "info" | "warning" | "danger" | "success";
  className?: string;
}) {
  const variants = {
    info: "bg-brand-50 text-brand-800 border-brand-100",
    warning: "bg-amber-50 text-amber-800 border-amber-100",
    danger: "bg-red-50 text-red-800 border-red-100",
    success: "bg-mint-50 text-mint-800 border-mint-100",
  };
  return (
    <div className={cn("flex gap-3 rounded-xl border p-4 text-sm", variants[variant], className)}>
      <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
      <div className="space-y-1">{children}</div>
    </div>
  );
}

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn("h-6 w-6 animate-spin text-brand-600", className)} />;
}

export function Loading({ label = "Carregando..." }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-slate-500">
      <Spinner />
      <span className="text-sm">{label}</span>
    </div>
  );
}

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center">
      <p className="font-semibold text-slate-700">{title}</p>
      {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
    </div>
  );
}

export function StatCard({
  label,
  value,
  hint,
  tone = "brand",
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  tone?: "brand" | "mint" | "amber" | "red" | "violet";
}) {
  const tones = {
    brand: "from-brand-500 to-brand-700",
    mint: "from-mint-500 to-mint-700",
    amber: "from-amber-500 to-amber-600",
    red: "from-red-500 to-red-600",
    violet: "from-violet-500 to-violet-600",
  };
  return (
    <div className={cn("rounded-2xl bg-gradient-to-br p-5 text-white shadow-soft", tones[tone])}>
      <p className="text-sm/relaxed opacity-90">{label}</p>
      <p className="mt-2 text-3xl font-bold">{value}</p>
      {hint && <p className="mt-1 text-xs opacity-80">{hint}</p>}
    </div>
  );
}

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

export function Modal({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
      <div className="w-full max-w-lg rounded-2xl bg-white p-5 shadow-xl">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100">
            <X className="h-5 w-5" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function Table({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-100 bg-white shadow-soft">
      <table className="min-w-full divide-y divide-slate-100 text-sm">{children}</table>
    </div>
  );
}

export function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return <p className="mt-1 text-xs text-red-600">{message}</p>;
}
