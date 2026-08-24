-- Allow historical inactive rows for the same URL/code/location after a re-fetch.
DROP INDEX IF EXISTS coupons.gc_coupons_url_code_location_key;
CREATE UNIQUE INDEX IF NOT EXISTS gc_coupons_url_code_location_active_key
  ON coupons.gc_coupons (url, code, location)
  WHERE status = 'fetched';
