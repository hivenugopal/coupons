import { useState } from 'react';
import { fetchCouponCode } from '../lib/offersApi';

interface ClaimButtonProps {
  offerId: number;
  hasCode: boolean;
}

/** Retrieves a coupon code only after the visitor asks to reveal it. */
export function ClaimButton({ offerId, hasCode }: ClaimButtonProps) {
  const [code, setCode] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'error'>('idle');

  if (!hasCode) {
    return <span className="no-code">No code found</span>;
  }

  if (code) {
    return <span className="revealed-code">{code}</span>;
  }

  const reveal = async () => {
    setStatus('loading');
    try {
      setCode(await fetchCouponCode(offerId));
      setStatus('idle');
    } catch {
      setStatus('error');
    }
  };

  return (
    <>
      <button type="button" className="claim-button" onClick={reveal} disabled={status === 'loading'}>
        {status === 'loading' ? 'Loading...' : 'Claim Code'}
      </button>
      {status === 'error' && <span className="claim-error">Could not load code</span>}
    </>
  );
}
