import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api } from "./api";

export type Role =
  | "admin"
  | "manager"
  | "receptionist"
  | "classifier"
  | "operator"
  | "hospital_staff"
  | "patient";

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone?: string | null;
  roles: Role[];
  unit_ids: string[];
}

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    email: string;
    password: string;
    full_name: string;
    phone?: string;
  }) => Promise<void>;
  logout: () => void;
  hasRole: (...roles: Role[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("sf_user");
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        localStorage.removeItem("sf_user");
      }
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await api.post<{
      access_token: string;
      user: User;
    }>("/api/v1/auth/login", { email, password });
    localStorage.setItem("sf_token", response.access_token);
    localStorage.setItem("sf_user", JSON.stringify(response.user));
    setUser(response.user);
  }, []);

  const register = useCallback(
    async (data: { email: string; password: string; full_name: string; phone?: string }) => {
      const response = await api.post<{
        access_token: string;
        user: User;
      }>("/api/v1/auth/register", data);
      localStorage.setItem("sf_token", response.access_token);
      localStorage.setItem("sf_user", JSON.stringify(response.user));
      setUser(response.user);
    },
    []
  );

  const logout = useCallback(() => {
    localStorage.removeItem("sf_token");
    localStorage.removeItem("sf_user");
    setUser(null);
  }, []);

  const hasRole = useCallback(
    (...roles: Role[]) => !!user && user.roles.some((role) => roles.includes(role)),
    [user]
  );

  const value = useMemo(
    () => ({ user, loading, login, register, logout, hasRole }),
    [user, loading, login, register, logout, hasRole]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth deve ser usado dentro de AuthProvider");
  return context;
}
