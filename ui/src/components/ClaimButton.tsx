import { useState } from 'react';

interface ClaimButtonProps {
  code: string;
}

/** Shows a "Claim Code" button that reveals the coupon code in place once clicked. */
export function ClaimButton({ code }: ClaimButtonProps) {
  const [revealed, setRevealed] = useState(false);

  if (!code) {
    return <span className="no-code">No code found</span>;
  }

  if (revealed) {
    return <span className="revealed-code">{code}</span>;
  }

  return (
    <button type="button" className="claim-button" onClick={() => setRevealed(true)}>
      Claim Code
    </button>
  );
}
