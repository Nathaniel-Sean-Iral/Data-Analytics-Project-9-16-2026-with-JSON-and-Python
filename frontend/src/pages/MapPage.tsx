import { useEffect, useMemo, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Building2, Users, Siren, Layers, MapPin } from 'lucide-react';
import { PageHeader } from '@/components/ui/card';
import { Spinner } from '@/components/ui/button';
import { useAsync } from '@/lib/useAsync';
import { fetchHouseholds, fetchCenters, fetchIncidents } from '@/api/services';
import { cn } from '@/lib/cn';
import { formatDateTime } from '@/lib/labels';
import { MUNICIPALITY_CENTER } from '@/lib/location';
import type { IncidentSeverity } from '@/api/types';

maplibregl.setWorkerUrl(workerUrl);

const MAP_STYLES = [
  'https://tiles.openfreemap.org/styles/liberty',
  'https://demotiles.maplibre.org/style.json',
] as const;
const DEFAULT_CENTER: [number, number] = [MUNICIPALITY_CENTER[1], MUNICIPALITY_CENTER[0]];

const SEVERITY_COLOR: Record<IncidentSeverity, string> = {
  low: '#10b981',
  moderate: '#f59e0b',
  high: '#f97316',
  critical: '#e11d3f',
};

interface LayerState {
  households: boolean;
  centers: boolean;
  incidents: boolean;
}

type MapPointItem = { id: number; lat?: number; lng?: number };

function buildPointsGeoJson<T extends MapPointItem>(
  items: T[],
  kind: 'household' | 'center' | 'incident',
  extraBuilder: (item: T) => Record<string, string | number | boolean | null | undefined>,
) {
  return {
    type: 'FeatureCollection' as const,
    features: items.map((item) => ({
      type: 'Feature' as const,
      geometry: {
        type: 'Point' as const,
        coordinates: [item.lng, item.lat] as [number, number],
      },
      properties: {
        id: item.id,
        kind,
        ...extraBuilder(item),
      },
    })),
  };
}

function buildIncidentZonesGeoJson(
  items: Array<{
    id: number;
    lat?: number;
    lng?: number;
    severity?: IncidentSeverity;
    title?: string;
    barangay?: string;
    status?: string;
    reported_at?: string;
    zone_geojson?: import('@/api/types').GeoJsonGeometry;
  }>,
) {
  // Use saved zone polygons when present; otherwise fall back to a small circle
  // around the incident point so every incident still contributes a shape.
  const zones = items
    .filter((incident) => incident.zone_geojson && incident.zone_geojson.type)
    .map((incident) => ({
      type: 'Feature' as const,
      geometry: incident.zone_geojson as GeoJSON.Geometry,
      properties: {
        id: incident.id,
        kind: 'incident-zone',
        title: incident.title ?? 'Incident',
        severity: incident.severity ?? 'low',
        barangay: incident.barangay ?? '',
        status: incident.status ?? 'reported',
        reported_at: incident.reported_at ?? '',
      },
    }));

  const points = 24;
  const radius = 0.0018;
  const circles = items
    .filter((incident) => Number.isFinite(incident.lat) && Number.isFinite(incident.lng))
    .map((incident) => {
      const centerLng = Number(incident.lng);
      const centerLat = Number(incident.lat);
      const ring = Array.from({ length: points + 1 }, (_, index) => {
        const angle = (index / points) * Math.PI * 2;
        const lat = centerLat + Math.cos(angle) * radius;
        const lng = centerLng + Math.sin(angle) * radius;
        return [lng, lat] as [number, number];
      });

      return {
        type: 'Feature' as const,
        geometry: {
          type: 'Polygon' as const,
          coordinates: [ring],
        },
        properties: {
          id: incident.id,
          kind: 'incident-zone',
          title: incident.title ?? 'Incident',
          severity: incident.severity ?? 'low',
          barangay: incident.barangay ?? '',
          status: incident.status ?? 'reported',
          reported_at: incident.reported_at ?? '',
        },
      };
    });

  return {
    type: 'FeatureCollection' as const,
    features: [...zones, ...circles],
  };
}

