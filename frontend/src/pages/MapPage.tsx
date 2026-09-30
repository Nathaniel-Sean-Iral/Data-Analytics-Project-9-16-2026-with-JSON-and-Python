import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Building2, Users, Siren, Layers, MapPin, Search, X, LocateFixed, Crosshair } from 'lucide-react';
import { PageHeader } from '@/components/ui/card';
import { Spinner } from '@/components/ui/button';
import { Select } from '@/components/ui/form';
import { useAsync } from '@/lib/useAsync';
import { fetchAllHouseholds, fetchCenters, fetchIncidents } from '@/api/services';
import { BARANGAYS } from '@/api/mock';
import { cn } from '@/lib/cn';
import { formatDateTime } from '@/lib/labels';
import { MUNICIPALITY_BOUNDS, MUNICIPALITY_CENTER } from '@/lib/location';
import type { GeoJSON as GeoJSONData } from 'geojson';
import type { GeoJsonGeometry, IncidentSeverity } from '@/api/types';

maplibregl.setWorkerUrl(workerUrl);

const MAP_STYLES = [
  'https://tiles.openfreemap.org/styles/liberty',
  'https://demotiles.maplibre.org/style.json',
] as const;
const DEFAULT_CENTER: [number, number] = [MUNICIPALITY_CENTER[1], MUNICIPALITY_CENTER[0]];
const MUNICIPALITY_BOUNDS_TUPLE: [[number, number], [number, number]] = [
  [MUNICIPALITY_BOUNDS.minLng, MUNICIPALITY_BOUNDS.minLat],
  [MUNICIPALITY_BOUNDS.maxLng, MUNICIPALITY_BOUNDS.maxLat],
];
const MAX_SEARCH_RESULTS = 8;

const SEVERITY_COLOR: Record<IncidentSeverity, string> = {
  low: '#10b981',
  moderate: '#f59e0b',
  high: '#f97316',
  critical: '#e11d3f',
};
const SEVERITY_ORDER: IncidentSeverity[] = ['low', 'moderate', 'high', 'critical'];

interface LayerState {
  households: boolean;
  centers: boolean;
  incidents: boolean;
}

type PointKind = 'household' | 'center' | 'incident';

interface SearchEntry {
  key: string;
  kind: PointKind;
  title: string;
  subtitle: string;
  lat: number;
  lng: number;
  props: Record<string, string | number>;
}

type MapPointItem = { id: number; lat?: number; lng?: number };

/** `Number.isFinite` is not a type guard, so narrow coordinates explicitly. */
function hasCoordinates<T extends { lat?: number; lng?: number }>(item: T): item is T & { lat: number; lng: number } {
  return Number.isFinite(item.lat) && Number.isFinite(item.lng);
}

