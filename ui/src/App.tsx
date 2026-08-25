import { useEffect, useMemo, useState } from 'react';
import { ClaimPage } from './components/ClaimPage';
import { ClickClaimPage } from './components/ClickClaimPage';
import { FilterBar } from './components/FilterBar';
import { OffersTable } from './components/OffersTable';
import { loadLocations, loadOffers } from './lib/offersApi';
import type { Offer } from './types';
import './App.css';

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
      <main className="app">
        <h1>Great Clips Coupon Finder</h1>
        <ClaimPage offerId={claimOfferId} onBack={() => setClaimOfferId(null)} />
      </main>
    );
  }

  if (clickOfferId !== null) {
    return (
      <main className="app">
        <h1>Great Clips Coupon Finder</h1>
        <ClickClaimPage offerId={clickOfferId} onBack={() => setClickOfferId(null)} />
      </main>
    );
  }

  return (
    <main className="app">
      <h1>Great Clips Coupon Finder</h1>

      {locationsStatus === 'loading' && <p className="status-message">Loading locations&hellip;</p>}
      {locationsStatus === 'error' && (
        <p className="status-message error">Could not load locations: {errorMessage}.</p>
      )}

      {locationsStatus === 'ready' && (
        <>
          <FilterBar
            states={states}
            cities={cities}
            selectedState={selectedState}
            selectedCity={selectedCity}
            onStateChange={handleStateChange}
            onCityChange={setSelectedCity}
          />

          {!selectedState || !selectedCity ? (
            <p className="prompt-message">Select a state and city to see available coupons.</p>
          ) : (
            <>
              {offersStatus === 'loading' && <p className="status-message">Loading coupons&hellip;</p>}
              {offersStatus === 'error' && (
                <p className="status-message error">Could not load coupons: {errorMessage}.</p>
              )}
              {offersStatus === 'ready' && (
                <OffersTable offers={offers} onClaim={setClaimOfferId} onClickOffer={setClickOfferId} />
              )}
            </>
          )}
        </>
      )}
    </main>
  );
}

export default App;
