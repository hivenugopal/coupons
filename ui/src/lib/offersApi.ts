import type { Offer } from '../types';

interface OffersResponse {
  offers: Offer[];
}

export async function loadOffers(): Promise<Offer[]> {
  const response = await fetch('/api/offers');
  if (!response.ok) {
    throw new Error(`Failed to load offers: ${response.status} ${response.statusText}`);
  }
  const payload = (await response.json()) as OffersResponse;
  return payload.offers;
}

export async function fetchCouponCode(offerId: number): Promise<string> {
  const response = await fetch(`/api/offers?code_for=${encodeURIComponent(offerId)}`);
  const payload = (await response.json()) as { code?: string; error?: string };
  if (!response.ok || !payload.code) {
    throw new Error(payload.error || `Could not load coupon code (${response.status}).`);
  }
  return payload.code;
}
