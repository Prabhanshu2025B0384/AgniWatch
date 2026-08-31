import React, { useState, useEffect } from 'react';
import { ThemeProvider, CssBaseline, Box, AppBar, Toolbar, Typography, Grid, Alert } from '@mui/material';
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment';
import theme from './theme';
import { IndiaMap } from './components/Map';
import { HotspotPanel } from './components/HotspotPanel';
import { api } from './services/api';

const App: React.FC = () => {
  const [hotspots, setHotspots] = useState<any[]>([]);
  const [selectedHotspot, setSelectedHotspot] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch initial map layer data
    const loadData = async () => {
        try {
            const resp = await api.get('/api/hotspots/');
            if (resp.data && resp.data.data) {
                setHotspots(resp.data.data);
                setApiError(null);
            }
        } catch (e) {
            console.error("Failed to load hotspots", e);
            setApiError("NASA FIRMS API key is not configured or backend is unreachable.");
            // Provide fallback dummy data so the map is not completely empty
            setHotspots([
                { id: "demo-1", latitude: 22.5, longitude: 79.5, brightness: 310, frp: 25 },
                { id: "demo-2", latitude: 23.1, longitude: 80.2, brightness: 340, frp: 120 }
            ]);
        }
    };
    loadData();
    
    // Listen for x402 payment required
    const handlePaymentRequired = (e: any) => {
        const { req } = e.detail;
        console.log("x402 Payment Required intercepted", req);
        alert("x402 Payment Required via Algorand Testnet. Proceeding to GoPlausible Facilitator... (Check console)");
    };
    window.addEventListener('x402-payment-required', handlePaymentRequired);
    return () => window.removeEventListener('x402-payment-required', handlePaymentRequired);
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
        <AppBar position="static" color="transparent" elevation={0} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Toolbar>
            <LocalFireDepartmentIcon color="primary" sx={{ mr: 2 }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
              AgniWatch
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Agentic Thermal Intelligence (x402 + Algorand)
            </Typography>
          </Toolbar>
        </AppBar>
        
        <Box sx={{ flexGrow: 1, p: 2 }}>
          {apiError && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                  LIVE SATELLITE DATA UNAVAILABLE: {apiError} (Showing demo data)
              </Alert>
          )}
          <Grid container spacing={2} sx={{ height: apiError ? 'calc(100% - 64px)' : '100%' }}>
            <Grid size={{ xs: 12, md: 8 }} sx={{ height: '100%' }}>
              <IndiaMap hotspots={hotspots} onHotspotClick={setSelectedHotspot} />
            </Grid>
            <Grid size={{ xs: 12, md: 4 }} sx={{ height: '100%' }}>
              <HotspotPanel hotspotId={selectedHotspot} onClose={() => setSelectedHotspot(null)} />
            </Grid>
          </Grid>
        </Box>
      </Box>
    </ThemeProvider>
  );
};

export default App;
