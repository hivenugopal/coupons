import type { Offer } from '../types';

interface OffersTableProps {
  offers: Offer[];
  onClaim: (offerId: number) => void;
  onClickOffer: (offerId: number) => void;
}

function formatLocation(offer: Offer): string {
  if (offer.addressLine1 || offer.addressLine2) {
    const parts = [offer.storeName, offer.addressLine1, offer.addressLine2].filter(Boolean);
    const line = parts.join(', ');
    const cityState = [offer.city, offer.state].filter(Boolean).join(', ');
    return [line, cityState].filter(Boolean).join(' \u2014 ') || offer.location || '-';
  }
  return offer.location || [offer.storeName, offer.city, offer.state].filter(Boolean).join(' \u2014 ') || '-';
}

export function OffersTable({ offers, onClaim, onClickOffer }: OffersTableProps) {
  if (offers.length === 0) {
    return (
      <p className="empty-panel empty-state">No active coupons found for the selected city.</p>
    );
  }

  return (
    <section className="table-card">
      <div className="table-banner">
        <span>
          {offers.length} deal{offers.length === 1 ? '' : 's'} ready to claim
        </span>
        <strong>Limited-time salon offers</strong>
      </div>
      <table className="offers-table">
        <thead>
          <tr>
            <th>Location</th>
            <th>Price/Discount</th>
            <th>Expires</th>
            <th>Coupon</th>
          </tr>
        </thead>
        <tbody>
          {offers.map((offer) => (
            <tr key={offer.id}>
              <td>{formatLocation(offer)}</td>
              <td>
                <span className="price-chip">{offer.price || '-'}</span>
              </td>
              <td>{offer.expires || '-'}</td>
              <td>
                <div className="action-row">
                  <button type="button" className="claim-link" onClick={() => onClaim(offer.id)}>
                    Claim
                  </button>
                  <button
                    type="button"
                    className="claim-link secondary"
                    onClick={() => onClickOffer(offer.id)}
                  >
                    Click
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
