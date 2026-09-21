import React, { createContext, useContext, useState, useEffect } from 'react';
import { supabase } from '../supabaseClient';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);   // { id, email, role, name }
  const [loading, setLoading] = useState(true);

  /** Fetch the admin_profiles row for a Supabase auth user and set state. */
  const loadProfile = async (supabaseUser) => {
    try {
      const { data, error } = await supabase
        .from('admin_profiles')
        .select('role, name')
        .eq('id', supabaseUser.id)
        .single();

      if (error) throw error;

      setUser({
        id: supabaseUser.id,
        email: supabaseUser.email,
        role: data.role,
        name: data.name,
      });
    } catch {
      // Profile row missing — treat as unauthorised admin
      setUser({
        id: supabaseUser.id,
        email: supabaseUser.email,
        role: null,
        name: supabaseUser.email.split('@')[0],
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Restore existing session on mount
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.user) {
        loadProfile(session.user);
      } else {
        setLoading(false);
      }
    });

    // Listen for auth state changes (login / logout)
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        if (session?.user) {
          loadProfile(session.user);
        } else {
          setUser(null);
          setLoading(false);
        }
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  /** Sign in with Supabase Auth (email + password). Throws on failure. */
  const login = async (email, password) => {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
    return data;
  };

  /** Sign out of Supabase Auth and clear local user state. */
  const logout = async () => {
    await supabase.auth.signOut();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
