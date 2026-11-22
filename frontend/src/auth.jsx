import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { apiRequest, setUnauthorizedHandler } from "./api.js";

const STORAGE_KEY = "careerprep.session";
const AuthContext = createContext(null);

function loadSession() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) ?? null;
  } catch {
    return null;
  }
}

function saveSession(session) {
  try {
    if (session) localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* storage unavailable: session lasts until the tab closes */
  }
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(loadSession); // { token, user } or null
  const [checking, setChecking] = useState(Boolean(loadSession()));

  const clear = useCallback(() => {
    saveSession(null);
    setSession(null);
  }, []);

  useEffect(() => setUnauthorizedHandler(clear), [clear]);

  // Confirm a stored token is still valid when the app opens.
  useEffect(() => {
    const stored = loadSession();
    if (!stored) return;
    apiRequest("/api/auth/me", { token: stored.token })
      .then((user) => {
        const fresh = { token: stored.token, user };
        saveSession(fresh);
        setSession(fresh);
      })
      .catch(clear)
      .finally(() => setChecking(false));
  }, [clear]);

  const start = useCallback((data) => {
    const next = { token: data.access_token, user: data.user };
    saveSession(next);
    setSession(next);
    return next.user;
  }, []);

  const login = useCallback(
    async (email, password) => start(await apiRequest("/api/auth/login", { method: "POST", body: { email, password } })),
    [start]
  );

  const register = useCallback(
    async (fullName, email, password) =>
      start(
        await apiRequest("/api/auth/register", {
          method: "POST",
          body: { full_name: fullName, email, password },
        })
      ),
    [start]
  );

  const logout = useCallback(async () => {
    try {
      if (session) await apiRequest("/api/auth/logout", { method: "POST", token: session.token });
    } catch {
      /* the local session is cleared either way */
    }
    clear();
  }, [session, clear]);

  const value = useMemo(
    () => ({
      user: session?.user ?? null,
      token: session?.token ?? null,
      checking,
      login,
      register,
      logout,
      // Convenience: call the API as the signed-in user.
      api: (path, options = {}) => apiRequest(path, { ...options, token: session?.token }),
    }),
    [session, checking, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}

export function homePathFor(user) {
  if (!user) return "/login";
  if (user.role === "admin") return "/admin/content";
  if (user.role === "mentor") return "/mentor/requests";
  return "/applications";
}
