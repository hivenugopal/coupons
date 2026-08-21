/** A single row from couponfinder's results.csv (pipe-delimited). */
export interface Offer {
  url: string;
  code: string;
  confidence: string;
  source: string;
  price: string;
  location: string;
  storeName: string;
  addressLine1: string;
  addressLine2: string;
  city: string;
  state: string;
  expires: string;
  error: string;
}
