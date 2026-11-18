/**
 * Tiny inline SVG sparkline for metric cards. Pure SVG (no ECharts) so the
 * overview stays light. Nulls/empty render nothing; the line is warm ink with
 * a faint area fill, matching the workspace's restrained chart language.
 */
export function Sparkline({
  data,
  width = 120,
  height = 36,
  tone = "var(--primary)",
  label,
}: {
  data: (number | null | undefined)[];
  width?: number;
  height?: number;
  tone?: string;
  label?: string;
}) {
  const pts = data.filter((v): v is number => v !== null && v !== undefined && Number.isFinite(v));
  if (pts.length < 2) return <div style={{ height }} aria-hidden />;

  const lo = Math.min(...pts);
  const hi = Math.max(...pts);
  const span = hi - lo || 1;
  const pad = 3;
  const stepX = (width - pad * 2) / (pts.length - 1);
  const coords = pts.map((v, i) => {
    const x = pad + i * stepX;
    const y = pad + (1 - (v - lo) / span) * (height - pad * 2);
    return [x, y] as const;
  });
  const line = coords.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const area = `${line} L${(width - pad).toFixed(1)},${height - pad} L${pad},${height - pad} Z`;

  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" role="img" aria-label={label ?? "روند"}>
      <path d={area} fill={tone} opacity={0.08} />
      <path d={line} fill="none" stroke={tone} strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}