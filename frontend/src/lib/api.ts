const BASE = (import.meta.env.VITE_API_BASE as string) || "";

export class ApiError extends Error {
  status: number;
  code: string;
  details?: unknown;

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

function token() {
  return localStorage.getItem("sf_token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  const jwt = token();
  if (jwt) headers.Authorization = `Bearer ${jwt}`;

  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, { ...options, headers });
  } catch (error) {
    throw new ApiError(0, "network_error", "Não foi possível falar com o servidor. Verifique sua conexão.");
  }
  if (response.status === 204) return null as T;
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const err = body?.error || {};
    throw new ApiError(
      response.status,
      err.code || "error",
      err.message || "Erro inesperado",
      err.details
    );
  }
  return body as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(data ?? {}) }),
  patch: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(data ?? {}) }),
  put: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(data ?? {}) }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

export function wsUrl(channels: string[], jwt?: string | null) {
  const params = new URLSearchParams();
  params.set("channels", channels.join(","));
  const tokenValue = jwt === undefined ? token() : jwt;
  if (tokenValue) params.set("token", tokenValue);
  const httpBase = BASE || window.location.origin;
  const wsBase = httpBase.replace(/^http/, "ws");
  return `${wsBase}/api/v1/ws?${params.toString()}`;
}
