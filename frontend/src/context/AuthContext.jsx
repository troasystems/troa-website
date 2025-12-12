import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for token in URL (from OAuth callback)
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    const authSuccess = urlParams.get('auth_success');
    
    console.log('[Auth] URL params - token:', token ? 'present' : 'missing', 'auth_success:', authSuccess);
    console.log('[Auth] Current localStorage token:', localStorage.getItem('session_token') ? 'present' : 'missing');
    
    if (token) {
      // Store token in localStorage
      console.log('[Auth] Storing token in localStorage');
      localStorage.setItem('session_token', token);
      // Remove token from URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
    
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      // Get token from localStorage
      const token = localStorage.getItem('session_token');
      console.log('[Auth] Checking auth with token:', token ? 'present' : 'missing');
      
      const response = await axios.get(`${API}/auth/user`, {
        withCredentials: true,
        headers: {
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });
      console.log('[Auth] User authenticated:', response.data.email);
      setUser(response.data);
    } catch (error) {
      console.log('[Auth] Auth check failed:', error.response?.status, error.response?.data);
      setUser(null);
      // Clear invalid token
      localStorage.removeItem('session_token');
    } finally {
      setLoading(false);
    }
  };

  const login = () => {
    window.location.href = `${API}/auth/google/login`;
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, {
        withCredentials: true
      });
      setUser(null);
      localStorage.removeItem('session_token');
      window.location.href = '/';
    } catch (error) {
      console.error('Logout error:', error);
      localStorage.removeItem('session_token');
      setUser(null);
      window.location.href = '/';
    }
  };

  const value = {
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin',
    isManager: user?.role === 'manager',
    role: user?.role || 'user'
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
