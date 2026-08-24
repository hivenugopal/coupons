import type { Offer } from '../types';

export interface LocationOptions {
  states: string[];
  citiesByState: Record<string, string[]>;
}

export interface ClaimDetails {
  coupon: string;
  price: string;
  location: string;
  city: string;
  state: string;
  expires: string;
}

export async function loadLocations(): Promise<LocationOptions> {
  const response = await fetch('/api/offers');
  if (!response.ok) {
    throw new Error(`Failed to load locations: ${response.status} ${response.statusText}`);
  }
  return (await response.json()) as LocationOptions;
}

export async function loadOffers(state: string, city: string): Promise<Offer[]> {
  const params = new URLSearchParams({ state, city });
  const response = await fetch(`/api/offers?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Failed to load offers: ${response.status} ${response.statusText}`);
  }
  const payload = (await response.json()) as { offers?: Offer[] };
  return payload.offers ?? [];
}

export async function fetchClaimDetails(offerId: number): Promise<ClaimDetails> {
  const response = await fetch(`/api/offers?code_for=${encodeURIComponent(offerId)}`);
  const payload = (await response.json()) as ClaimDetails & { error?: string };
  if (!response.ok || !payload.coupon) {
    throw new Error(payload.error || `Could not load coupon (${response.status}).`);
  }
  return payload;
}

export async function fetchCouponCode(offerId: number): Promise<string> {
  const details = await fetchClaimDetails(offerId);
  return details.coupon;
}
