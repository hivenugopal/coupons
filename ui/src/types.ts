/** Public offer data returned by the Vercel API; coupon codes are loaded on demand. */
export interface Offer {
  id: number;
  url: string;
  price: string;
  location: string;
  storeName: string;
  addressLine1: string;
  addressLine2: string;
  city: string;
  state: string;
  expires: string;
  hasCode: boolean;
}
