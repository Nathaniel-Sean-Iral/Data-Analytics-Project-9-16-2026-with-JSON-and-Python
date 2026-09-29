export const MUNICIPALITY = 'San Rafael';
export const PROVINCE = 'Bulacan';
export const REGION = 'Central Luzon (Region III)';
export const PSGC_CODE = '031422000';
export const ZIP_CODE = '3008';

export const MUNICIPALITY_LABEL = `${MUNICIPALITY}, ${PROVINCE}`;

/**
 * OSM centroid of the San Rafael boundary relation (8404894), Poblacion area.
 * Mirrors backend/app/core/location.py.
 */
export const MUNICIPALITY_CENTER: [number, number] = [14.9581, 120.9637];

/** OSM municipal extent padded by ~500 m on each side. */
export const MUNICIPALITY_BOUNDS = {
  minLat: 14.944,
  maxLat: 15.0461,
  minLng: 120.8881,
  maxLng: 121.0646,
};

export function isWithinMunicipality(lat: number, lng: number): boolean {
  return (
    lat >= MUNICIPALITY_BOUNDS.minLat &&
    lat <= MUNICIPALITY_BOUNDS.maxLat &&
    lng >= MUNICIPALITY_BOUNDS.minLng &&
    lng <= MUNICIPALITY_BOUNDS.maxLng
  );
}
