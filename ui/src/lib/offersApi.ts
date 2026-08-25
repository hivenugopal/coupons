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

export interface ClickClaimResponse {
  claim_id: number;
  date_clicked: string;
  redirect_url: string;
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

export async function recordClickClaim(offerId: number, email: string): Promise<ClickClaimResponse> {
  const response = await fetch('/api/claims', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ offer_id: offerId, email }),
  });
  const payload = (await response.json()) as ClickClaimResponse & { error?: string; ok?: boolean };
  if (!response.ok || !payload.ok || !payload.redirect_url) {
    throw new Error(payload.error || `Could not record click (${response.status}).`);
  }
  return payload;
}
