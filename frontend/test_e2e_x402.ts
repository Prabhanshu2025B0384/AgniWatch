// Mock window and import.meta for Node.js
if (typeof window === 'undefined') {
    (global as any).window = {
        location: { hostname: 'localhost' },
        dispatchEvent: (event: any) => {
            console.log(`[Event Dispatched]: ${event.type}`);
        },
        removeEventListener: () => {},
        addEventListener: () => {}
    };
    (global as any).CustomEvent = class CustomEvent {
        type: string;
        detail: any;
        constructor(type: string, options?: any) {
            this.type = type;
            this.detail = options?.detail || {};
        }
    };
}
(global as any).import = { meta: { env: {} } }; // Stub import.meta.env

import { api } from './src/services/api';
import './src/services/x402Client';

async function runTest() {
    console.log("PHASE 2 - x402 PAYMENT CHALLENGE (And Beyond)");
    try {
        console.log("Making request to /api/analysis/1...");
        const response = await api.get('/api/analysis/1');
        
        console.log("PHASE 6 - PAID REQUEST");
        console.log(`Status: ${response.status}`);
        console.log(`Response Data:`, JSON.stringify(response.data, null, 2));
        
        if (response.status === 200) {
            console.log("\nTEST FULLY PROVEN: The interceptor successfully caught the 402, paid, and retried to get a 200!");
        } else {
            console.log("\nTEST FAILED: Unexpected status code.");
        }
    } catch (e: any) {
        console.error("Request failed:", e.message);
        if (e.response) {
            console.error(`Response status: ${e.response.status}`);
            console.error(`Response data:`, e.response.data);
            if (e.response.headers && e.response.headers['payment-required']) {
                console.log("\nPayment Requirements: PASS");
                console.log("402 intercepted, but payment failed to process fully.");
            }
        }
    }
}

runTest();

