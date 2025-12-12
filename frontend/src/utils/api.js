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

export const BACKEND_URL = getBackendUrl();
export const API = `${BACKEND_URL}/api`;

// Helper function to get full image URL
export const getImageUrl = (imagePath) => {
  if (!imagePath) return '';
  
  // If it's a full URL, check if it needs hostname replacement
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
    // List of old hostnames that should be replaced with current origin
    const oldHostnames = [
      'villaportal.emergent.host',
      'villaportal.preview.emergentagent.com',
      'localhost:8001',
      'localhost:3000'
    ];
    
    try {
      const url = new URL(imagePath);
      const currentOrigin = typeof window !== 'undefined' ? window.location.origin : BACKEND_URL;
      
      // Check if the URL uses an old hostname
      if (oldHostnames.some(host => url.hostname === host || url.host === host)) {
        // Replace with current origin, keeping the path
        return `${currentOrigin}${url.pathname}`;
      }
    } catch (e) {
      // If URL parsing fails, return as-is
      return imagePath;
    }
    
    return imagePath;
  }
  
  // If relative path, prepend backend URL
  return `${BACKEND_URL}${imagePath}`;
};

// Basic auth credentials from environment variables (no longer needed but kept for compatibility)
const BASIC_AUTH_USERNAME = process.env.REACT_APP_BASIC_AUTH_USERNAME || 'dogfooding';
const BASIC_AUTH_PASSWORD = process.env.REACT_APP_BASIC_AUTH_PASSWORD || 'skywalker';

// Create base64 encoded basic auth header
export const basicAuthToken = btoa(`${BASIC_AUTH_USERNAME}:${BASIC_AUTH_PASSWORD}`);

// Helper function to get basic auth string
export const getBasicAuth = () => btoa(`${BASIC_AUTH_USERNAME}:${BASIC_AUTH_PASSWORD}`);

// Create axios instance
export const apiClient = axios.create({
  baseURL: API,
  withCredentials: true
});

// Add interceptor to include session token if available
apiClient.interceptors.request.use(
  (config) => {
    const sessionToken = localStorage.getItem('session_token');
    if (sessionToken) {
      config.headers['X-Session-Token'] = `Bearer ${sessionToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default apiClient;
