import React, { useState, useCallback } from 'react';
import { Box, ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import MapView from './components/MapView';
import ControlPanel from './components/ControlPanel';
import RouteInfo from './components/RouteInfo';
import { calculateRoute, solveVRP } from './services/api';
import './styles/App.css';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#6366f1' },
    secondary: { main: '#22c55e' },
  },
});

export default function App() {
  const [originPoint, setOriginPoint] = useState(null);
  const [destPoint, setDestPoint] = useState(null);
  const [routeData, setRouteData] = useState(null);
  const [vrpData, setVrpData] = useState(null);
  const [mode, setMode] = useState('balanced');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [hour, setHour] = useState(12);
  const [dayOfWeek, setDayOfWeek] = useState(1);
  const [weatherCode, setWeatherCode] = useState(0);
  const [numVehicles, setNumVehicles] = useState(2);
  const [vrpStops, setVrpStops] = useState([]);
  const [error, setError] = useState(null);

  const handleMapClick = useCallback(
    point => {
      if (activeTab === 0) {
        if (!originPoint) {
          setOriginPoint(point);
        } else if (!destPoint) {
          setDestPoint(point);
        } else {
          // Reset and start over
          setOriginPoint(point);
          setDestPoint(null);
          setRouteData(null);
        }
      } else {
        setVrpStops(prev => [...prev, point]);
      }
    },
    [originPoint, destPoint, activeTab]
  );

  const handleCalculateRoute = useCallback(async () => {
    if (!originPoint || !destPoint) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await calculateRoute(originPoint, destPoint, mode, hour, dayOfWeek, weatherCode);
      setRouteData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [originPoint, destPoint, mode, hour, dayOfWeek, weatherCode]);

  const handleSolveVRP = useCallback(async () => {
    if (vrpStops.length < 2) return;
    setIsLoading(true);
    setError(null);
    try {
      const depot = vrpStops[0];
      const deliveries = vrpStops.slice(1);
      const data = await solveVRP(depot, deliveries, numVehicles, 'time');
      setVrpData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [vrpStops, numVehicles]);

  const handleClear = useCallback(() => {
    setOriginPoint(null);
    setDestPoint(null);
    setRouteData(null);
    setVrpData(null);
    setVrpStops([]);
    setError(null);
  }, []);

  const handleRemoveStop = useCallback(idx => {
    setVrpStops(prev => prev.filter((_, i) => i !== idx));
  }, []);

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box className="app-container">
        <Box className="sidebar">
          <ControlPanel
            mode={mode}
            setMode={setMode}
            hour={hour}
            setHour={setHour}
            dayOfWeek={dayOfWeek}
            setDayOfWeek={setDayOfWeek}
            weatherCode={weatherCode}
            setWeatherCode={setWeatherCode}
            numVehicles={numVehicles}
            setNumVehicles={setNumVehicles}
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            originPoint={originPoint}
            destPoint={destPoint}
            vrpStops={vrpStops}
            onCalculateRoute={handleCalculateRoute}
            onSolveVRP={handleSolveVRP}
            onClear={handleClear}
            onRemoveStop={handleRemoveStop}
            isLoading={isLoading}
          />
          {error && (
            <Box
              sx={{
                color: '#ef4444',
                px: 2,
                py: 1.5,
                fontSize: '0.82rem',
                background: '#ef444415',
                borderTop: '1px solid #ef444430',
              }}
            >
              ⚠️ {error}
            </Box>
          )}
          <RouteInfo routeData={routeData} vrpData={vrpData} isLoading={isLoading} mode={mode} />
        </Box>
        <Box className="map-container">
          <MapView
            originPoint={originPoint}
            destPoint={destPoint}
            routeData={routeData}
            vrpData={vrpData}
            onMapClick={handleMapClick}
            mode={mode}
            vrpStops={vrpStops}
          />
        </Box>
      </Box>
    </ThemeProvider>
  );
}
