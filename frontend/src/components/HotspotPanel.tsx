import React, { useState, useEffect } from 'react';
import { Box, Typography, Card, CardContent, Chip, Button, Alert, CircularProgress } from '@mui/material';
import { api } from '../services/api';
import WhatshotIcon from '@mui/icons-material/Whatshot';
import FactoryIcon from '@mui/icons-material/Factory';
import ForestIcon from '@mui/icons-material/Forest';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';

interface HotspotPanelProps {
  hotspotId: string | null;
  onClose: () => void;
}

export const HotspotPanel: React.FC<HotspotPanelProps> = ({ hotspotId, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [paymentStatus, setPaymentStatus] = useState<string | null>(null);

  useEffect(() => {
    if (!hotspotId) {
        setAnalysis(null);
        setError(null);
        setPaymentStatus(null);
        return;
    }
    fetchAnalysis();
  }, [hotspotId]);

  useEffect(() => {
    const handlePaymentStarted = () => {
        setPaymentStatus("Signing Transaction (Demo Wallet)...");
    };
    const handlePaymentSuccess = (e: any) => {
        const payload = e.detail?.payload;
        setPaymentStatus(`Settlement Successful (TX ID: ${payload?.id})`);
        setTimeout(() => setPaymentStatus(null), 3000);
    };
    const handlePaymentFailed = (e: any) => {
        setPaymentStatus(null);
        setError(`Payment failed: ${e.detail?.error?.message || 'Unknown error'}`);
    };

    window.addEventListener('x402-payment-started', handlePaymentStarted);
    window.addEventListener('x402-payment-success', handlePaymentSuccess);
    window.addEventListener('x402-payment-failed', handlePaymentFailed);

    return () => {
        window.removeEventListener('x402-payment-started', handlePaymentStarted);
        window.removeEventListener('x402-payment-success', handlePaymentSuccess);
        window.removeEventListener('x402-payment-failed', handlePaymentFailed);
    };
  }, []);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);
    setPaymentStatus(null);
    try {
        const response = await api.get(`/api/analysis/${hotspotId}`);
        setAnalysis(response.data.data);
    } catch (err: any) {
        if (err.response?.status === 402) {
            setError("Premium analysis requires payment (x402). Check payment modal.");
        } else {
            setError("Failed to fetch analysis.");
        }
    } finally {
        setLoading(false);
    }
  };

  if (!hotspotId) {
    return (
        <Card sx={{ m: 2, p: 2, height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Typography variant="body1" color="text.secondary">Select a hotspot on the map to view details.</Typography>
        </Card>
    );
  }

  const getRiskColor = (risk: string) => {
      switch(risk) {
          case 'CRITICAL': return 'error';
          case 'HIGH': return 'warning';
          case 'MODERATE': return 'info';
          default: return 'success';
      }
  };

  return (
    <Card sx={{ m: 2, height: '100%', overflow: 'auto' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Hotspot Analysis</Typography>
            <Button size="small" onClick={onClose}>Close</Button>
        </Box>

        {paymentStatus && (
            <Alert icon={<AccountBalanceWalletIcon />} severity="info" sx={{ mb: 2 }}>
                {paymentStatus}
            </Alert>
        )}

        {loading ? (
            <Box sx={{ py: 4, display: 'flex', justifyContent: 'center' }}><CircularProgress /></Box>
        ) : error ? (
            <Alert severity="warning" action={<Button color="inherit" size="small" onClick={fetchAnalysis}>Retry</Button>}>
                {error}
            </Alert>
        ) : analysis ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <Box>
                    <Typography variant="subtitle2" color="text.secondary">Classification</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                        {analysis.analysis.classification === 'industrial' ? <FactoryIcon color="primary" /> : <ForestIcon color="error" />}
                        <Typography variant="h5" sx={{ textTransform: 'capitalize' }}>
                            {analysis.analysis.classification}
                        </Typography>
                        <Chip label={`Risk: ${analysis.analysis.risk_level}`} color={getRiskColor(analysis.analysis.risk_level) as any} size="small" />
                    </Box>
                </Box>

                <Box>
                    <Typography variant="subtitle2" color="text.secondary">Thermal Metrics</Typography>
                    <Typography variant="body1">FRP: <strong>{analysis.hotspot.frp} MW</strong></Typography>
                    <Typography variant="body1">Brightness: <strong>{analysis.hotspot.brightness} K</strong></Typography>
                    <Typography variant="body2" color="text.secondary">
                        Detected by {analysis.hotspot.satellite} on {analysis.hotspot.acq_date} {analysis.hotspot.acq_time}
                    </Typography>
                </Box>

                <Box>
                    <Typography variant="subtitle2" color="text.secondary">AI Evidence</Typography>
                    <Box sx={{ mt: 1 }}>
                        {analysis.analysis.evidence.map((ev: string, idx: number) => (
                            <Alert icon={<WhatshotIcon fontSize="inherit" />} severity="info" sx={{ mb: 1, py: 0 }} key={idx}>
                                {ev}
                            </Alert>
                        ))}
                    </Box>
                </Box>
                
                {analysis.payment_receipt && (
                    <Box sx={{ mt: 2 }}>
                        <Alert severity="success" icon={false}>
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                                Unlocked via x402 Algorand Transaction
                            </Typography>
                            {analysis.payment_receipt.id && (
                                <a 
                                    href={`https://lora.algokit.io/testnet/transaction/${analysis.payment_receipt.id}`} 
                                    target="_blank" 
                                    rel="noreferrer"
                                    style={{ fontSize: '12px', color: '#1976d2' }}
                                >
                                    View on Lora (Tx: {analysis.payment_receipt.id.substring(0,8)}...)
                                </a>
                            )}
                        </Alert>
                    </Box>
                )}
            </Box>
        ) : null}
      </CardContent>
    </Card>
  );
};
