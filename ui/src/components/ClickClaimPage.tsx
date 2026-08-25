import { useState, type FormEvent } from 'react';
import { EMAIL_ERROR, isValidEmail, normalizeEmail } from '../lib/email';
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
    const cleanedEmail = normalizeEmail(email);
    if (!isValidEmail(cleanedEmail)) {
      setStatus('error');
      setErrorMessage(EMAIL_ERROR);
      return;
    }

    setStatus('submitting');
    setErrorMessage('');

    try {
      const claim = await recordClickClaim(offerId, cleanedEmail);
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
      <p className="warn-banner">
        Enter your email, then Proceed. We open the salon offer in a new tab.
      </p>
      <form className="claim-card" onSubmit={proceed} noValidate>
        <label className="claim-email">
          <span>Email address</span>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            required
            spellCheck={false}
            inputMode="email"
            disabled={status === 'submitting' || status === 'opened'}
          />
        </label>
        {status === 'opened' ? (
          <button type="button" className="claim-button" onClick={onBack}>
            Back to Offers page
          </button>
        ) : (
          <button type="submit" className="claim-button" disabled={status === 'submitting'}>
            {status === 'submitting' ? 'Opening Great Clips...' : 'Proceed'}
          </button>
        )}
        {errorMessage && <p className="error-banner">{errorMessage}</p>}
        {popupBlocked && openedUrl && (
          <p className="error-banner">
            The offer tab was blocked.{' '}
            <a href={openedUrl} target="_blank" rel="noopener noreferrer">
              Open Great Clips offer
            </a>
          </p>
        )}
        {status === 'opened' && !popupBlocked && (
          <p className="success-banner">Great Clips opened in a new tab. Print the coupon there.</p>
        )}
      </form>
    </section>
  );
}
