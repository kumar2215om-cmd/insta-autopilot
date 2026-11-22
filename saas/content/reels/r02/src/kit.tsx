import React from 'react';
import { AbsoluteFill, Audio, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, Easing } from 'remotion';
import '@fontsource/bricolage-grotesque/700.css';
import '@fontsource/bricolage-grotesque/800.css';
import '@fontsource/manrope/600.css';
import '@fontsource/manrope/700.css';
import '@fontsource/manrope/800.css';
import '@fontsource/jetbrains-mono/700.css';
import { C, F } from './brand';

export const FPS = 30;

export const f = (s: number) => Math.round(s * FPS);

// ---------- helpers ----------
export const useT = () => useCurrentFrame() / FPS;                       // seconds inside the current Sequence
export const pop = (frame: number, at: number, fps = FPS) => spring({ frame: frame - f(at), fps, config: { damping: 11, stiffness: 170, mass: 0.7 } });
export const ease = (t: number, a: number, b: number) => interpolate(t, [a, b], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });

export const Dots: React.FC<{ color?: string; dot?: string }> = ({ color = C.paper, dot = 'rgba(17,19,24,.13)' }) => (
  <AbsoluteFill style={{ background: color, backgroundImage: `radial-gradient(${dot} 3px, transparent 3.6px)`, backgroundSize: '52px 52px' }} />
);

export const Card: React.FC<{ style?: React.CSSProperties; children: React.ReactNode; bg?: string }> = ({ style, children, bg = C.white }) => (
  <div style={{ background: bg, border: `5px solid ${C.ink}`, borderRadius: 34, boxShadow: `14px 14px 0 ${C.ink}`, ...style }}>{children}</div>
);

export const Pill: React.FC<{ children: React.ReactNode; bg?: string; color?: string; style?: React.CSSProperties }> = ({ children, bg = C.volt, color = C.ink, style }) => (
  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 12, background: bg, color, border: `4px solid ${C.ink}`, borderRadius: 999,
    padding: '8px 24px', font: `700 30px ${F.mono}`, letterSpacing: '.06em', textTransform: 'uppercase', ...style }}>{children}</span>
);

export const Logo: React.FC<{ size: number }> = ({ size }) => (
  <svg width={size} height={size} viewBox="0 0 32 32">
    <rect width="32" height="32" rx="9" fill={C.cobalt} />
    <path d="M9.6 8.5h12.8a3.1 3.1 0 0 1 3.1 3.1v7.1a3.1 3.1 0 0 1-3.1 3.1h-6.6l-4.6 3.6a.6.6 0 0 1-1-.5v-3.1h-.6a3.1 3.1 0 0 1-3.1-3.1v-7.1a3.1 3.1 0 0 1 3.1-3.1z" fill="#fff" />
    <path d="M15.4 11.9l-3.1 2.7 3.1 2.7" stroke={C.cobalt} strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    <path d="M12.7 14.6h5.5a2.6 2.6 0 0 1 2.6 2.6v1" stroke={C.cobalt} strokeWidth="1.9" strokeLinecap="round" fill="none" />
  </svg>
);

export const ClaudeMark: React.FC<{ size: number }> = ({ size }) => (
  <svg width={size} height={size} viewBox="0 0 32 32"><g fill="#D97757">
    {Array.from({ length: 10 }).map((_, i) => <rect key={i} x="15" y="3" width="2.4" height="13" rx="1.2" transform={`rotate(${i * 36} 16 16)`} />)}</g></svg>
);

export const Wordmark: React.FC<{ size: number; dark?: boolean }> = ({ size, dark }) => (
  <span style={{ display: 'inline-flex', alignItems: 'center', gap: size * 0.3 }}>
    <Logo size={size} />
    <span style={{ font: `800 ${size * 0.7}px/1 ${F.head}`, letterSpacing: '-.04em', color: dark ? '#fff' : C.ink }}>Reply<span style={{ color: dark ? C.volt : C.cobalt }}>Inbox</span></span>
  </span>
);

