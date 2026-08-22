import { useMemo, useState } from 'react';
import { fetchCouponsFromUrls, type FetchCouponsResponse } from '../lib/adminApi';

interface AdminPageProps {
  onFetched: () => void;
}

function extractUrls(input: string): string[] {
  return Array.from(
    new Set(
      input
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter((line) => /^https?:\/\//i.test(line)),
    ),
  );
}

export function AdminPage({ onFetched }: AdminPageProps) {
  const [value, setValue] = useState('');
  const [adminToken, setAdminToken] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'done' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [result, setResult] = useState<FetchCouponsResponse | null>(null);

  const urls = useMemo(() => extractUrls(value), [value]);

  const submit = async () => {
    if (urls.length === 0) {
      setStatus('error');
      setMessage('Enter at least one valid URL (http/https), one per line.');
      return;
    }
    if (!adminToken) {
      setStatus('error');
      setMessage('Enter the admin token configured for this deployment.');
      return;
    }

    setStatus('loading');
    setMessage('Fetching coupons...');
    setResult(null);

    try {
      const response = await fetchCouponsFromUrls(urls, adminToken);
      setResult(response);
      setStatus('done');
      setMessage(
        `Done. Processed ${response.urls_processed ?? 0} URL(s), stored ${response.rows_stored ?? 0} row(s).`,
      );
      onFetched();
    } catch (err) {
      setStatus('error');
      setMessage(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <section className="admin-page">
      <h2>Admin: Fetch Coupons</h2>
      <p className="admin-help">
        Paste up to 10 allowed URLs per request. The server fetches static HTML only, so codes that require
        a browser click cannot be captured.
      </p>

      <label className="admin-token">
        <span>Admin token</span>
        <input
          type="password"
          value={adminToken}
          onChange={(e) => setAdminToken(e.target.value)}
          autoComplete="current-password"
        />
      </label>

      <textarea
        className="admin-textarea"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={[
          'https://offers.greatclips.com/vqZhNYR',
          'https://offers.greatclips.com/DRd0nhA',
        ].join('\n')}
      />

      <div className="admin-actions">
        <button type="button" className="claim-button" onClick={submit} disabled={status === 'loading'}>
          {status === 'loading' ? 'Fetching...' : 'Fetch Coupons'}
        </button>
        <span className="admin-count">Valid URLs: {urls.length}</span>
      </div>

      {message && <p className={`status-message ${status === 'error' ? 'error' : ''}`}>{message}</p>}

      {result?.results && result.results.length > 0 && (
        <table className="offers-table admin-results">
          <thead>
            <tr>
              <th>URL</th>
              <th>Status</th>
              <th>Codes Found</th>
              <th>Rows Written</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            {result.results.map((row) => (
              <tr key={row.url}>
                <td>{row.url}</td>
                <td>{row.ok ? 'OK' : 'Failed'}</td>
                <td>{row.codes_found ?? 0}</td>
                <td>{row.rows_written ?? 0}</td>
                <td>{row.error ?? '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
