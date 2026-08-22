export interface FetchCouponsResponse {
  ok: boolean;
  output_file?: string;
  urls_received?: number;
  urls_processed?: number;
  rows_stored?: number;
  results?: Array<{
    url: string;
    ok: boolean;
    error?: string;
    codes_found?: number;
    rows_written?: number;
  }>;
  error?: string;
}

export async function fetchCouponsFromUrls(
  urls: string[],
  adminToken: string,
): Promise<FetchCouponsResponse> {
  const response = await fetch('/api/fetch-coupons', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Admin-Token': adminToken },
    body: JSON.stringify({
      urls,
    }),
  });

  const data = (await response.json()) as FetchCouponsResponse;
  if (!response.ok || data.ok === false) {
    throw new Error(data.error || `Request failed with status ${response.status}`);
  }
  return data;
}