// Drop + squash entrance
export const Drop: React.FC<{ at: number; children: React.ReactNode; style?: React.CSSProperties; from?: number }> = ({ at, children, style, from = -120 }) => {
  const fr = useCurrentFrame();
  const p = pop(fr, at);
  const sq = interpolate(p, [0, 0.7, 1, 1.15], [1, 1, 1, 0.96], { extrapolateRight: 'clamp' });
  return <div style={{ opacity: p > 0.02 ? 1 : 0, transform: `translateY(${(1 - Math.min(p, 1)) * from}px) scale(${Math.min(p, 1.04)}, ${sq})`, transformOrigin: '50% 100%', ...style }}>{children}</div>;
};

export const Stamp: React.FC<{ at: number; children: React.ReactNode; style?: React.CSSProperties; rot?: number }> = ({ at, children, style, rot = -6 }) => {
  const fr = useCurrentFrame();
  const p = pop(fr, at);
  const sc = interpolate(p, [0, 1], [2.2, 1]);
  return <div style={{ opacity: p > 0.02 ? Math.min(1, p * 2) : 0, transform: `scale(${sc}) rotate(${rot}deg)`, ...style }}>{children}</div>;
};

export const Cursor: React.FC<{ path: [number, number, number][]; clickAt?: number[] }> = ({ path, clickAt = [] }) => {
  const t = useT();
  let x = path[0][1], y = path[0][2];
  for (let i = 1; i < path.length; i++) {
    const [t1, x1, y1] = path[i]; const [t0, x0, y0] = path[i - 1];
    if (t >= t0) { const k = ease(t, t0, t1); x = x0 + (x1 - x0) * k; y = y0 + (y1 - y0) * k; }
  }
  const click = clickAt.some(c => t >= c && t < c + 0.18);
  const ring = clickAt.map(c => ease(t, c, c + 0.4)).find((k, i) => t >= clickAt[i] && t < clickAt[i] + 0.4);
  return (
    <div style={{ position: 'absolute', left: x, top: y, zIndex: 20 }}>
      {ring !== undefined && <div style={{ position: 'absolute', left: -40 * ring, top: -40 * ring, width: 80 * ring, height: 80 * ring, borderRadius: '50%', border: `6px solid ${C.cobalt}`, opacity: 1 - ring }} />}
      <svg width="64" height="64" viewBox="0 0 24 24" style={{ transform: `scale(${click ? 0.85 : 1})`, filter: 'drop-shadow(3px 3px 0 rgba(17,19,24,.35))' }}>
        <path d="M4 2l14 9-6 1.4L15 20l-3 1.4-3.2-7.6L4 18z" fill="#fff" stroke={C.ink} strokeWidth="1.6" strokeLinejoin="round" /></svg>
    </div>
  );
};

export const Typed: React.FC<{ text: string; from: number; to: number }> = ({ text, from, to }) => {
  const t = useT();
  const n = Math.round(text.length * ease(t, from, to));
  return <span>{text.slice(0, n)}{t >= from && t < to + 0.3 && Math.floor(t * 3) % 2 === 0 ? <span style={{ color: C.cobalt }}>|</span> : null}</span>;
};

export const Window: React.FC<{ url: string; children: React.ReactNode; style?: React.CSSProperties }> = ({ url, children, style }) => (
  <Card style={{ overflow: 'hidden', ...style }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '18px 26px', borderBottom: `4px solid ${C.ink}`, background: C.mist }}>
      {[C.coral, C.volt, C.win].map(c => <span key={c} style={{ width: 20, height: 20, borderRadius: '50%', background: c, border: `3px solid ${C.ink}` }} />)}
      <span style={{ marginLeft: 16, flex: 1, background: '#fff', border: `3px solid ${C.ink}`, borderRadius: 999, padding: '6px 20px', font: `700 24px ${F.mono}`, color: '#555' }}>{url}</span>
    </div>
    <div style={{ padding: 34 }}>{children}</div>
  </Card>
);

export const Btn: React.FC<{ children: React.ReactNode; active?: boolean; bg?: string; color?: string; style?: React.CSSProperties }> = ({ children, active, bg = C.cobalt, color = '#fff', style }) => (
  <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 14, background: bg, color, border: `5px solid ${C.ink}`, borderRadius: 22,
    boxShadow: active ? `2px 2px 0 ${C.ink}` : `8px 8px 0 ${C.ink}`, transform: active ? 'translate(6px,6px)' : 'none', padding: '20px 36px', font: `800 40px ${F.body}`, ...style }}>{children}</div>
);

