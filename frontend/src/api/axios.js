import axios from "axios";

// ============================================================
// ESS AI API CONFIGURATION
// ============================================================

const API_BASE_URL =
  "https://dependence-tab-reproduction-distinction.trycloudflare.com";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// ============================================================
// AUTOMATIC JWT
// ============================================================

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default api;