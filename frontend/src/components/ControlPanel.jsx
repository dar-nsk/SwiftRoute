import React from 'react';
import {
  Box,
  Tabs,
  Tab,
  FormControl,
  FormControlLabel,
  RadioGroup,
  Radio,
  Slider,
  Select,
  MenuItem,
  InputLabel,
  Button,
  IconButton,
  Typography,
  Stack,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Divider,
} from '@mui/material';
import BoltIcon from '@mui/icons-material/Bolt';
import NatureIcon from '@mui/icons-material/Nature';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import BalanceIcon from '@mui/icons-material/Balance';
import DeleteIcon from '@mui/icons-material/Delete';
import DirectionsIcon from '@mui/icons-material/Directions';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import ClearIcon from '@mui/icons-material/Clear';
import WbSunnyIcon from '@mui/icons-material/WbSunny';
import GrainIcon from '@mui/icons-material/Grain';
import AcUnitIcon from '@mui/icons-material/AcUnit';

const SIDEBAR_BG = '#1a1a2e';
const PANEL_BG = '#16213e';
const BORDER = '#2d2d4e';
const ACCENT = '#6366f1';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

const hourMarks = [
  { value: 0, label: '12am' },
  { value: 6, label: '6am' },
  { value: 12, label: 'Noon' },
  { value: 17, label: '5pm' },
  { value: 22, label: '10pm' },
];

const modeOptions = [
  { value: 'fastest', label: 'Fastest', icon: <BoltIcon sx={{ fontSize: 18 }} />, color: '#3b82f6' },
  { value: 'eco', label: 'Eco / Green', icon: <NatureIcon sx={{ fontSize: 18 }} />, color: '#22c55e' },
  { value: 'toll_free', label: 'Toll-Free', icon: <AttachMoneyIcon sx={{ fontSize: 18 }} />, color: '#f97316' },
  { value: 'balanced', label: 'Balanced', icon: <BalanceIcon sx={{ fontSize: 18 }} />, color: '#a855f7' },
];

const weatherOptions = [
  { value: 0, label: 'Clear', icon: <WbSunnyIcon sx={{ fontSize: 18 }} /> },
  { value: 1, label: 'Rain', icon: <GrainIcon sx={{ fontSize: 18 }} /> },
  { value: 2, label: 'Snow', icon: <AcUnitIcon sx={{ fontSize: 18 }} /> },
];

function SectionTitle({ children }) {
  return (
    <Typography
      variant="caption"
      sx={{
        color: '#7c7ca0',
        fontWeight: 700,
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        mb: 0.5,
        display: 'block',
      }}
    >
      {children}
    </Typography>
  );
}

function StatusBadge({ originPoint, destPoint }) {
  let text, color;
  if (!originPoint) {
    text = '📍 Click map to set origin (A)';
    color = '#f59e0b';
  } else if (!destPoint) {
    text = '📍 Click map to set destination (B)';
    color = '#3b82f6';
  } else {
    text = '✅ Ready to calculate';
    color = '#22c55e';
  }
  return (
    <Box
      sx={{
        mt: 1,
        px: 1.5,
        py: 0.75,
        borderRadius: 1,
        background: `${color}18`,
        border: `1px solid ${color}44`,
        fontSize: '0.78rem',
        color,
        fontWeight: 500,
      }}
    >
      {text}
    </Box>
  );
}

