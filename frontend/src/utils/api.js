import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Basic auth credentials
const BASIC_AUTH_USERNAME = 'dogfooding';
const BASIC_AUTH_PASSWORD = 'skywalker';

// Create base64 encoded basic auth header
const basicAuthToken = btoa(`${BASIC_AUTH_USERNAME}:${BASIC_AUTH_PASSWORD}`);

// Create axios instance with basic auth
export const apiClient = axios.create({
  baseURL: API,
  withCredentials: true,
  headers: {
    'Authorization': `Basic ${basicAuthToken}`
  }
});

// Add interceptor to include session token if available
apiClient.interceptors.request.use(
  (config) => {
    const sessionToken = localStorage.getItem('session_token');
    if (sessionToken) {
      // Add Bearer token in addition to basic auth
      config.headers['X-Session-Token'] = `Bearer ${sessionToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default apiClient;
