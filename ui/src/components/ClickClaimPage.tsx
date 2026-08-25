import { useState, type FormEvent } from 'react';
import { recordClickClaim } from '../lib/offersApi';

interface ClickClaimPageProps {
  offerId: number;
  onBack: () => void;
}

export function ClickClaimPage({ offerId, onBack }: ClickClaimPageProps) {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'submitting' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const proceed = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setStatus('submitting');
    setErrorMessage('');

    try {
      const claim = await recordClickClaim(offerId, email);
      window.location.assign(claim.redirect_url);
    } catch (error) {
      setStatus('error');
      setErrorMessage(error instanceof Error ? error.message : String(error));
    }
  };

  return (
    <section className="claim-page">
      <button type="button" className="back-link" onClick={onBack}>
        Back to offers
      </button>
      <h2>Continue to Great Clips</h2>
      <form className="claim-card" onSubmit={proceed}>
        <label className="claim-email">
          <span>Email address</span>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            required
          />
        </label>
        <p>
          When you proceed, we record your email address, the selected offer, its Great Clips URL, and
          the time you clicked. You will then complete redemption directly on the Great Clips website.
        </p>
        <button type="submit" className="claim-button" disabled={status === 'submitting'}>
          {status === 'submitting' ? 'Opening Great Clips...' : 'Proceed'}
        </button>
        {errorMessage && <p className="status-message error">{errorMessage}</p>}
      </form>
    </section>
  );
}