export default function ControlPanel({
  mode, setMode,
  hour, setHour,
  dayOfWeek, setDayOfWeek,
  weatherCode, setWeatherCode,
  numVehicles, setNumVehicles,
  activeTab, setActiveTab,
  originPoint, destPoint,
  vrpStops,
  onCalculateRoute,
  onSolveVRP,
  onClear,
  onRemoveStop,
  isLoading,
}) {
  return (
    <Box
      sx={{
        background: SIDEBAR_BG,
        color: '#e2e8f0',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
      }}
    >
      {/* Header */}
      <Box
        sx={{
          px: 2,
          pt: 2,
          pb: 1,
          borderBottom: `1px solid ${BORDER}`,
          background: '#12122a',
        }}
      >
        <Stack direction="row" alignItems="center" spacing={1}>
          <DirectionsIcon sx={{ color: ACCENT, fontSize: 26 }} />
          <Box>
            <Typography variant="subtitle1" sx={{ fontWeight: 700, lineHeight: 1.2, color: '#e2e8f0' }}>
              AI Fleet Router
            </Typography>
            <Typography variant="caption" sx={{ color: '#7c7ca0' }}>
              Optimal path &amp; fleet routing
            </Typography>
          </Box>
        </Stack>
      </Box>

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onChange={(_, v) => setActiveTab(v)}
        sx={{
          borderBottom: `1px solid ${BORDER}`,
          minHeight: 40,
          '& .MuiTab-root': { color: '#7c7ca0', minHeight: 40, fontSize: '0.8rem', fontWeight: 600 },
          '& .Mui-selected': { color: '#e2e8f0' },
          '& .MuiTabs-indicator': { backgroundColor: ACCENT },
        }}
      >
        <Tab icon={<DirectionsIcon sx={{ fontSize: 16 }} />} iconPosition="start" label="Single Route" />
        <Tab icon={<LocalShippingIcon sx={{ fontSize: 16 }} />} iconPosition="start" label="Fleet VRP" />
      </Tabs>

      {/* Tab 0 — Single Route */}
      {activeTab === 0 && (
        <Box sx={{ px: 2, py: 2, flex: 1, overflowY: 'auto' }}>
          {/* Mode */}
          <SectionTitle>Optimization Mode</SectionTitle>
          <RadioGroup value={mode} onChange={e => setMode(e.target.value)}>
            {modeOptions.map(opt => (
              <FormControlLabel
                key={opt.value}
                value={opt.value}
                control={
                  <Radio
                    size="small"
                    sx={{ color: BORDER, '&.Mui-checked': { color: opt.color }, py: 0.5 }}
                  />
                }
                label={
                  <Stack direction="row" alignItems="center" spacing={0.75}>
                    <Box sx={{ color: opt.color }}>{opt.icon}</Box>
                    <Typography variant="body2" sx={{ color: '#e2e8f0', fontWeight: mode === opt.value ? 700 : 400 }}>
                      {opt.label}
                    </Typography>
                  </Stack>
                }
                sx={{
                  mx: 0,
                  mb: 0.5,
                  px: 1,
                  borderRadius: 1,
                  border: `1px solid ${mode === opt.value ? opt.color + '88' : BORDER}`,
                  background: mode === opt.value ? `${opt.color}12` : 'transparent',
                  transition: 'all 0.2s',
                }}
              />
            ))}
          </RadioGroup>

          <Divider sx={{ borderColor: BORDER, my: 2 }} />

          {/* Hour slider */}
          <SectionTitle>Departure Time — {hour}:00</SectionTitle>
          <Box sx={{ px: 1 }}>
            <Slider
              value={hour}
              min={0}
              max={23}
              step={1}
              marks={hourMarks}
              onChange={(_, v) => setHour(v)}
              sx={{
                color: ACCENT,
                '& .MuiSlider-markLabel': { color: '#7c7ca0', fontSize: '0.65rem' },
              }}
            />
          </Box>

          <Divider sx={{ borderColor: BORDER, my: 2 }} />

          {/* Day of week */}
          <SectionTitle>Day of Week</SectionTitle>
          <FormControl fullWidth size="small" sx={{ mt: 0.5 }}>
            <Select
              value={dayOfWeek}
              onChange={e => setDayOfWeek(e.target.value)}
              sx={{
                color: '#e2e8f0',
                background: PANEL_BG,
                borderColor: BORDER,
                '& .MuiOutlinedInput-notchedOutline': { borderColor: BORDER },
                '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: ACCENT },
                '& .MuiSvgIcon-root': { color: '#7c7ca0' },
              }}
            >
              {DAYS.map((day, idx) => (
                <MenuItem key={idx} value={idx + 1}>
                  {day}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Divider sx={{ borderColor: BORDER, my: 2 }} />

          {/* Weather */}
          <SectionTitle>Weather Conditions</SectionTitle>
          <RadioGroup
            row
            value={weatherCode}
            onChange={e => setWeatherCode(Number(e.target.value))}
            sx={{ gap: 0.5 }}
          >
            {weatherOptions.map(opt => (
              <FormControlLabel
                key={opt.value}
                value={opt.value}
                control={
                  <Radio
                    size="small"
                    sx={{
                      color: BORDER,
                      '&.Mui-checked': { color: ACCENT },
                      display: 'none',
                    }}
                  />
                }
                label={
                  <Stack
                    direction="row"
                    alignItems="center"
                    spacing={0.5}
                    sx={{
                      px: 1.25,
                      py: 0.5,
                      borderRadius: 1,
                      border: `1px solid ${weatherCode === opt.value ? ACCENT : BORDER}`,
                      background: weatherCode === opt.value ? `${ACCENT}20` : PANEL_BG,
                      cursor: 'pointer',
                      fontSize: '0.78rem',
                      color: '#e2e8f0',
                      transition: 'all 0.2s',
                    }}
                    onClick={() => setWeatherCode(opt.value)}
                  >
                    {opt.icon}
                    <span>{opt.label}</span>
                  </Stack>
                }
                sx={{ mx: 0 }}
              />
            ))}
          </RadioGroup>

          <Divider sx={{ borderColor: BORDER, my: 2 }} />

          {/* Status */}
          <StatusBadge originPoint={originPoint} destPoint={destPoint} />

          {/* Action buttons */}
          <Stack direction="row" spacing={1} sx={{ mt: 1.5 }}>
            <Button
              variant="contained"
              fullWidth
              disabled={!originPoint || !destPoint || isLoading}
              onClick={onCalculateRoute}
              startIcon={isLoading ? <CircularProgress size={16} color="inherit" /> : <DirectionsIcon />}
              sx={{
                background: ACCENT,
                fontWeight: 700,
                '&:hover': { background: '#4f46e5' },
                '&.Mui-disabled': { background: `${ACCENT}44`, color: '#7c7ca0' },
              }}
            >
              {isLoading ? 'Calculating…' : 'Calculate'}
            </Button>
            <Button
              variant="outlined"
              onClick={onClear}
              startIcon={<ClearIcon />}
              sx={{
                borderColor: BORDER,
                color: '#7c7ca0',
                '&:hover': { borderColor: '#ef4444', color: '#ef4444' },
              }}
            >
              Clear
            </Button>
          </Stack>
        </Box>
      )}

      {/* Tab 1 — Fleet VRP */}
      {activeTab === 1 && (
        <Box sx={{ px: 2, py: 2, flex: 1, overflowY: 'auto' }}>
          <Typography variant="body2" sx={{ color: '#7c7ca0', mb: 2, lineHeight: 1.6 }}>
            Click on the map to add stops. The <strong style={{ color: '#f59e0b' }}>first click</strong> sets the
            depot. Subsequent clicks add delivery stops.
          </Typography>

          {/* Number of vehicles */}
          <SectionTitle>Number of Vehicles — {numVehicles}</SectionTitle>
          <Box sx={{ px: 1, mb: 2 }}>
            <Slider
              value={numVehicles}
              min={1}
              max={5}
              step={1}
              marks={[1, 2, 3, 4, 5].map(v => ({ value: v, label: String(v) }))}
              onChange={(_, v) => setNumVehicles(v)}
              sx={{
                color: '#22c55e',
                '& .MuiSlider-markLabel': { color: '#7c7ca0', fontSize: '0.7rem' },
              }}
            />
          </Box>

          <Divider sx={{ borderColor: BORDER, my: 1.5 }} />

          {/* Stop list */}
          <SectionTitle>Stops ({vrpStops.length})</SectionTitle>
          {vrpStops.length === 0 ? (
            <Typography variant="caption" sx={{ color: '#7c7ca0' }}>
              No stops added yet. Click the map.
            </Typography>
          ) : (
            <List dense disablePadding>
              {vrpStops.map((stop, idx) => (
                <ListItem
                  key={idx}
                  disablePadding
                  secondaryAction={
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={() => onRemoveStop(idx)}
                      sx={{ color: '#7c7ca0', '&:hover': { color: '#ef4444' } }}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  }
                  sx={{
                    mb: 0.5,
                    px: 1,
                    py: 0.25,
                    borderRadius: 1,
                    border: `1px solid ${BORDER}`,
                    background: PANEL_BG,
                  }}
                >
                  <Box
                    sx={{
                      width: 22,
                      height: 22,
                      borderRadius: '50%',
                      background: idx === 0 ? '#f59e0b' : '#8b5cf6',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 10,
                      fontWeight: 700,
                      color: '#fff',
                      mr: 1,
                      flexShrink: 0,
                    }}
                  >
                    {idx === 0 ? '★' : idx}
                  </Box>
                  <ListItemText
                    primary={idx === 0 ? 'Depot' : `Stop ${idx}`}
                    secondary={`${stop[0].toFixed(4)}, ${stop[1].toFixed(4)}`}
                    primaryTypographyProps={{ fontSize: '0.8rem', color: '#e2e8f0', fontWeight: 600 }}
                    secondaryTypographyProps={{ fontSize: '0.7rem', color: '#7c7ca0' }}
                  />
                </ListItem>
              ))}
            </List>
          )}

          <Divider sx={{ borderColor: BORDER, my: 1.5 }} />

          <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
            <Button
              variant="contained"
              fullWidth
              disabled={vrpStops.length < 2 || isLoading}
              onClick={onSolveVRP}
              startIcon={
                isLoading ? <CircularProgress size={16} color="inherit" /> : <LocalShippingIcon />
              }
              sx={{
                background: '#22c55e',
                color: '#0f0f1a',
                fontWeight: 700,
                '&:hover': { background: '#16a34a' },
                '&.Mui-disabled': { background: '#22c55e44', color: '#7c7ca0' },
              }}
            >
              {isLoading ? 'Solving…' : 'Solve Fleet Route'}
            </Button>
            <Button
              variant="outlined"
              onClick={onClear}
              startIcon={<ClearIcon />}
              sx={{
                borderColor: BORDER,
                color: '#7c7ca0',
                '&:hover': { borderColor: '#ef4444', color: '#ef4444' },
              }}
            >
              Clear
            </Button>
          </Stack>

          {vrpStops.length < 2 && vrpStops.length > 0 && (
            <Typography variant="caption" sx={{ color: '#f59e0b', mt: 1, display: 'block' }}>
              Add at least one delivery stop after the depot.
            </Typography>
          )}
        </Box>
      )}
    </Box>
  );
}
