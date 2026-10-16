import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Chip,
  Skeleton,
  Divider,
  Stack,
} from '@mui/material';
import DirectionsCarIcon from '@mui/icons-material/DirectionsCar';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import LocalGasStationIcon from '@mui/icons-material/LocalGasStation';
import CloudIcon from '@mui/icons-material/Cloud';

const PANEL_BG = '#16213e';
const BORDER = '#2d2d4e';

const MODE_META = {
  fastest: { label: 'Fastest', color: '#3b82f6' },
  eco: { label: 'Eco / Green', color: '#22c55e' },
  toll_free: { label: 'Toll-Free', color: '#f97316' },
  balanced: { label: 'Balanced', color: '#a855f7' },
};

const VRP_COLORS = ['#ef4444', '#3b82f6', '#22c55e', '#f59e0b', '#8b5cf6'];

function MetricCard({ icon, label, value, unit, color }) {
  return (
    <Card
      sx={{
        background: PANEL_BG,
        border: `1px solid ${BORDER}`,
        borderRadius: 2,
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: '0 4px 12px rgba(99,102,241,0.2)',
        },
      }}
    >
      <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
        <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 0.5 }}>
          <Box sx={{ color: color || '#6366f1' }}>{icon}</Box>
          <Typography variant="caption" sx={{ color: '#7c7ca0', fontWeight: 600 }}>
            {label}
          </Typography>
        </Stack>
        <Typography variant="h6" sx={{ color: '#e2e8f0', fontWeight: 700, lineHeight: 1 }}>
          {value}
          <Typography component="span" variant="caption" sx={{ color: '#7c7ca0', ml: 0.5 }}>
            {unit}
          </Typography>
        </Typography>
      </CardContent>
    </Card>
  );
}

function SkeletonCards() {
  return (
    <Box sx={{ px: 2, py: 1.5 }}>
      <Grid container spacing={1}>
        {[0, 1, 2, 3].map(i => (
          <Grid item xs={6} key={i}>
            <Skeleton
              variant="rectangular"
              height={72}
              sx={{ borderRadius: 2, bgcolor: '#2d2d4e' }}
              animation="wave"
            />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}

export default function RouteInfo({ routeData, vrpData, isLoading, mode }) {
  const modeMeta = MODE_META[mode] || MODE_META.balanced;

  if (!isLoading && !routeData && !vrpData) return null;

  return (
    <Box sx={{ borderTop: `1px solid ${BORDER}` }}>
      {/* Section header */}
      <Box sx={{ px: 2, pt: 1.5, pb: 0.5 }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="caption" sx={{ color: '#7c7ca0', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            Route Results
          </Typography>
          {!isLoading && routeData && (
            <Chip
              label={modeMeta.label}
              size="small"
              sx={{
                background: `${modeMeta.color}22`,
                color: modeMeta.color,
                borderColor: `${modeMeta.color}66`,
                border: '1px solid',
                fontWeight: 700,
                fontSize: '0.7rem',
                height: 20,
              }}
            />
          )}
        </Stack>
      </Box>

      {/* Loading state */}
      {isLoading && <SkeletonCards />}

      {/* Single route metrics */}
      {!isLoading && routeData && (
        <Box sx={{ px: 2, pb: 2 }}>
          <Grid container spacing={1}>
            <Grid item xs={6}>
              <MetricCard
                icon={<DirectionsCarIcon sx={{ fontSize: 18 }} />}
                label="Distance"
                value={(routeData.distance_m / 1000).toFixed(2)}
                unit="km"
                color="#3b82f6"
              />
            </Grid>
            <Grid item xs={6}>
              <MetricCard
                icon={<AccessTimeIcon sx={{ fontSize: 18 }} />}
                label="ETA"
                value={Math.round(routeData.time_sec / 60)}
                unit="min"
                color="#22c55e"
              />
            </Grid>
            <Grid item xs={6}>
              <MetricCard
                icon={<LocalGasStationIcon sx={{ fontSize: 18 }} />}
                label="Fuel"
                value={routeData.fuel_liters?.toFixed(2) ?? '–'}
                unit="L"
                color="#f59e0b"
              />
            </Grid>
            <Grid item xs={6}>
              <MetricCard
                icon={<CloudIcon sx={{ fontSize: 18 }} />}
                label="CO₂"
                value={routeData.co2_kg?.toFixed(2) ?? '–'}
                unit="kg"
                color="#a855f7"
              />
            </Grid>
          </Grid>

          {/* Additional info */}
          {routeData.algorithm && (
            <Box
              sx={{
                mt: 1,
                px: 1.25,
                py: 0.75,
                borderRadius: 1,
                background: '#6366f115',
                border: '1px solid #6366f130',
                fontSize: '0.72rem',
                color: '#7c7ca0',
              }}
            >
              Algorithm: <strong style={{ color: '#a5b4fc' }}>{routeData.algorithm}</strong>
              {routeData.nodes_explored != null && (
                <> &nbsp;·&nbsp; Nodes: <strong style={{ color: '#a5b4fc' }}>{routeData.nodes_explored}</strong></>
              )}
            </Box>
          )}
        </Box>
      )}

      {/* VRP summary — vehicle_stats is the authoritative source */}
      {!isLoading && vrpData && vrpData.vehicle_stats && (
        <Box sx={{ px: 2, pb: 2 }}>
          <Typography variant="caption" sx={{ color: '#7c7ca0', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', display: 'block', mb: 1 }}>
            Fleet Summary
          </Typography>

          {vrpData.vehicle_stats.map((stat, idx) => (
            <Box
              key={idx}
              sx={{
                mb: 0.75,
                px: 1.5,
                py: 1,
                borderRadius: 1,
                border: `1px solid ${BORDER}`,
                background: PANEL_BG,
                display: 'flex',
                alignItems: 'center',
                gap: 1.5,
              }}
            >
              <Box
                sx={{
                  width: 26,
                  height: 26,
                  borderRadius: '50%',
                  background: VRP_COLORS[idx % VRP_COLORS.length],
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 11,
                  fontWeight: 700,
                  color: '#fff',
                  flexShrink: 0,
                }}
              >
                {idx + 1}
              </Box>
              <Box sx={{ flex: 1 }}>
                <Typography variant="caption" sx={{ color: '#e2e8f0', fontWeight: 700 }}>
                  Vehicle {idx + 1}
                </Typography>
                <Typography variant="caption" sx={{ color: '#7c7ca0', display: 'block' }}>
                  {stat.stops ?? 0} stops &nbsp;·&nbsp;
                  {(stat.distance_m / 1000).toFixed(1)} km &nbsp;·&nbsp;
                  {Math.round(stat.time_sec / 60)} min
                </Typography>
              </Box>
            </Box>
          ))}

          {/* Totals */}
          <Divider sx={{ borderColor: BORDER, my: 1 }} />
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="caption" sx={{ color: '#7c7ca0', fontWeight: 700 }}>
              Total distance
            </Typography>
            <Typography variant="caption" sx={{ color: '#e2e8f0', fontWeight: 700 }}>
              {vrpData.total_distance_m != null ? (vrpData.total_distance_m / 1000).toFixed(2) : '–'} km
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.25 }}>
            <Typography variant="caption" sx={{ color: '#7c7ca0', fontWeight: 700 }}>
              Total time
            </Typography>
            <Typography variant="caption" sx={{ color: '#e2e8f0', fontWeight: 700 }}>
              {vrpData.total_time_sec != null ? Math.round(vrpData.total_time_sec / 60) : '–'} min
            </Typography>
          </Box>
        </Box>
      )}
    </Box>
  );
}
