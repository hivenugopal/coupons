import { useEffect, useState } from 'react';
import { fetchClaimDetails, type ClaimDetails } from '../lib/offersApi';

interface ClaimPageProps {
  offerId: number;
  onBack: () => void;
}

function formatExpires(value: string | null | undefined): string {
  const text = String(value || '').trim();
  const iso = /^(\d{4})-(\d{2})-(\d{2})/.exec(text);
  if (iso) {
    return `${iso[2]}/${iso[3]}/${iso[1]}`;
  }
  return text || '-';
}

export function ClaimPage({ offerId, onBack }: ClaimPageProps) {
  const [details, setDetails] = useState<ClaimDetails | null>(null);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    let cancelled = false;
    fetchClaimDetails(offerId)
      .then((loaded) => {
        if (!cancelled) {
          setDetails(loaded);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setErrorMessage(err instanceof Error ? err.message : String(err));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [offerId]);

  return (
    <section className="claim-page">
      <button type="button" className="back-link" onClick={onBack}>
        Back to offers
      </button>

      {!details && !errorMessage && <p className="info-banner">Loading coupon&hellip;</p>}
      {errorMessage && <p className="error-banner">{errorMessage}</p>}

      {details && (
        <article className="claim-card">
          <div className="coupon-banner">
            <h2>Your coupon</h2>
          </div>
          <p className="coupon-code">{details.coupon}</p>
          <p>
            <strong>Haircut for:</strong> {details.price || '-'}
          </p>
          <p>
            <strong>Location:</strong> Valid at {details.location} in {details.city}, {details.state}.
          </p>
          <p>
            <strong>Expires:</strong> {formatExpires(details.expires)}.
          </p>
          <p>
            <strong>Terms &amp; Conditions:</strong> Not valid with any other offer. Limit one coupon
            per customer. No copies. Taxes may apply.
          </p>
        </article>
      )}
    </section>
  );
}
