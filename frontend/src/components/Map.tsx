import React from 'react';
import { MapContainer, TileLayer, Popup, CircleMarker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Box } from '@mui/material';

// Fix Leaflet icon issue
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface Hotspot {
  id: string;
  latitude: number;
  longitude: number;
  brightness: number;
  frp: number;
}

interface MapProps {
  hotspots: Hotspot[];
  onHotspotClick: (id: string) => void;
}

const getMarkerColor = (frp: number) => {
    if (frp > 100) return '#ef5350'; // Red
    if (frp > 20) return '#ff9800'; // Orange
    return '#ffeb3b'; // Yellow
};

export const IndiaMap: React.FC<MapProps> = ({ hotspots, onHotspotClick }) => {
  return (
    <Box sx={{ height: '100%', width: '100%', borderRadius: 2, overflow: 'hidden' }}>
      <MapContainer 
        center={[20.5937, 78.9629]} 
        zoom={5} 
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {hotspots.map((hotspot) => (
          <CircleMarker
            key={hotspot.id}
            center={[hotspot.latitude, hotspot.longitude]}
            radius={Math.max(5, Math.min(hotspot.frp / 10, 20))}
            pathOptions={{ 
                color: getMarkerColor(hotspot.frp), 
                fillColor: getMarkerColor(hotspot.frp), 
                fillOpacity: 0.6 
            }}
            eventHandlers={{
                click: () => onHotspotClick(hotspot.id),
            }}
          >
            <Popup>
              <strong>Hotspot</strong><br />
              FRP: {hotspot.frp}<br />
              Brightness: {hotspot.brightness}K
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </Box>
  );
};