function escapeHtml(value: unknown): string {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

type PolygonalGeometry = Extract<GeoJsonGeometry, { type: 'Polygon' | 'MultiPolygon' }>;

function isPolygonGeometry(geometry?: GeoJsonGeometry): geometry is PolygonalGeometry {
  return geometry?.type === 'Polygon' || geometry?.type === 'MultiPolygon';
}

function buildPointsGeoJson<T extends MapPointItem>(
  items: T[],
  kind: PointKind,
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
    .filter((incident) => isPolygonGeometry(incident.zone_geojson))
    .map((incident) => ({
      type: 'Feature' as const,
      geometry: incident.zone_geojson,
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
    .filter(
      (incident) =>
        !isPolygonGeometry(incident.zone_geojson) && Number.isFinite(incident.lat) && Number.isFinite(incident.lng),
    )
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

/** Shared by map clicks and search results so both popups look identical. */
function buildPopupHtml(
  kind: 'households' | 'centers' | 'incidents' | 'incident-zones',
  rawProps: Record<string, string | number | undefined>,
): string {
  const props = rawProps;

  if (kind === 'households') {
    return `
      <div style="min-width:220px; font-family: system-ui, sans-serif;">
        <div style="font-size: 14px; font-weight: 700; color: #0f172a; margin-bottom: 4px;">${escapeHtml(props.head_name ?? 'Household')}</div>
        <div style="font-size: 11px; color: #475569; margin-bottom: 6px;">${escapeHtml(props.household_no)}</div>
        <div style="font-size: 12px; color: #334155; line-height: 1.5;">${escapeHtml(props.address)}</div>
        <div style="font-size: 11px; color: #475569; margin-top: 6px;">Size: ${escapeHtml(props.size ?? 0)} · ${escapeHtml(props.barangay)}</div>
      </div>
    `;
  }

  if (kind === 'centers') {
    const occupancy = Number(props.current_occupants ?? 0);
    const capacity = Number(props.capacity ?? 0);
    const load = capacity > 0 ? Math.round((occupancy / capacity) * 100) : 0;
    return `
      <div style="min-width:220px; font-family: system-ui, sans-serif;">
        <div style="font-size: 14px; font-weight: 700; color: #0f172a; margin-bottom: 4px;">${escapeHtml(props.name ?? 'Evacuation Center')}</div>
        <div style="font-size: 12px; color: #334155; line-height: 1.5;">${escapeHtml(props.barangay)} · ${escapeHtml(props.address)}</div>
        <div style="font-size: 11px; color: #475569; margin-top: 6px;">Occupancy: <b>${occupancy}</b> / ${capacity} · Load: <b>${load}%</b></div>
      </div>
    `;
  }

  const severity = String(props.severity ?? 'low');
  const color = SEVERITY_COLOR[severity as IncidentSeverity] ?? '#94a3b8';
  return `
    <div style="min-width:220px; font-family: system-ui, sans-serif;">
      <div style="font-size: 14px; font-weight: 700; color: #0f172a; margin-bottom: 4px;">${escapeHtml(props.title ?? 'Incident')}</div>
      <div style="display:flex; gap:6px; flex-wrap:wrap; margin-bottom:6px;">
        <span style="display:inline-block; border-radius:9999px; background:${color}22; color:${color}; font-weight:600; font-size:10px; padding:3px 8px; text-transform:capitalize;">${escapeHtml(severity)}</span>
        <span style="display:inline-block; border-radius:9999px; background:#e2e8f0; color:#334155; font-weight:600; font-size:10px; padding:3px 8px; text-transform:capitalize;">${escapeHtml(props.status ?? 'reported')}</span>
      </div>
      <div style="font-size: 12px; color: #334155;">${escapeHtml(props.barangay)}</div>
      <div style="font-size: 11px; color: #475569; margin-top: 4px;">${escapeHtml(formatDateTime(String(props.reported_at ?? '')))}</div>
    </div>
  `;
}

const EMPTY_COLLECTION = { type: 'FeatureCollection' as const, features: [] };

export function MapPage() {
  const households = useAsync(() => fetchAllHouseholds());
  const centers = useAsync(() => fetchCenters());
  const incidents = useAsync(() => fetchIncidents());
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const searchInput = useRef<HTMLInputElement | null>(null);
  const [layers, setLayers] = useState<LayerState>({ households: true, centers: true, incidents: true });
  const [barangay, setBarangay] = useState('ALL');
  const [query, setQuery] = useState('');
  const [activeResult, setActiveResult] = useState(0);
  const [searchOpen, setSearchOpen] = useState(false);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);

  const loading = households.loading || centers.loading || incidents.loading;

  const locatedHouseholds = useMemo(() => (households.data ?? []).filter(hasCoordinates), [households.data]);
  const locatedCenters = useMemo(() => (centers.data ?? []).filter(hasCoordinates), [centers.data]);
  const locatedIncidents = useMemo(() => (incidents.data ?? []).filter(hasCoordinates), [incidents.data]);

  const matchesBarangay = (item: { barangay?: string }) => barangay === 'ALL' || item.barangay === barangay;

  const validHouseholds = useMemo(() => locatedHouseholds.filter(matchesBarangay), [locatedHouseholds, barangay]);
  const validCenters = useMemo(() => locatedCenters.filter(matchesBarangay), [locatedCenters, barangay]);
  const validIncidents = useMemo(() => locatedIncidents.filter(matchesBarangay), [locatedIncidents, barangay]);

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

  const searchIndex = useMemo<SearchEntry[]>(() => {
    const entries: SearchEntry[] = [
      ...validHouseholds.map((h) => ({
        key: `household-${h.id}`,
        kind: 'household' as const,
        title: h.head_name,
        subtitle: `${h.household_no} · ${h.barangay}`,
        lat: h.lat,
        lng: h.lng,
        props: {
          household_no: h.household_no,
          head_name: h.head_name,
          address: h.address,
          barangay: h.barangay,
          size: h.size,
        },
      })),
      ...validCenters.map((c) => ({
        key: `center-${c.id}`,
        kind: 'center' as const,
        title: c.name,
        subtitle: `${c.barangay} · ${c.current_occupants}/${c.capacity} occupants`,
        lat: c.lat,
        lng: c.lng,
        props: {
          name: c.name,
          address: c.address,
          barangay: c.barangay,
          current_occupants: c.current_occupants,
          capacity: c.capacity,
        },
      })),
      ...validIncidents.map((inc) => ({
        key: `incident-${inc.id}`,
        kind: 'incident' as const,
        title: inc.title,
        subtitle: `${inc.severity} · ${inc.barangay}`,
        lat: inc.lat,
        lng: inc.lng,
        props: {
          title: inc.title,
          severity: inc.severity,
          status: inc.status,
          barangay: inc.barangay,
          reported_at: inc.reported_at,
        },
      })),
    ];
    return entries;
  }, [validHouseholds, validCenters, validIncidents]);

  const results = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (needle.length < 2) return [];
    return searchIndex
      .filter((entry) => `${entry.title} ${entry.subtitle}`.toLowerCase().includes(needle))
      .slice(0, MAX_SEARCH_RESULTS);
  }, [query, searchIndex]);

  const severityCounts = useMemo(() => {
    const counts: Record<string, number> = { low: 0, moderate: 0, high: 0, critical: 0 };
    validIncidents.forEach((inc) => {
      const severity = String(inc.severity ?? 'low');
      if (severity in counts) counts[severity] += 1;
    });
    return counts;
  }, [validIncidents]);

  const toggle = (key: keyof LayerState) =>
    setLayers((prev) => ({ ...prev, [key]: !prev[key] }));

  const layerToggles: Array<{ key: keyof LayerState; label: string; total: number; visible: number; icon: React.ReactNode }> = [
    { key: 'households', label: 'Households', total: locatedHouseholds.length, visible: validHouseholds.length, icon: <Users className="h-3.5 w-3.5" /> },
    { key: 'centers', label: 'Evacuation centers', total: locatedCenters.length, visible: validCenters.length, icon: <Building2 className="h-3.5 w-3.5" /> },
    { key: 'incidents', label: 'Incidents', total: locatedIncidents.length, visible: validIncidents.length, icon: <Siren className="h-3.5 w-3.5" /> },
  ];

  // Latest data for the map handlers, which are registered once per map instance
  // and would otherwise close over the values from the first render.
  const dataRef = useRef({ householdGeoJson, centerGeoJson, incidentGeoJson, incidentZoneGeoJson });
  dataRef.current = { householdGeoJson, centerGeoJson, incidentGeoJson, incidentZoneGeoJson };
  const selectRef = useRef<(entry: SearchEntry | null) => void>(() => {});
  selectRef.current = (entry) => setSelectedKey(entry ? entry.key : null);

  const showSelection = useCallback((lng: number, lat: number) => {
    const map = mapRef.current;
    const source = map?.getSource('selection') as maplibregl.GeoJSONSource | undefined;
    if (!source) return;
    source.setData({
      type: 'FeatureCollection',
      features: [{ type: 'Feature', geometry: { type: 'Point', coordinates: [lng, lat] }, properties: {} }],
    } as GeoJSONData);
  }, []);

  const focusEntry = useCallback(
    (entry: SearchEntry) => {
      const map = mapRef.current;
      setSelectedKey(entry.key);
      showSelection(entry.lng, entry.lat);
      if (!map) return;
      map.flyTo({ center: [entry.lng, entry.lat], zoom: 16, duration: 900 });
      new maplibregl.Popup({ closeButton: true, closeOnClick: true })
        .setLngLat([entry.lng, entry.lat])
        .setHTML(buildPopupHtml(`${entry.kind}s`, entry.props))
        .addTo(map);
    },
    [showSelection],
  );

  const resetView = useCallback(() => {
    mapRef.current?.fitBounds(MUNICIPALITY_BOUNDS_TUPLE, { padding: 48, duration: 700 });
    setSelectedKey(null);
  }, []);

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
    let handlersRegistered = false;

    const addMapLayers = () => {
      const data = dataRef.current;

      if (!map.getSource('households')) {
        map.addSource('households', { type: 'geojson', data: data.householdGeoJson as GeoJSONData });
      } else {
        (map.getSource('households') as maplibregl.GeoJSONSource | undefined)?.setData(data.householdGeoJson as GeoJSONData);
      }

      if (!map.getSource('centers')) {
        map.addSource('centers', { type: 'geojson', data: data.centerGeoJson as GeoJSONData });
      } else {
        (map.getSource('centers') as maplibregl.GeoJSONSource | undefined)?.setData(data.centerGeoJson as GeoJSONData);
      }

      if (!map.getSource('incidents')) {
        map.addSource('incidents', { type: 'geojson', data: data.incidentGeoJson as GeoJSONData });
      } else {
        (map.getSource('incidents') as maplibregl.GeoJSONSource | undefined)?.setData(data.incidentGeoJson as GeoJSONData);
      }

      if (!map.getSource('incident-zones')) {
        map.addSource('incident-zones', { type: 'geojson', data: data.incidentZoneGeoJson as GeoJSONData });
      } else {
        (map.getSource('incident-zones') as maplibregl.GeoJSONSource | undefined)?.setData(data.incidentZoneGeoJson as GeoJSONData);
      }

      if (!map.getSource('selection')) {
        map.addSource('selection', { type: 'geojson', data: EMPTY_COLLECTION as unknown as GeoJSONData });
      }

      if (!map.getLayer('selection-layer')) {
        map.addLayer({
          id: 'selection-layer',
          type: 'circle',
          source: 'selection',
          paint: {
            'circle-radius': 14,
            'circle-color': 'rgba(37, 99, 235, 0.15)',
            'circle-stroke-color': '#2563eb',
            'circle-stroke-width': 2,
          },
        });
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

      if (handlersRegistered) return;
      handlersRegistered = true;

      const sourceFor: Record<string, 'households' | 'centers' | 'incidents' | 'incident-zones'> = {
        'households-layer': 'households',
        'centers-layer': 'centers',
        'incident-zones-layer': 'incident-zones',
        'incidents-layer': 'incidents',
      };

      Object.entries(sourceFor).forEach(([layerId, sourceName]) => {
        map.on('click', layerId, (event: any) => {
          const feature = event.features?.[0];
          if (!feature?.properties) return;
          const props = feature.properties as Record<string, string | number | undefined>;
          selectRef.current(null);
          new maplibregl.Popup({ closeButton: true, closeOnClick: true })
            .setLngLat(event.lngLat)
            .setHTML(buildPopupHtml(sourceName, props))
            .addTo(map);
        });

        map.on('mouseenter', layerId, () => {
          map.getCanvas().style.cursor = 'pointer';
        });

        map.on('mouseleave', layerId, () => {
          map.getCanvas().style.cursor = '';
        });
      });
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
  }, []);

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
        source.setData(data as any);
      }
    };

    updateSource('households', householdGeoJson);
    updateSource('centers', centerGeoJson);
    updateSource('incidents', incidentGeoJson);
    updateSource('incident-zones', incidentZoneGeoJson);
  }, [householdGeoJson, centerGeoJson, incidentGeoJson, incidentZoneGeoJson]);

  useEffect(() => {
    if (!selectedKey) {
      const source = mapRef.current?.getSource('selection') as maplibregl.GeoJSONSource | undefined;
      source?.setData(EMPTY_COLLECTION as unknown as GeoJSONData);
    }
  }, [selectedKey]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const inSearch = target === searchInput.current;
      const typing = inSearch || target?.tagName === 'INPUT' || target?.tagName === 'TEXTAREA' || target?.tagName === 'SELECT';

      if (event.key === '/' && !typing) {
        event.preventDefault();
        searchInput.current?.focus();
        return;
      }

      if (event.key === 'Escape') {
        setQuery('');
        setSearchOpen(false);
        searchInput.current?.blur();
        return;
      }

      // The search input handles its own arrow/enter keys so results are not
      // activated twice.
      if (inSearch) return;
      if (!searchOpen || results.length === 0) return;

      if (event.key === 'ArrowDown') {
        event.preventDefault();
        setActiveResult((index) => (index + 1) % results.length);
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        setActiveResult((index) => (index - 1 + results.length) % results.length);
      } else if (event.key === 'Enter') {
        event.preventDefault();
        const entry = results[activeResult];
        if (entry) {
          focusEntry(entry);
          setQuery(entry.title);
          setSearchOpen(false);
        }
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [searchOpen, results, activeResult, focusEntry]);

  const onMapCount = validHouseholds.length + validCenters.length + validIncidents.length;
  const searchHint =
    query.trim().length >= 2
      ? `${results.length} match${results.length === 1 ? '' : 'es'} on the map`
      : `${onMapCount} feature${onMapCount === 1 ? '' : 's'} on the map`;

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
        <div className="absolute left-3 top-3 z-[600] w-[19rem] max-w-[calc(100%-1.5rem)] space-y-2">
          <div className="relative rounded-xl border border-slate-200 bg-white p-2 shadow-lg">
            <div className="flex items-center gap-2">
              <Search className="ml-1 h-4 w-4 shrink-0 text-slate-400" />
              <input
                ref={searchInput}
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  setActiveResult(0);
                  setSearchOpen(true);
                }}
                onFocus={() => setSearchOpen(true)}
                onBlur={() => window.setTimeout(() => setSearchOpen(false), 150)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && results[activeResult]) {
                    event.preventDefault();
                    focusEntry(results[activeResult]);
                    setQuery(results[activeResult].title);
                    setSearchOpen(false);
                  }
                }}
                placeholder="Search households, centers, incidents…"
                className="w-full bg-transparent text-sm text-slate-800 outline-none placeholder:text-slate-400"
              />
              {query && (
                <button
                  onClick={() => {
                    setQuery('');
                    searchInput.current?.focus();
                  }}
                  className="shrink-0 rounded p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
                  aria-label="Clear search"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>

            {searchOpen && query.trim().length >= 2 && (
              <div className="mt-2 max-h-64 overflow-y-auto border-t border-slate-100 pt-1">
                {results.length === 0 ? (
                  <p className="px-2 py-3 text-center text-xs text-slate-500">No matches on the map</p>
                ) : (
                  results.map((entry, index) => (
                    <button
                      key={entry.key}
                      onMouseEnter={() => setActiveResult(index)}
                      onMouseDown={(event) => event.preventDefault()}
                      onClick={() => {
                        focusEntry(entry);
                        setQuery(entry.title);
                        setSearchOpen(false);
                      }}
                      className={cn(
                        'flex w-full items-start gap-2 rounded-lg px-2 py-1.5 text-left transition-colors',
                        index === activeResult ? 'bg-brand-50' : 'hover:bg-slate-50',
                      )}
                    >
                      {entry.kind === 'household' && <Users className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-500" />}
                      {entry.kind === 'center' && <Building2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand-600" />}
                      {entry.kind === 'incident' && <Siren className="mt-0.5 h-3.5 w-3.5 shrink-0 text-danger-500" />}
                      <span className="min-w-0">
                        <span className="block truncate text-xs font-semibold text-slate-800">{entry.title}</span>
                        <span className="block truncate text-[11px] text-slate-500">{entry.subtitle}</span>
                      </span>
                    </button>
                  ))
                )}
              </div>
            )}

            <div className="mt-2 flex items-center gap-2 border-t border-slate-100 pt-2">
              <LocateFixed className="h-3.5 w-3.5 shrink-0 text-slate-400" />
              <Select
                value={barangay}
                onChange={(event) => {
                  setBarangay(event.target.value);
                  setSelectedKey(null);
                }}
                className="!py-1 text-xs"
                aria-label="Filter by barangay"
              >
                <option value="ALL">All barangays</option>
                {BARANGAYS.map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </Select>
              <button
                onClick={resetView}
                title="Reset view to municipality bounds"
                className="shrink-0 rounded-lg border border-slate-200 p-1.5 text-slate-500 transition-colors hover:bg-slate-50 hover:text-slate-700"
              >
                <Crosshair className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
          <p className="px-1 text-[10px] text-slate-500">
            {searchHint} · press <kbd className="rounded border border-slate-300 px-1">/</kbd> to search
          </p>
        </div>

        <div className="absolute bottom-3 left-3 right-3 z-[600] rounded-xl border border-slate-200 bg-white p-3 shadow-lg sm:bottom-auto sm:left-auto sm:right-3 sm:top-3 sm:w-56">
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
                    'flex h-4 w-4 shrink-0 items-center justify-center rounded border',
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
                <span className="flex-1 truncate">{lt.label}</span>
                <span className="shrink-0 text-[10px] tabular-nums text-slate-400">
                  {lt.visible === lt.total ? lt.total : `${lt.visible}/${lt.total}`}
                </span>
              </button>
            ))}
          </div>

          <div className="mt-3 border-t border-slate-100 pt-2">
            <div className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-slate-400">Incident severity</div>
            <div className="space-y-1">
              {SEVERITY_ORDER.map((severity) => (
                <div key={severity} className="flex items-center gap-2 text-[11px] text-slate-600">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: SEVERITY_COLOR[severity] }} />
                  <span className="flex-1 capitalize">{severity}</span>
                  <span className="tabular-nums text-slate-400">{severityCounts[severity] ?? 0}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
