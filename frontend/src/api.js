import axios from 'axios';

// Create an axios instance
const api = axios.create({
  baseURL: 'http://localhost:8000',
});

// Add a request interceptor
// This function will be called before every request is sent
api.interceptors.request.use(
  (config) => {
    // Get the token from localStorage
    const token = localStorage.getItem('userToken');
    if (token) {
      // If the token exists, add it to the Authorization header
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    // Do something with request error
    return Promise.reject(error);
  }
);

export default api;