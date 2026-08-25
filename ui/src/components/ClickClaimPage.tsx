import { useState, type FormEvent } from 'react';
import { recordClickClaim } from '../lib/offersApi';

interface ClickClaimPageProps {
  offerId: number;
  onBack: () => void;
}

export function ClickClaimPage({ offerId, onBack }: ClickClaimPageProps) {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'submitting' | 'opened' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [openedUrl, setOpenedUrl] = useState('');
  const [popupBlocked, setPopupBlocked] = useState(false);

  const proceed = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setStatus('submitting');
    setErrorMessage('');

    try {
      const claim = await recordClickClaim(offerId, email);
      const opened = window.open(claim.redirect_url, '_blank', 'noopener,noreferrer');
      setOpenedUrl(claim.redirect_url);
      setPopupBlocked(!opened);
      setStatus('opened');
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
            disabled={status === 'submitting' || status === 'opened'}
          />
        </label>
        <p>
          When you proceed, we record your email address, the selected offer, its Great Clips URL, and
          the time you clicked. The Great Clips offer then opens in a new tab so you can print the coupon.
        </p>
        {status === 'opened' ? (
          <button type="button" className="claim-button" onClick={onBack}>
            Back to Offers page
          </button>
        ) : (
          <button type="submit" className="claim-button" disabled={status === 'submitting'}>
            {status === 'submitting' ? 'Opening Great Clips...' : 'Proceed'}
          </button>
        )}
        {errorMessage && <p className="status-message error">{errorMessage}</p>}
        {popupBlocked && openedUrl && (
          <p className="status-message error">
            The offer tab was blocked.{' '}
            <a href={openedUrl} target="_blank" rel="noopener noreferrer">
              Open Great Clips offer
            </a>
          </p>
        )}
      </form>
    </section>
  );
}
