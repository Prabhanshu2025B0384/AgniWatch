import axios from 'axios';

// Fallback logic for API URL resolution:
// 1. Explicitly configured VITE_API_URL (e.g., in Vercel settings pointing to Render backend)
// 2. If running locally (localhost:5173), fallback to local backend (localhost:8000)
// 3. If deployed on the same domain without VITE_API_URL, fallback to /api

const getApiUrl = () => {
    try {
        if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_URL) {
            return import.meta.env.VITE_API_URL;
        }
    } catch (e) {}
    
    if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
        return "http://localhost:8000";
    }
    return "http://localhost:8000"; // Default for tests
};

export const api = axios.create({
    baseURL: getApiUrl(),
    headers: {
        'Content-Type': 'application/json'
    }
});

// We can intercept 402 responses to trigger UI modals for payment.
api.interceptors.response.use(
    response => response,
    async error => {
        if (error.response && error.response.status === 402) {
            // Trigger global event or state for Payment Required UI
            const req = error.response.headers['payment-required'];
            window.dispatchEvent(new CustomEvent('x402-payment-required', { detail: { req, originalRequest: error.config } }));
        }
        return Promise.reject(error);
    }
);
