import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

const STORAGE_KEY = "fwpa.auth.session";

export interface AuthUser {
  email: string;
  displayName: string;
  role: string;
  department: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const DEMO_EMAIL = (import.meta.env.VITE_DEMO_EMAIL as string | undefined) ?? "hod@aiml.edu";
const DEMO_PASSWORD =
  (import.meta.env.VITE_DEMO_PASSWORD as string | undefined) ?? "aiml2026";

function readStoredUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => readStoredUser());

  const login = useCallback(async (email: string, password: string) => {
    // Frontend gate for Capstone demo. Replace with JWT /api/v1/auth/login when backend auth lands.
    await new Promise((resolve) => setTimeout(resolve, 450));
    const normalized = email.trim().toLowerCase();
    if (normalized !== DEMO_EMAIL.toLowerCase() || password !== DEMO_PASSWORD) {
      throw new Error("Invalid email or password. Use the demo administrator credentials.");
    }
    const nextUser: AuthUser = {
      email: DEMO_EMAIL,
      displayName: "Department Administrator",
      role: "HOD / Planner",
      department: "AIML",
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(nextUser));
    setUser(nextUser);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: user !== null,
      login,
      logout,
    }),
    [user, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}

export const demoCredentials = {
  email: DEMO_EMAIL,
  password: DEMO_PASSWORD,
};
