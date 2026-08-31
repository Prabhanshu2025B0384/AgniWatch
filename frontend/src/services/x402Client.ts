import { x402Client, x402HTTPClient } from '@x402/core/client';
import { ExactAvmScheme, type ClientAvmSigner } from '@x402-avm/avm';
import { api } from './api';
import axios from 'axios';

const baseClient = new x402Client();

export const demoAvmSigner: ClientAvmSigner = {
    address: "", // Will be populated right before payment
    signTransactions: async (txns: Uint8Array[], indexesToSign?: number[]) => {
        return Promise.all(txns.map(async (unsignedTxn, i) => {
            if (indexesToSign && !indexesToSign.includes(i)) return null;
            
            // Convert to base64
            const base64Txn = btoa(String.fromCharCode(...unsignedTxn));
            
            // Send to backend to sign
            const res = await api.post('/api/demo/sign-payment', { unsigned_txn_b64: base64Txn });
            const signedB64 = res.data.signed_txn_b64;
            
            // Convert back to Uint8Array
            const binaryString = atob(signedB64);
            const bytes = new Uint8Array(binaryString.length);
            for (let j = 0; j < binaryString.length; j++) {
                bytes[j] = binaryString.charCodeAt(j);
            }
            return bytes;
        }));
    }
};

// Register the scheme for Algorand TestNet
baseClient.register('algorand:testnet', new ExactAvmScheme(demoAvmSigner));

export const httpClient = new x402HTTPClient(baseClient);

// Setup the axios interceptor
api.interceptors.response.use(
    response => response,
    async error => {
        // Only handle 402 once
        if (error.response && error.response.status === 402 && !error.config._isRetry) {
            error.config._isRetry = true;
            
            try {
                // Parse the 402 response using x402HTTPClient
                const getHeader = (name: string) => error.response.headers[name.toLowerCase()];
                const paymentRequired = httpClient.getPaymentRequiredResponse(getHeader);
                
                // Fire an event so the UI can show "Signing..." state
                window.dispatchEvent(new CustomEvent('x402-payment-started', { detail: {} }));
                
                // Fetch the address dynamically if we don't have it yet
                if (!demoAvmSigner.address) {
                    const addrRes = await api.get('/api/demo/address');
                    demoAvmSigner.address = addrRes.data.address;
                }
                
                // Create payment payload (this invokes our demo signer and the facilitator)
                const payload = await httpClient.createPaymentPayload(paymentRequired);
                
                // Encode the header
                const headers = httpClient.encodePaymentSignatureHeader(payload);
                
                // Attach the new headers and retry the request
                error.config.headers = { ...error.config.headers, ...headers };
                
                // Fire an event for success
                window.dispatchEvent(new CustomEvent('x402-payment-success', { detail: { payload } }));
                
                return axios(error.config);
                
            } catch (paymentError) {
                console.error("Payment failed:", paymentError);
                window.dispatchEvent(new CustomEvent('x402-payment-failed', { detail: { error: paymentError } }));
                return Promise.reject(paymentError);
            }
        }
        return Promise.reject(error);
    }
);
