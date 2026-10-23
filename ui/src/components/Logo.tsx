interface LogoProps {
  size?: number;
  className?: string;
}

// A sharp geometric "A" logo in AssetIt style — a stylized letter A
// made from two angled strokes meeting at a peak, with a cyan glow.
export default function Logo({ size = 32, className = '' }: LogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="logoGrad" x1="16" y1="2" x2="16" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#00C6FF" />
          <stop offset="1" stopColor="#00A3FF" />
        </linearGradient>
      </defs>
      {/* Left stroke of A */}
      <path d="M16 2L5 30H10.5L16 14L21.5 30H27L16 2Z" fill="url(#logoGrad)" />
      {/* Crossbar of A */}
      <path d="M12.5 20H19.5L18 16H14L12.5 20Z" fill="#00A3FF" opacity="0.5" />
      {/* Inner highlight */}
      <path d="M16 5L8.5 28H11L16 16L21 28H23.5L16 5Z" fill="#0d0d0d" opacity="0.3" />
    </svg>
  );
}
