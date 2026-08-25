import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { ClaimPage } from './components/ClaimPage';
import { ClickClaimPage } from './components/ClickClaimPage';
import { FilterBar } from './components/FilterBar';
import { OffersTable } from './components/OffersTable';
import { SiteBanner } from './components/SiteBanner';
import { loadLocations, loadOffers } from './lib/offersApi';
import type { Offer } from './types';
import './App.css';

function PageShell({
  subtitle,
  children,
}: {
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <div className="page">
      <SiteBanner title="Great Clips Coupon Finder" subtitle={subtitle} />
      <div className="promo-strip">Haircut specials near you. Claim a code here or print it at Great Clips.</div>
      <main className="app">{children}</main>
    </div>
  );
}

function App() {
  const [states, setStates] = useState<string[]>([]);
  const [citiesByState, setCitiesByState] = useState<Record<string, string[]>>({});
  const [selectedState, setSelectedState] = useState('');
  const [selectedCity, setSelectedCity] = useState('');
  const [offers, setOffers] = useState<Offer[]>([]);
  const [locationsStatus, setLocationsStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [offersStatus, setOffersStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [claimOfferId, setClaimOfferId] = useState<number | null>(null);
  const [clickOfferId, setClickOfferId] = useState<number | null>(null);

  const cities = useMemo(
    () => (selectedState ? citiesByState[selectedState] ?? [] : []),
    [citiesByState, selectedState],
  );

  useEffect(() => {
    loadLocations()
      .then((loaded) => {
        setStates(loaded.states ?? []);
        setCitiesByState(loaded.citiesByState ?? {});
        setLocationsStatus('ready');
      })
      .catch((err: unknown) => {
        setErrorMessage(err instanceof Error ? err.message : String(err));
        setLocationsStatus('error');
      });
  }, []);

  useEffect(() => {
    if (!selectedState || !selectedCity) {
      setOffers([]);
      setOffersStatus('idle');
      return;
    }

    setOffersStatus('loading');
    setErrorMessage('');
    loadOffers(selectedState, selectedCity)
      .then((loaded) => {
        setOffers(loaded);
        setOffersStatus('ready');
      })
      .catch((err: unknown) => {
        setErrorMessage(err instanceof Error ? err.message : String(err));
        setOffersStatus('error');
      });
  }, [selectedState, selectedCity]);

  const handleStateChange = (state: string) => {
    setSelectedState(state);
    setSelectedCity('');
  };

  if (claimOfferId !== null) {
    return (
      <PageShell subtitle="Show this coupon at checkout. One offer per customer.">
        <ClaimPage offerId={claimOfferId} onBack={() => setClaimOfferId(null)} />
      </PageShell>
    );
  }

  if (clickOfferId !== null) {
    return (
      <PageShell subtitle="We'll open the Great Clips offer so you can print the coupon.">
        <ClickClaimPage offerId={clickOfferId} onBack={() => setClickOfferId(null)} />
      </PageShell>
    );
  }

  return (
    <PageShell subtitle="Pick a location to see current haircut prices and expiration dates.">
      {locationsStatus === 'loading' && <p className="info-banner">Loading locations&hellip;</p>}
      {locationsStatus === 'error' && (
        <p className="error-banner">Could not load locations: {errorMessage}.</p>
      )}

      {locationsStatus === 'ready' && (
        <>
          <section className="filter-panel">
            <FilterBar
              states={states}
              cities={cities}
              selectedState={selectedState}
              selectedCity={selectedCity}
              onStateChange={handleStateChange}
              onCityChange={setSelectedCity}
            />
          </section>

          {!selectedState || !selectedCity ? (
            <p className="info-banner">Select a state and city to see available coupons.</p>
          ) : (
            <>
              {offersStatus === 'loading' && <p className="info-banner">Loading coupons&hellip;</p>}
              {offersStatus === 'error' && (
                <p className="error-banner">Could not load coupons: {errorMessage}.</p>
              )}
              {offersStatus === 'ready' && (
                <OffersTable offers={offers} onClaim={setClaimOfferId} onClickOffer={setClickOfferId} />
              )}
            </>
          )}
        </>
      )}
    </PageShell>
  );
}

export default App;
