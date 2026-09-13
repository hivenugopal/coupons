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
      // Do not pass "noopener" in window.open features: many browsers then return null
      // even when the tab opens, which falsely looks like a blocked popup.
      const opened = window.open(claim.redirect_url, '_blank');
      if (opened) {
        opened.opener = null;
      }
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
      <ul className="warn-banner claim-steps">
        <li>Enter your email, then Proceed. We open the salon offer in a new tab.</li>
        <li>Check if it's valid in your location by looking at the details.</li>
        <li>Check if today the offer is still valid or expired.</li>
        <li>
          At the Great Clips salon, show your coupon when paying. You can use your phone for a
          digital copy or take the print out.
        </li>
        <li>
          Note: This great deal is only available at select locations, so check if your local salon
          accepts it.
        </li>
      </ul>
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
        {status === 'opened' && openedUrl && popupBlocked && (
          <p className="error-banner">
            The offer tab was blocked, enable your browser pop up settings for seamless access or Open{' '}
            <a href={openedUrl} target="_blank" rel="noopener noreferrer">
              Great Clips offer link
            </a>
            .
          </p>
        )}
        {status === 'opened' && openedUrl && !popupBlocked && (
          <p className="success-banner">
            If you cannot see the offer page, Open{' '}
            <a href={openedUrl} target="_blank" rel="noopener noreferrer">
              Great Clips offer link
            </a>
            .
          </p>
        )}
      </form>
    </section>
  );
}
