import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

// Use current origin for API calls (works in production with custom domain)
// Fall back to env variable for local development
const getBackendUrl = () => {
  // In production, use the same origin as the frontend
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
    return window.location.origin;
  }
  // In development, use the env variable
  return process.env.REACT_APP_BACKEND_URL || '';
};

const BACKEND_URL = getBackendUrl();
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
  const [needsVillaNumber, setNeedsVillaNumber] = useState(false);

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
      
      // Check if user needs to provide villa number
      if (response.data.needs_villa_number) {
        console.log('[Auth] User needs to provide villa number');
        setNeedsVillaNumber(true);
      } else {
        setNeedsVillaNumber(false);
      }
    } catch (error) {
      console.log('[Auth] Auth check failed:', error.response?.status, error.response?.data);
      setUser(null);
      setNeedsVillaNumber(false);
      // Clear invalid token
      localStorage.removeItem('session_token');
    } finally {
      setLoading(false);
    }
  };

  const refreshUser = async () => {
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${API}/auth/user`, {
        withCredentials: true,
        headers: {
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });
      console.log('[Auth] User data refreshed');
      setUser(response.data);
      
      // Update villa number requirement
      if (response.data.needs_villa_number) {
        setNeedsVillaNumber(true);
      } else {
        setNeedsVillaNumber(false);
      }
      
      return response.data;
    } catch (error) {
      console.error('[Auth] Failed to refresh user data:', error);
      throw error;
    }
  };

  const updateVillaNumber = (villaNumber) => {
    // Update local user state after villa number is set
    if (user) {
      setUser({ ...user, villa_number: villaNumber, needs_villa_number: false });
    }
    setNeedsVillaNumber(false);
  };

  const loginWithGoogle = () => {
    // Open Google OAuth in a popup window
    const width = 500;
    const height = 600;
    const left = window.screen.width / 2 - width / 2;
    const top = window.screen.height / 2 - height / 2;
    
    const popup = window.open(
      `${API}/auth/google/login`,
      'Google Login',
      `width=${width},height=${height},left=${left},top=${top}`
    );

    // Listen for messages from the popup
    const handleMessage = async (event) => {
      // Verify the origin
      if (event.origin !== window.location.origin && event.origin !== BACKEND_URL) {
        return;
      }

      if (event.data.type === 'oauth_success' && event.data.token) {
        console.log('[Auth] OAuth success, storing token');
        localStorage.setItem('session_token', event.data.token);
        
        // Close popup
        if (popup) {
          popup.close();
        }
        
        // Check auth to update user state
        await checkAuth();
        
        // Remove event listener
        window.removeEventListener('message', handleMessage);
      }
    };

    window.addEventListener('message', handleMessage);

    // Check if popup was blocked
    if (!popup || popup.closed || typeof popup.closed === 'undefined') {
      alert('Popup blocked! Please allow popups for this website.');
      window.removeEventListener('message', handleMessage);
    }
  };

  const loginWithEmail = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, {
        email,
        password
      });

      if (response.data.token) {
        localStorage.setItem('session_token', response.data.token);
        setUser(response.data.user);
        console.log('[Auth] Email login successful');
      }
    } catch (error) {
      console.error('[Auth] Email login failed:', error.response?.data);
      throw error;
    }
  };

  const registerWithEmail = async (email, password, name, villa_number = null, picture = null) => {
    try {
      const response = await axios.post(`${API}/auth/register`, {
        email,
        password,
        name,
        villa_number,
        picture
      });

      if (response.data.token) {
        localStorage.setItem('session_token', response.data.token);
        setUser(response.data.user);
        console.log('[Auth] Registration successful');
      }
    } catch (error) {
      console.error('[Auth] Registration failed:', error.response?.data);
      throw error;
    }
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
    loginWithGoogle,
    loginWithEmail,
    registerWithEmail,
    logout,
    refreshUser,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin',
    isManager: user?.role === 'manager',
    role: user?.role || 'user'
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
