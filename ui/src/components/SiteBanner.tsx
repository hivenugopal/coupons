interface SiteBannerProps {
  kicker?: string;
  title: string;
  subtitle: string;
}

export function SiteBanner({
  kicker = 'Local haircut deals',
  title,
  subtitle,
}: SiteBannerProps) {
  return (
    <header className="hero-banner">
      <div className="hero-banner-inner">
        <p className="hero-kicker">{kicker}</p>
        <h1>{title}</h1>
        <p className="hero-subtitle">{subtitle}</p>
      </div>
    </header>
  );
}
