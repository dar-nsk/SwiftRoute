import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Interceptor to add meaningful error messages
api.interceptors.response.use(
  response => response,
  error => {
    if (error.code === 'ECONNABORTED')
      throw new Error('Request timed out. The server may be loading the road network.');
    if (!error.response)
      throw new Error('Cannot reach server. Make sure the backend is running.');
    const msg = error.response.data?.detail || error.response.statusText;
    if (error.response.status === 503) throw new Error(`Service unavailable: ${msg}`);
    if (error.response.status === 404) throw new Error(`Route not found: ${msg}`);
    throw new Error(`API error ${error.response.status}: ${msg}`);
  }
);

export const calculateRoute = async (origin, destination, mode, hour, dayOfWeek, weatherCode) => {
  const { data } = await api.post('/api/route', {
    origin: { lat: origin[0], lon: origin[1] },
    destination: { lat: destination[0], lon: destination[1] },
    mode,
    hour,
    day_of_week: dayOfWeek,
    weather_code: weatherCode,
  });
  return data;
};

export const solveVRP = async (depot, deliveries, numVehicles, optimizeFor) => {
  const { data } = await api.post('/api/vrp', {
    depot: { lat: depot[0], lon: depot[1] },
    deliveries: deliveries.map(d => ({ lat: d[0], lon: d[1] })),
    num_vehicles: numVehicles,
    optimize_for: optimizeFor,
  });
  return data;
};

export const getHealthCheck = async () => {
  const { data } = await api.get('/api/health');
  return data;
};

export const getModes = async () => {
  const { data } = await api.get('/api/route/modes');
  return data;
};

export const getDemoVRP = async () => {
  const { data } = await api.get('/api/vrp/demo');
  return data;
};
