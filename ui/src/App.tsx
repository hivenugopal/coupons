import { useEffect, useMemo, useState } from 'react';
import { AdminPage } from './components/AdminPage';
import { FilterBar } from './components/FilterBar';
import { OffersTable } from './components/OffersTable';
import { loadOffers } from './lib/offersApi';
import type { Offer } from './types';
import './App.css';

const ALL = 'All';

function App() {
  const [offers, setOffers] = useState<Offer[]>([]);
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = useState('');
  const [selectedState, setSelectedState] = useState(ALL);
  const [selectedCity, setSelectedCity] = useState(ALL);
  const [activeTab, setActiveTab] = useState<'offers' | 'admin'>('offers');

  const reloadOffers = () => {
    setStatus('loading');
    setErrorMessage('');
    loadOffers()
      .then((loaded) => {
        setOffers(loaded);
        setStatus('ready');
      })
      .catch((err: unknown) => {
        setErrorMessage(err instanceof Error ? err.message : String(err));
        setStatus('error');
      });
  };

  useEffect(() => {
    reloadOffers();
  }, []);

  const states = useMemo(
    () => Array.from(new Set(offers.map((o) => o.state).filter(Boolean))).sort(),
    [offers],
  );

  const cities = useMemo(() => {
    const inState = selectedState === ALL ? offers : offers.filter((o) => o.state === selectedState);
    return Array.from(new Set(inState.map((o) => o.city).filter(Boolean))).sort();
  }, [offers, selectedState]);

  const filteredOffers = useMemo(
    () =>
      offers.filter(
        (o) =>
          (selectedState === ALL || o.state === selectedState) &&
          (selectedCity === ALL || o.city === selectedCity),
      ),
    [offers, selectedState, selectedCity],
  );

  const handleStateChange = (state: string) => {
    setSelectedState(state);
    setSelectedCity(ALL);
  };

  return (
    <main className="app">
      <h1>Great Clips Coupon Finder</h1>

      <div className="tab-bar">
        <button
          type="button"
          className={`tab-button ${activeTab === 'offers' ? 'active' : ''}`}
          onClick={() => setActiveTab('offers')}
        >
          Offers
        </button>
        <button
          type="button"
          className={`tab-button ${activeTab === 'admin' ? 'active' : ''}`}
          onClick={() => setActiveTab('admin')}
        >
          Admin
        </button>
      </div>

      {activeTab === 'admin' && <AdminPage onFetched={reloadOffers} />}

      {activeTab === 'offers' && (
        <>
          <FilterBar
            states={states}
            cities={cities}
            selectedState={selectedState}
            selectedCity={selectedCity}
            onStateChange={handleStateChange}
            onCityChange={setSelectedCity}
          />

          {status === 'loading' && <p className="status-message">Loading offers&hellip;</p>}
          {status === 'error' && (
            <p className="status-message error">
              Could not load offers: {errorMessage}.
            </p>
          )}
          {status === 'ready' && <OffersTable offers={filteredOffers} />}
        </>
      )}
    </main>
  );
}

export default App;