export function MapPage() {
  const households = useAsync(() => fetchHouseholds());
  const centers = useAsync(() => fetchCenters());
  const incidents = useAsync(() => fetchIncidents());
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [layers, setLayers] = useState<LayerState>({ households: true, centers: true, incidents: true });

  const loading = households.loading || centers.loading || incidents.loading;
  const validHouseholds = (households.data?.items ?? []).filter((h) => Number.isFinite(h.lat) && Number.isFinite(h.lng));
  const validCenters = (centers.data ?? []).filter((c) => Number.isFinite(c.lat) && Number.isFinite(c.lng));
  const validIncidents = (incidents.data ?? []).filter((inc) => Number.isFinite(inc.lat) && Number.isFinite(inc.lng));

  const householdGeoJson = useMemo(
    () =>
      buildPointsGeoJson(validHouseholds, 'household', (h) => ({
        household_no: h.household_no,
        head_name: h.head_name,
        address: h.address,
        barangay: h.barangay,
        size: h.size,
      })),
    [validHouseholds],
  );

  const centerGeoJson = useMemo(
    () =>
      buildPointsGeoJson(validCenters, 'center', (c) => ({
        name: c.name,
        address: c.address,
        barangay: c.barangay,
        current_occupants: c.current_occupants,
        capacity: c.capacity,
      })),
    [validCenters],
  );

  const incidentGeoJson = useMemo(
    () =>
      buildPointsGeoJson(validIncidents, 'incident', (inc) => ({
        title: inc.title,
        severity: inc.severity,
        status: inc.status,
        barangay: inc.barangay,
        type: inc.type,
        reported_at: inc.reported_at,
      })),
    [validIncidents],
  );

  const incidentZoneGeoJson = useMemo(() => buildIncidentZonesGeoJson(validIncidents), [validIncidents]);

  const toggle = (key: keyof LayerState) =>
    setLayers((prev) => ({ ...prev, [key]: !prev[key] }));

  const layerToggles: Array<{ key: keyof LayerState; label: string; icon: React.ReactNode }> = [
    { key: 'households', label: 'Households', icon: <Users className="h-3.5 w-3.5" /> },
    { key: 'centers', label: 'Evacuation centers', icon: <Building2 className="h-3.5 w-3.5" /> },
    { key: 'incidents', label: 'Incidents', icon: <Siren className="h-3.5 w-3.5" /> },
  ];

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: MAP_STYLES[0],
      center: DEFAULT_CENTER,
      zoom: 12,
      attributionControl: { compact: true },
    });

    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: true, showZoom: true }), 'top-right');
    map.addControl(new maplibregl.ScaleControl(), 'bottom-left');

    let activeStyleIndex = 0;

    const addMapLayers = () => {
      if (!map.getSource('households')) {
        map.addSource('households', { type: 'geojson', data: householdGeoJson });
      } else {
        (map.getSource('households') as maplibregl.GeoJSONSource | undefined)?.setData(householdGeoJson as GeoJSON.GeoJSON);
      }

      if (!map.getSource('centers')) {
        map.addSource('centers', { type: 'geojson', data: centerGeoJson });
      } else {
        (map.getSource('centers') as maplibregl.GeoJSONSource | undefined)?.setData(centerGeoJson as GeoJSON.GeoJSON);
      }

      if (!map.getSource('incidents')) {
        map.addSource('incidents', { type: 'geojson', data: incidentGeoJson });
      } else {
        (map.getSource('incidents') as maplibregl.GeoJSONSource | undefined)?.setData(incidentGeoJson as GeoJSON.GeoJSON);
      }

      if (!map.getSource('incident-zones')) {
        map.addSource('incident-zones', { type: 'geojson', data: incidentZoneGeoJson });
      } else {
        (map.getSource('incident-zones') as maplibregl.GeoJSONSource | undefined)?.setData(incidentZoneGeoJson as GeoJSON.GeoJSON);
      }

      if (!map.getLayer('households-layer')) {
        map.addLayer({
          id: 'households-layer',
          type: 'circle',
          source: 'households',
          paint: {
            'circle-radius': 6,
            'circle-color': '#0f172a',
            'circle-opacity': 0.9,
            'circle-stroke-color': '#ffffff',
            'circle-stroke-width': 1,
          },
        });
      }

      if (!map.getLayer('centers-layer')) {
        map.addLayer({
          id: 'centers-layer',
          type: 'circle',
          source: 'centers',
          paint: {
            'circle-radius': 10,
            'circle-color': '#2563eb',
            'circle-opacity': 0.9,
            'circle-stroke-color': '#ffffff',
            'circle-stroke-width': 1,
          },
        });
      }

      if (!map.getLayer('incident-zones-layer')) {
        map.addLayer({
          id: 'incident-zones-layer',
          type: 'fill',
          source: 'incident-zones',
          paint: {
            'fill-color': ['match', ['get', 'severity'], 'low', '#10b981', 'moderate', '#f59e0b', 'high', '#f97316', 'critical', '#e11d3f', '#94a3b8'],
            'fill-opacity': 0.18,
            'fill-outline-color': ['match', ['get', 'severity'], 'low', '#10b981', 'moderate', '#f59e0b', 'high', '#f97316', 'critical', '#e11d3f', '#94a3b8'],
          },
        });
      }

      if (!map.getLayer('incidents-layer')) {
        map.addLayer({
          id: 'incidents-layer',
          type: 'circle',
          source: 'incidents',
          paint: {
            'circle-radius': ['case', ['==', ['get', 'severity'], 'critical'], 16, ['==', ['get', 'severity'], 'high'], 12, ['==', ['get', 'severity'], 'moderate'], 10, 8],
            'circle-color': ['match', ['get', 'severity'], 'low', '#10b981', 'moderate', '#f59e0b', 'high', '#f97316', 'critical', '#e11d3f', '#94a3b8'],
            'circle-opacity': 0.35,
            'circle-stroke-color': ['match', ['get', 'severity'], 'low', '#10b981', 'moderate', '#f59e0b', 'high', '#f97316', 'critical', '#e11d3f', '#94a3b8'],
            'circle-stroke-width': 1.5,
          },
        });
      }

      const showPopup = (layerId: string, sourceName: 'households' | 'centers' | 'incidents' | 'incident-zones') => {
        map.on('click', layerId, (event: any) => {
          const feature = event.features?.[0];
          if (!feature?.properties) return;

          const props = feature.properties as Record<string, string | number | undefined>;
          let html = '';

          if (sourceName === 'households') {
            html = `
              <div style="min-width:220px; font-family: system-ui, sans-serif;">
                <div style="font-size: 14px; font-weight: 700; color: #0f172a; margin-bottom: 4px;">${props.head_name ?? 'Household'}</div>
                <div style="font-size: 11px; color: #475569; margin-bottom: 6px;">${props.household_no ?? ''}</div>
                <div style="font-size: 12px; color: #334155; line-height: 1.5;">${props.address ?? ''}</div>
                <div style="font-size: 11px; color: #475569; margin-top: 6px;">Size: ${props.size ?? 0} · ${props.barangay ?? ''}</div>
              </div>
            `;
          }

          if (sourceName === 'centers') {
            const occupancy = Number(props.current_occupants ?? 0);
            const capacity = Number(props.capacity ?? 0);
            const load = capacity > 0 ? Math.round((occupancy / capacity) * 100) : 0;
            html = `
              <div style="min-width:220px; font-family: system-ui, sans-serif;">
                <div style="font-size: 14px; font-weight: 700; color: #0f172a; margin-bottom: 4px;">${props.name ?? 'Evacuation Center'}</div>
                <div style="font-size: 12px; color: #334155; line-height: 1.5;">${props.barangay ?? ''} · ${props.address ?? ''}</div>
                <div style="font-size: 11px; color: #475569; margin-top: 6px;">Occupancy: <b>${occupancy}</b> / ${capacity} · Load: <b>${load}%</b></div>
              </div>
            `;
          }

          if (sourceName === 'incidents' || sourceName === 'incident-zones') {
            const severity = String(props.severity ?? 'low');
            const color = SEVERITY_COLOR[severity as IncidentSeverity] ?? '#94a3b8';
            html = `
              <div style="min-width:220px; font-family: system-ui, sans-serif;">
                <div style="font-size: 14px; font-weight: 700; color: #0f172a; margin-bottom: 4px;">${props.title ?? 'Incident'}</div>
                <div style="display:flex; gap:6px; flex-wrap:wrap; margin-bottom:6px;">
                  <span style="display:inline-block; border-radius:9999px; background:${color}22; color:${color}; font-weight:600; font-size:10px; padding:3px 8px; text-transform:capitalize;">${severity}</span>
                  <span style="display:inline-block; border-radius:9999px; background:#e2e8f0; color:#334155; font-weight:600; font-size:10px; padding:3px 8px; text-transform:capitalize;">${String(props.status ?? 'reported')}</span>
                </div>
                <div style="font-size: 12px; color: #334155;">${props.barangay ?? ''}</div>
                <div style="font-size: 11px; color: #475569; margin-top: 4px;">${formatDateTime(String(props.reported_at ?? ''))}</div>
              </div>
            `;
          }

          new maplibregl.Popup({ closeButton: true, closeOnClick: true })
            .setLngLat(event.lngLat)
            .setHTML(html)
            .addTo(map);
        });

        map.on('mouseenter', layerId, () => {
          map.getCanvas().style.cursor = 'pointer';
        });

        map.on('mouseleave', layerId, () => {
          map.getCanvas().style.cursor = '';
        });
      };

      showPopup('households-layer', 'households');
      showPopup('centers-layer', 'centers');
      showPopup('incident-zones-layer', 'incident-zones');
      showPopup('incidents-layer', 'incidents');
    };

    const maybeFallbackStyle = (event: any) => {
      const message = event?.error?.message ?? event?.message ?? '';
      if (activeStyleIndex === 0 && /style|tile|fetch|network/i.test(message)) {
        activeStyleIndex = 1;
        map.setStyle(MAP_STYLES[1]);
      }
    };

    map.on('style.load', addMapLayers);
    map.on('error', maybeFallbackStyle);
    map.once('load', addMapLayers);

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [householdGeoJson, centerGeoJson, incidentGeoJson, incidentZoneGeoJson]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const layerOrder: Array<keyof LayerState> = ['households', 'centers', 'incidents'];
    layerOrder.forEach((key) => {
      const id = `${key}-layer`;
      const visibility = layers[key] ? 'visible' : 'none';
      if (map.getLayer(id)) {
        map.setLayoutProperty(id, 'visibility', visibility);
      }
    });

    if (map.getLayer('incident-zones-layer')) {
      map.setLayoutProperty('incident-zones-layer', 'visibility', layers.incidents ? 'visible' : 'none');
    }
  }, [layers]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const updateSource = (id: 'households' | 'centers' | 'incidents' | 'incident-zones', data: unknown) => {
      const source = map.getSource(id) as maplibregl.GeoJSONSource | undefined;
      if (source) {
        source.setData(data as GeoJSON.GeoJSON);
      }
    };

    updateSource('households', householdGeoJson);
    updateSource('centers', centerGeoJson);
    updateSource('incidents', incidentGeoJson);
    updateSource('incident-zones', incidentZoneGeoJson);
  }, [householdGeoJson, centerGeoJson, incidentGeoJson, incidentZoneGeoJson]);

  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title="Operations Map"
        description="Households, evacuation centers and incident zones mapped on OpenFreeMap with MapLibre."
        icon={<MapPin className="h-5 w-5" />}
      />

      <div className="relative min-h-[70vh] flex-1 overflow-hidden rounded-xl border border-slate-200 shadow-sm">
        {loading && (
          <div className="absolute inset-0 z-[500] flex items-center justify-center bg-white/80 backdrop-blur-sm">
            <Spinner className="h-8 w-8 text-brand-600" />
          </div>
        )}

        <div ref={mapContainer} className="absolute inset-0 h-full w-full" />
        <div className="absolute left-3 top-3 z-[600] rounded-xl border border-slate-200 bg-white p-3 shadow-lg">
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-slate-700">
            <Layers className="h-3.5 w-3.5 text-brand-600" />
            Data layers
          </div>
          <div className="space-y-1.5">
            {layerToggles.map((lt) => (
              <button
                key={lt.key}
                onClick={() => toggle(lt.key)}
                className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-xs font-medium text-slate-700 transition-colors hover:bg-slate-50"
              >
                <span
                  className={cn(
                    'flex h-4 w-4 items-center justify-center rounded border',
                    layers[lt.key] ? 'border-brand-600 bg-brand-600 text-white' : 'border-slate-300 bg-white',
                  )}
                >
                  {layers[lt.key] && (
                    <svg viewBox="0 0 24 24" className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth="3">
                      <path d="M20 6 9 17l-5-5" />
                    </svg>
                  )}
                </span>
                {lt.icon}
                {lt.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}