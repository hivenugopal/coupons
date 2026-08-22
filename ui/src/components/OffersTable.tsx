import type { Offer } from '../types';
import { ClaimButton } from './ClaimButton';

interface OffersTableProps {
  offers: Offer[];
}

function formatLocation(offer: Offer): string {
  const parts = [offer.storeName, offer.addressLine1, offer.addressLine2].filter(Boolean);
  const line = parts.join(', ');
  const cityState = [offer.city, offer.state].filter(Boolean).join(', ');
  return [line, cityState].filter(Boolean).join(' \u2014 ') || offer.location || '-';
}

export function OffersTable({ offers }: OffersTableProps) {
  if (offers.length === 0) {
    return <p className="empty-state">No offers match the selected filters.</p>;
  }

  return (
    <table className="offers-table">
      <thead>
        <tr>
          <th>Location</th>
          <th>Discount</th>
          <th>Expires</th>
          <th>Coupon</th>
        </tr>
      </thead>
      <tbody>
        {offers.map((offer, index) => (
          <tr key={`${offer.url}-${index}`}>
            <td>{formatLocation(offer)}</td>
            <td>{offer.price || '-'}</td>
            <td>{offer.expires || '-'}</td>
            <td>
              <ClaimButton offerId={offer.id} hasCode={offer.hasCode} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
