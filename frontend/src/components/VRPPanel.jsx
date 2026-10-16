import React from 'react';
import {
  Box,
  Typography,
  Skeleton,
  Divider,
  Stack,
} from '@mui/material';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import DirectionsCarIcon from '@mui/icons-material/DirectionsCar';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import RouteIcon from '@mui/icons-material/Route';

const PANEL_BG = '#16213e';
const BORDER = '#2d2d4e';
const VRP_COLORS = ['#ef4444', '#3b82f6', '#22c55e', '#f59e0b', '#8b5cf6'];

function VehicleRow({ vehicle, index }) {
  const color = VRP_COLORS[index % VRP_COLORS.length];
  return (
    <Box
      sx={{
        px: 1.5,
        py: 1,
        mb: 0.75,
        borderRadius: 1.5,
        border: `1px solid ${color}44`,
        background: `${color}0d`,
        display: 'flex',
        alignItems: 'flex-start',
        gap: 1.5,
      }}
    >
      {/* Vehicle badge */}
      <Box
        sx={{
          width: 32,
          height: 32,
          borderRadius: '50%',
          background: color,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          boxShadow: `0 2px 8px ${color}66`,
        }}
      >
        <LocalShippingIcon sx={{ fontSize: 16, color: '#fff' }} />
      </Box>

      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Typography variant="body2" sx={{ fontWeight: 700, color: '#e2e8f0', lineHeight: 1.3 }}>
          Vehicle {index + 1}
        </Typography>

        {/* Stats row */}
        <Stack direction="row" spacing={1.5} sx={{ mt: 0.5, flexWrap: 'wrap' }}>
          <Stack direction="row" alignItems="center" spacing={0.4}>
            <DirectionsCarIcon sx={{ fontSize: 13, color: '#7c7ca0' }} />
            <Typography variant="caption" sx={{ color: '#7c7ca0' }}>
              {vehicle.stops?.length ?? 0} stops
            </Typography>
          </Stack>
          <Stack direction="row" alignItems="center" spacing={0.4}>
            <RouteIcon sx={{ fontSize: 13, color: '#7c7ca0' }} />
            <Typography variant="caption" sx={{ color: '#7c7ca0' }}>
              {vehicle.distance_km?.toFixed(2) ?? '–'} km
            </Typography>
          </Stack>
          <Stack direction="row" alignItems="center" spacing={0.4}>
            <AccessTimeIcon sx={{ fontSize: 13, color: '#7c7ca0' }} />
            <Typography variant="caption" sx={{ color: '#7c7ca0' }}>
              {vehicle.time_min?.toFixed(0) ?? '–'} min
            </Typography>
          </Stack>
        </Stack>

        {/* Stop sequence */}
        {vehicle.stops && vehicle.stops.length > 0 && (
          <Box sx={{ mt: 0.75, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {vehicle.stops.map((stop, si) => (
              <Box
                key={si}
                sx={{
                  px: 0.75,
                  py: 0.1,
                  borderRadius: 0.75,
                  background: `${color}22`,
                  border: `1px solid ${color}44`,
                  fontSize: '0.65rem',
                  color,
                  fontWeight: 700,
                }}
              >
                {stop}
              </Box>
            ))}
          </Box>
        )}
      </Box>
    </Box>
  );
}

export default function VRPPanel({ vrpData, isLoading }) {
  if (!isLoading && !vrpData) return null;

  return (
    <Box
      sx={{
        px: 2,
        py: 1.5,
        borderTop: `1px solid ${BORDER}`,
        background: '#12122a',
      }}
    >
      <Typography
        variant="caption"
        sx={{
          color: '#7c7ca0',
          fontWeight: 700,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          display: 'block',
          mb: 1.5,
        }}
      >
        Fleet Assignment
      </Typography>

      {/* Loading skeletons */}
      {isLoading && (
        <Box>
          {[0, 1, 2].map(i => (
            <Skeleton
              key={i}
              variant="rectangular"
              height={70}
              sx={{ borderRadius: 1.5, bgcolor: '#2d2d4e', mb: 0.75 }}
              animation="wave"
            />
          ))}
        </Box>
      )}

      {/* Vehicle routes */}
      {!isLoading && vrpData?.routes?.map((vehicle, idx) => (
        <VehicleRow key={idx} vehicle={vehicle} index={idx} />
      ))}

      {/* Total summary */}
      {!isLoading && vrpData?.total && (
        <>
          <Divider sx={{ borderColor: BORDER, my: 1.25 }} />
          <Box
            sx={{
              px: 1.5,
              py: 1,
              borderRadius: 1,
              background: PANEL_BG,
              border: `1px solid ${BORDER}`,
            }}
          >
            <Typography
              variant="caption"
              sx={{ color: '#7c7ca0', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', mb: 0.5 }}
            >
              Total Fleet
            </Typography>
            <Stack direction="row" spacing={3}>
              <Box>
                <Typography variant="caption" sx={{ color: '#7c7ca0' }}>
                  Distance
                </Typography>
                <Typography variant="body2" sx={{ color: '#e2e8f0', fontWeight: 700 }}>
                  {vrpData.total.distance_km?.toFixed(2) ?? '–'} km
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" sx={{ color: '#7c7ca0' }}>
                  Time
                </Typography>
                <Typography variant="body2" sx={{ color: '#e2e8f0', fontWeight: 700 }}>
                  {vrpData.total.time_min?.toFixed(0) ?? '–'} min
                </Typography>
              </Box>
              {vrpData.total.vehicles_used != null && (
                <Box>
                  <Typography variant="caption" sx={{ color: '#7c7ca0' }}>
                    Vehicles
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#e2e8f0', fontWeight: 700 }}>
                    {vrpData.total.vehicles_used}
                  </Typography>
                </Box>
              )}
            </Stack>
          </Box>
        </>
      )}
    </Box>
  );
}
