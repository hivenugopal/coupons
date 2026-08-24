import type { Offer } from '../types';

interface OffersTableProps {
  offers: Offer[];
  onClaim: (offerId: number) => void;
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

export function OffersTable({ offers, onClaim }: OffersTableProps) {
  if (offers.length === 0) {
    return <p className="empty-state">No active coupons found for the selected city.</p>;
  }

  return (
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
            <td>{offer.price || '-'}</td>
            <td>{offer.expires || '-'}</td>
            <td>
              <button type="button" className="claim-link" onClick={() => onClaim(offer.id)}>
                Claim
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
