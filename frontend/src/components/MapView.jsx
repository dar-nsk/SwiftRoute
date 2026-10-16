import React, { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet default marker icon broken by webpack
L.Icon.Default.mergeOptions({
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const MODE_COLORS = {
  fastest: '#3b82f6',
  eco: '#22c55e',
  toll_free: '#f97316',
  balanced: '#a855f7',
};

const VRP_COLORS = ['#ef4444', '#3b82f6', '#22c55e', '#f59e0b', '#8b5cf6'];

// Custom colored DivIcon factory
const makeColoredIcon = (color, label) =>
  L.divIcon({
    className: '',
    html: `<div style="
      width:32px;height:32px;border-radius:50%;
      background:${color};border:3px solid #fff;
      display:flex;align-items:center;justify-content:center;
      font-weight:bold;font-size:13px;color:#fff;
      box-shadow:0 2px 6px rgba(0,0,0,0.5);">
      ${label}
    </div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16],
  });

const originIcon = makeColoredIcon('#22c55e', 'A');
const destIcon = makeColoredIcon('#ef4444', 'B');

// Auto-fit map bounds to the route
function FitBounds({ routeData, vrpData, originPoint, destPoint }) {
  const map = useMap();

  useEffect(() => {
    if (routeData && routeData.coordinates && routeData.coordinates.length > 1) {
      const bounds = L.latLngBounds(routeData.coordinates);
      map.fitBounds(bounds, { padding: [40, 40] });
    } else if (originPoint && destPoint) {
      const bounds = L.latLngBounds([originPoint, destPoint]);
      map.fitBounds(bounds, { padding: [80, 80] });
    }
  }, [routeData, map, originPoint, destPoint]);

  useEffect(() => {
    if (vrpData && vrpData.routes) {
      const allCoords = vrpData.routes.flat();
      if (allCoords.length > 0) {
        const bounds = L.latLngBounds(allCoords);
        map.fitBounds(bounds, { padding: [40, 40] });
      }
    }
  }, [vrpData, map]);

  return null;
}

// Handles map click events and forwards them to the parent callback
function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click(e) {
      onMapClick([e.latlng.lat, e.latlng.lng]);
    },
  });
  return null;
}

export default function MapView({
  originPoint,
  destPoint,
  routeData,
  vrpData,
  onMapClick,
  mode,
  vrpStops,
}) {
  return (
    <MapContainer
      center={[40.758, -73.9855]}
      zoom={13}
      style={{ height: '100%', width: '100%' }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <MapClickHandler onMapClick={onMapClick} />

      <FitBounds
        routeData={routeData}
        vrpData={vrpData}
        originPoint={originPoint}
        destPoint={destPoint}
      />

      {/* Origin marker */}
      {originPoint && (
        <Marker position={originPoint} icon={originIcon}>
          <Popup>
            <span style={{ color: '#22c55e', fontWeight: 'bold' }}>Origin</span>
            <br />
            {originPoint[0].toFixed(5)}, {originPoint[1].toFixed(5)}
          </Popup>
        </Marker>
      )}

      {/* Destination marker */}
      {destPoint && (
        <Marker position={destPoint} icon={destIcon}>
          <Popup>
            <span style={{ color: '#ef4444', fontWeight: 'bold' }}>Destination</span>
            <br />
            {destPoint[0].toFixed(5)}, {destPoint[1].toFixed(5)}
          </Popup>
        </Marker>
      )}

      {/* Single route polyline — API returns coordinates as [[lat, lon], ...] */}
      {routeData && routeData.coordinates && routeData.coordinates.length > 1 && (
        <Polyline
          positions={routeData.coordinates}
          color={MODE_COLORS[mode] || '#a855f7'}
          weight={5}
          opacity={0.85}
        >
          <Popup>
            <div style={{ color: '#333' }}>
              <strong>Route</strong>
              <br />
              Distance: {(routeData.distance_m / 1000).toFixed(2)} km
              <br />
              ETA: {Math.round(routeData.time_sec / 60)} min
            </div>
          </Popup>
        </Polyline>
      )}

      {/* VRP stop markers */}
      {vrpStops && vrpStops.map((stop, idx) => {
        const isDepot = idx === 0;
        const icon = makeColoredIcon(isDepot ? '#f59e0b' : '#8b5cf6', isDepot ? '★' : String(idx));
        return (
          <Marker key={`vrp-stop-${idx}`} position={stop} icon={icon}>
            <Popup>
              <span style={{ fontWeight: 'bold' }}>
                {isDepot ? 'Depot' : `Stop ${idx}`}
              </span>
              <br />
              {stop[0].toFixed(5)}, {stop[1].toFixed(5)}
            </Popup>
          </Marker>
        );
      })}

      {/* VRP vehicle routes — routes is List[List[List[float]]] i.e. [[lat,lon],...] per vehicle */}
      {vrpData && vrpData.routes && vrpData.routes.map((coordList, vIdx) => {
        const color = VRP_COLORS[vIdx % VRP_COLORS.length];
        const stat = vrpData.vehicle_stats?.[vIdx];
        if (!coordList || coordList.length < 2) return null;
        return (
          <Polyline
            key={`vrp-route-${vIdx}`}
            positions={coordList}
            color={color}
            weight={4}
            opacity={0.8}
            dashArray={vIdx > 0 ? '8 4' : null}
          >
            <Popup>
              <div style={{ color: '#333' }}>
                <strong style={{ color }}>Vehicle {vIdx + 1}</strong>
                <br />
                Stops: {stat?.stops ?? 0}
                <br />
                Distance: {stat ? (stat.distance_m / 1000).toFixed(2) : '–'} km
                <br />
                ETA: {stat ? Math.round(stat.time_sec / 60) : '–'} min
              </div>
            </Popup>
          </Polyline>
        );
      })}
    </MapContainer>
  );
}
