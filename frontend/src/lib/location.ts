export const MUNICIPALITY = 'San Rafael';
export const PROVINCE = 'Bulacan';
export const REGION = 'Central Luzon (Region III)';
export const PSGC_CODE = '031422000';
export const ZIP_CODE = '3008';

export const MUNICIPALITY_LABEL = `${MUNICIPALITY}, ${PROVINCE}`;

/** Poblacion, San Rafael, Bulacan (municipal hall). */
export const MUNICIPALITY_CENTER: [number, number] = [14.9571, 120.9629];

export const MUNICIPALITY_BOUNDS = {
  minLat: 14.9,
  maxLat: 15.02,
  minLng: 120.9,
  maxLng: 121.02,
};

export function isWithinMunicipality(lat: number, lng: number): boolean {
  return (
    lat >= MUNICIPALITY_BOUNDS.minLat &&
    lat <= MUNICIPALITY_BOUNDS.maxLat &&
    lng >= MUNICIPALITY_BOUNDS.minLng &&
    lng <= MUNICIPALITY_BOUNDS.maxLng
  );
}
