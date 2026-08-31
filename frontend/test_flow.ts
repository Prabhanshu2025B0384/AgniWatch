import axios from 'axios';
import { x402Client, x402HTTPClient } from '@x402/core/client';
import { ExactAvmScheme, type ClientAvmSigner } from '@x402-avm/avm';

const BASE_URL = 'http://localhost:8000';

async function main() {
    console.log("1. Requesting analysis for hotspot 1d8e1aa3-443c-44cf-b88c-5575be4366dc");
    
    let paymentRequiredHeader = "";
    
    try {
        await axios.get(`${BASE_URL}/api/analysis/1d8e1aa3-443c-44cf-b88c-5575be4366dc`);
        console.log("FAIL: Expected 402 Payment Required, got 200 OK");
        process.exit(1);
    } catch (error: any) {
        if (error.response?.status === 402) {
            console.log("2. Received HTTP 402 with x402 payment requirements");
            paymentRequiredHeader = error.response.headers['payment-required'];
            console.log("Payment Required Header: " + paymentRequiredHeader);
        } else {
            console.log("FAIL: Expected 402 Payment Required, got", error.response?.status);
            process.exit(1);
        }
    }
    
    console.log("3. Fetching Demo Wallet Address...");
    const addrRes = await axios.get(`${BASE_URL}/api/demo/address`);
    const address = addrRes.data.address;
    console.log("Demo Wallet Address:", address);
    
    const demoAvmSigner: ClientAvmSigner = {
        address: address,
        signTransactions: async (txns: Uint8Array[], indexesToSign?: number[]) => {
            console.log("-> Demo Signer: Signing", txns.length, "transactions");
            return Promise.all(txns.map(async (unsignedTxn, i) => {
                if (indexesToSign && !indexesToSign.includes(i)) return null;
                const base64Txn = Buffer.from(unsignedTxn).toString('base64');
                const res = await axios.post(`${BASE_URL}/api/demo/sign-payment`, { unsigned_txn_b64: base64Txn });
                return new Uint8Array(Buffer.from(res.data.signed_txn_b64, 'base64'));
            }));
        }
    };
    
    const baseClient = new x402Client();
    baseClient.register('algorand:SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=', new ExactAvmScheme(demoAvmSigner));
    const httpClient = new x402HTTPClient(baseClient);
    
    console.log("4. Parsing payment requirements...");
    const paymentRequired = httpClient.getPaymentRequiredResponse((name) => {
        if (name.toLowerCase() === 'payment-required') return paymentRequiredHeader;
        return undefined;
    });
    
    console.log("5. Generating payment payload (this communicates with GoPlausible)...");
    const payload = await httpClient.createPaymentPayload(paymentRequired);
    console.log("Payment Payload created. Tx ID:", payload.id);
    
    console.log("6. Encoding payment signature header...");
    const signatureHeaders = httpClient.encodePaymentSignatureHeader(payload);
    
    console.log("7. Retrying API request with payment signature...");
    const finalRes = await axios.get(`${BASE_URL}/api/analysis/1d8e1aa3-443c-44cf-b88c-5575be4366dc`, {
        headers: signatureHeaders
    });
    
    console.log("8. SUCCESS! Received final analysis:", finalRes.status);
    console.log(JSON.stringify(finalRes.data, null, 2));
}

main().catch(e => {
    console.error("Test failed:", e.message);
    if (e.response) {
        console.error("Response:", e.response.data);
    }
});
