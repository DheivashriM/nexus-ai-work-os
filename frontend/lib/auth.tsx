"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { User } from "@/types";
import { api } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (name: string, email: string, password: string) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    // Verify any existing session token against the backend
    const savedToken = localStorage.getItem("token");
    if (savedToken) {
      setToken(savedToken);
      // Validate by calling /users/me — if token is stale or DB was reset, clear it
      api.getMe()
        .then((verifiedUser) => {
          setUser(verifiedUser);
          localStorage.setItem("user", JSON.stringify(verifiedUser));
          setLoading(false);
        })
        .catch(() => {
          // Token invalid, user gone, or DB was reset — clear stale session
          setToken(null);
          localStorage.removeItem("token");
          localStorage.removeItem("user");
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string): Promise<User> => {
    const res = await api.loginUser(email, password);
    setToken(res.access_token);
    setUser(res.user);
    localStorage.setItem("token", res.access_token);
    localStorage.setItem("user", JSON.stringify(res.user));
    return res.user;
  };

  const register = async (name: string, email: string, password: string): Promise<User> => {
    const res = await api.registerUser({ name, email, password });
    setToken(res.access_token);
    setUser(res.user);
    localStorage.setItem("token", res.access_token);
    localStorage.setItem("user", JSON.stringify(res.user));
    return res.user;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("token");
    localStorage.removeItem("user");
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

