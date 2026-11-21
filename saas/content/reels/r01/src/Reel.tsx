import React from 'react';
import { AbsoluteFill, Audio, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, Easing } from 'remotion';
import '@fontsource/bricolage-grotesque/700.css';
import '@fontsource/bricolage-grotesque/800.css';
import '@fontsource/manrope/600.css';
import '@fontsource/manrope/700.css';
import '@fontsource/manrope/800.css';
import '@fontsource/jetbrains-mono/700.css';
import TL from './timeline.json';
import { C, F } from './brand';

const FPS = 30;
export const TOTAL = Math.round(TL.end * FPS);
const f = (s: number) => Math.round(s * FPS);

// ---------- helpers ----------
const useT = () => useCurrentFrame() / FPS;                       // seconds inside the current Sequence
const pop = (frame: number, at: number, fps = FPS) => spring({ frame: frame - f(at), fps, config: { damping: 11, stiffness: 170, mass: 0.7 } });
const ease = (t: number, a: number, b: number) => interpolate(t, [a, b], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });

const Dots: React.FC<{ color?: string; dot?: string }> = ({ color = C.paper, dot = 'rgba(17,19,24,.13)' }) => (
  <AbsoluteFill style={{ background: color, backgroundImage: `radial-gradient(${dot} 3px, transparent 3.6px)`, backgroundSize: '52px 52px' }} />
);

const Card: React.FC<{ style?: React.CSSProperties; children: React.ReactNode; bg?: string }> = ({ style, children, bg = C.white }) => (
  <div style={{ background: bg, border: `5px solid ${C.ink}`, borderRadius: 34, boxShadow: `14px 14px 0 ${C.ink}`, ...style }}>{children}</div>
);

const Pill: React.FC<{ children: React.ReactNode; bg?: string; color?: string; style?: React.CSSProperties }> = ({ children, bg = C.volt, color = C.ink, style }) => (
  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 12, background: bg, color, border: `4px solid ${C.ink}`, borderRadius: 999,
    padding: '8px 24px', font: `700 30px ${F.mono}`, letterSpacing: '.06em', textTransform: 'uppercase', ...style }}>{children}</span>
);

const Logo: React.FC<{ size: number }> = ({ size }) => (
  <svg width={size} height={size} viewBox="0 0 32 32">
    <rect width="32" height="32" rx="9" fill={C.cobalt} />
    <path d="M9.6 8.5h12.8a3.1 3.1 0 0 1 3.1 3.1v7.1a3.1 3.1 0 0 1-3.1 3.1h-6.6l-4.6 3.6a.6.6 0 0 1-1-.5v-3.1h-.6a3.1 3.1 0 0 1-3.1-3.1v-7.1a3.1 3.1 0 0 1 3.1-3.1z" fill="#fff" />
    <path d="M15.4 11.9l-3.1 2.7 3.1 2.7" stroke={C.cobalt} strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    <path d="M12.7 14.6h5.5a2.6 2.6 0 0 1 2.6 2.6v1" stroke={C.cobalt} strokeWidth="1.9" strokeLinecap="round" fill="none" />
  </svg>
);

const ClaudeMark: React.FC<{ size: number }> = ({ size }) => (
  <svg width={size} height={size} viewBox="0 0 32 32"><g fill="#D97757">
    {Array.from({ length: 10 }).map((_, i) => <rect key={i} x="15" y="3" width="2.4" height="13" rx="1.2" transform={`rotate(${i * 36} 16 16)`} />)}</g></svg>
);

const Wordmark: React.FC<{ size: number; dark?: boolean }> = ({ size, dark }) => (
  <span style={{ display: 'inline-flex', alignItems: 'center', gap: size * 0.3 }}>
    <Logo size={size} />
    <span style={{ font: `800 ${size * 0.7}px/1 ${F.head}`, letterSpacing: '-.04em', color: dark ? '#fff' : C.ink }}>Reply<span style={{ color: dark ? C.volt : C.cobalt }}>Inbox</span></span>
  </span>
);

// Drop + squash entrance
const Drop: React.FC<{ at: number; children: React.ReactNode; style?: React.CSSProperties; from?: number }> = ({ at, children, style, from = -120 }) => {
  const fr = useCurrentFrame();
  const p = pop(fr, at);
  const sq = interpolate(p, [0, 0.7, 1, 1.15], [1, 1, 1, 0.96], { extrapolateRight: 'clamp' });
  return <div style={{ opacity: p > 0.02 ? 1 : 0, transform: `translateY(${(1 - Math.min(p, 1)) * from}px) scale(${Math.min(p, 1.04)}, ${sq})`, transformOrigin: '50% 100%', ...style }}>{children}</div>;
};

const Stamp: React.FC<{ at: number; children: React.ReactNode; style?: React.CSSProperties; rot?: number }> = ({ at, children, style, rot = -6 }) => {
  const fr = useCurrentFrame();
  const p = pop(fr, at);
  const sc = interpolate(p, [0, 1], [2.2, 1]);
  return <div style={{ opacity: p > 0.02 ? Math.min(1, p * 2) : 0, transform: `scale(${sc}) rotate(${rot}deg)`, ...style }}>{children}</div>;
};

const Cursor: React.FC<{ path: [number, number, number][]; clickAt?: number[] }> = ({ path, clickAt = [] }) => {
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

const Typed: React.FC<{ text: string; from: number; to: number }> = ({ text, from, to }) => {
  const t = useT();
  const n = Math.round(text.length * ease(t, from, to));
  return <span>{text.slice(0, n)}{t >= from && t < to + 0.3 && Math.floor(t * 3) % 2 === 0 ? <span style={{ color: C.cobalt }}>|</span> : null}</span>;
};

const Window: React.FC<{ url: string; children: React.ReactNode; style?: React.CSSProperties }> = ({ url, children, style }) => (
  <Card style={{ overflow: 'hidden', ...style }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '18px 26px', borderBottom: `4px solid ${C.ink}`, background: C.mist }}>
      {[C.coral, C.volt, C.win].map(c => <span key={c} style={{ width: 20, height: 20, borderRadius: '50%', background: c, border: `3px solid ${C.ink}` }} />)}
      <span style={{ marginLeft: 16, flex: 1, background: '#fff', border: `3px solid ${C.ink}`, borderRadius: 999, padding: '6px 20px', font: `700 24px ${F.mono}`, color: '#555' }}>{url}</span>
    </div>
    <div style={{ padding: 34 }}>{children}</div>
  </Card>
);

const Btn: React.FC<{ children: React.ReactNode; active?: boolean; bg?: string; color?: string; style?: React.CSSProperties }> = ({ children, active, bg = C.cobalt, color = '#fff', style }) => (
  <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 14, background: bg, color, border: `5px solid ${C.ink}`, borderRadius: 22,
    boxShadow: active ? `2px 2px 0 ${C.ink}` : `8px 8px 0 ${C.ink}`, transform: active ? 'translate(6px,6px)' : 'none', padding: '20px 36px', font: `800 40px ${F.body}`, ...style }}>{children}</div>
);

// ---------- persistent layers ----------
const Header: React.FC = () => (
  <div style={{ position: 'absolute', top: 262, left: 50, right: 50, display: 'flex', justifyContent: 'space-between', zIndex: 30 }}>
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 12, background: C.ink, color: '#fff', borderRadius: 999, padding: '12px 26px', font: `700 28px ${F.mono}`, letterSpacing: '.05em' }}>
      <span style={{ width: 18, height: 18, borderRadius: '50%', background: C.volt }} />CLAUDE × REPLYINBOX</span>
    <span style={{ background: C.ink, color: '#fff', borderRadius: 999, padding: '12px 26px', font: `700 28px ${F.mono}`, letterSpacing: '.05em' }}>INSTA MANAGER</span>
  </div>
);

const Captions: React.FC = () => {
  const t = useT();
  const ph = TL.phrases.find(p => t >= p.s - 0.05 && t < p.e + 0.18);
  if (!ph) return null;
  const k = ph.words.filter(w => t >= w.s).length - 1;
  return (
    <div style={{ position: 'absolute', left: 60, right: 60, top: 1182, display: 'flex', justifyContent: 'center', zIndex: 40 }}>
      <div style={{ background: C.ink, borderRadius: 26, padding: '16px 30px', maxWidth: 960, textAlign: 'center', font: `800 54px/1.18 ${F.head}`, letterSpacing: '-.02em', boxShadow: `8px 8px 0 ${C.cobalt}` }}>
        {ph.words.map((w, i) => (
          <span key={i} style={{ color: i <= k ? (w.key ? C.volt : '#fff') : 'rgba(255,255,255,.35)', marginRight: 20, display: 'inline-block',
            transform: i === k ? 'scale(1.08)' : 'none' }}>{w.w}</span>
        ))}
      </div>
    </div>
  );
};

type Ch = { at: number; until: number; pose: string; side: 'l' | 'r'; h?: number };
const CHARS: Ch[] = [
  { at: 0, until: 2.30, pose: 'portrait-pointing-at-the-viewer', side: 'r' },
  { at: 2.30, until: 5.30, pose: 'looking-at-the-phone-smiling', side: 'l' },
  { at: 5.30, until: 7.75, pose: 'holding-a-laptop-typing', side: 'r' },
  { at: 7.75, until: 10.62, pose: 'portrait-pointing-to-his-left-viewer-s-r', side: 'l' },
  { at: 10.62, until: 15.36, pose: 'sitting-cross-legged-with-a-laptop', side: 'r' },
  { at: 15.36, until: 17.95, pose: 'portrait-thumbs-up', side: 'l' },
  { at: 17.95, until: 23.50, pose: 'hand-on-chin-arm-crossed-smirk', side: 'r' },
  { at: 23.50, until: 28.10, pose: 'presenting-with-one-hand-other-in-pocket', side: 'l' },
  { at: 28.10, until: 32.55, pose: 'hands-behind-head', side: 'r' },
  { at: 32.55, until: 33.55, pose: 'portrait-both-fists-up-shouting', side: 'l' },
  { at: 33.55, until: 37.78, pose: 'portrait-peace-sign-wink', side: 'r' },
  { at: 37.78, until: 39.05, pose: 'beckoning-hand-gesture', side: 'l' },
  { at: 39.05, until: 41.19, pose: 'jumping-fists-up', side: 'r' },
];
const Character: React.FC = () => {
  const fr = useCurrentFrame(); const t = fr / FPS;
  const c = CHARS.find(x => t >= x.at && t < x.until);
  if (!c) return null;
  const p = pop(fr, c.at);
  const bob = Math.sin(t * 5) * 6;
  return (
    <div style={{ position: 'absolute', bottom: -30, [c.side === 'l' ? 'left' : 'right']: -10, height: c.h ?? 640, zIndex: 25,
      transform: `translateY(${(1 - Math.min(p, 1)) * 300 + bob}px) scaleY(${interpolate(p, [0, 1, 1.12], [1, 1, 0.95], { extrapolateRight: 'clamp' })})`, transformOrigin: '50% 100%' }}>
      <Img src={staticFile(`chars/${c.pose}.png`)} style={{ height: '100%' }} />
    </div>
  );
};

// ---------- scenes (times are absolute seconds; each scene is a Sequence from its start) ----------
const Stage: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{ position: 'absolute', left: 60, right: 60, top: 360, height: 790, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>{children}</div>
);
const StepTag: React.FC<{ n: number; text: string; at?: number }> = ({ n, text, at = 0 }) => (
  <Drop at={at} style={{ alignSelf: 'flex-start', marginBottom: 30 }}><Pill>STEP {n} · {text}</Pill></Drop>
);

const S1: React.FC = () => {
  const fr = useCurrentFrame();
  return (
    <Stage>
      <Drop at={0.05}><Card style={{ padding: '44px 54px', textAlign: 'center' }}>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 26, marginBottom: 26 }}>
          <ClaudeMark size={96} /><span style={{ font: `800 70px ${F.head}` }}>×</span><Logo size={96} /></div>
        <div style={{ font: `800 92px/1.02 ${F.head}`, letterSpacing: '-.05em' }}>Apna <span style={{ background: C.volt, padding: '0 14px', border: `5px solid ${C.ink}`, borderRadius: 16 }}>Insta manager</span></div>
        <div style={{ font: `800 92px/1.1 ${F.head}`, letterSpacing: '-.05em' }}>banao 👇</div>
      </Card></Drop>
      <div style={{ marginTop: 40, opacity: ease(fr / FPS, 0.9, 1.3) }}><Pill bg={C.ink} color="#fff">Claude + ReplyInbox · step by step</Pill></div>
    </Stage>
  );
};

const S2: React.FC = () => {  // starts 2.30
  const t = useT();
  return (
  <Stage>
    <StepTag n={1} text="ReplyInbox" />
    <Drop at={0.6}><Window url="replyinbox.in" style={{ width: 900 }}>
      <div style={{ textAlign: 'center', padding: '20px 0' }}>
        <Wordmark size={92} />
        <div style={{ font: `700 36px ${F.body}`, color: '#555', margin: '24px 0 40px' }}>Instagram DMs on autopilot</div>
        <Btn active={t > 2.45 && t < 2.8}>📸 Continue with Instagram</Btn>
      </div>
    </Window></Drop>
    <Cursor path={[[0, 900, 900], [1.9, 560, 640], [2.4, 540, 650]]} clickAt={[2.45]} />
  </Stage>
  );
};

const S3: React.FC = () => {  // starts 5.30
  const t = useT();
  return (
    <Stage>
      <StepTag n={1} text="ReplyInbox" />
      <Window url="replyinbox.in/app/settings" style={{ width: 920 }}>
        <div style={{ display: 'flex', gap: 30 }}>
          <div style={{ width: 230, display: 'flex', flexDirection: 'column', gap: 12, font: `700 30px ${F.body}` }}>
            {['Home', 'Automations', 'Inbox', 'Store', 'Settings'].map(x => (
              <div key={x} style={{ padding: '10px 16px', borderRadius: 14, background: x === 'Settings' && t > 0.2 ? C.volt : 'transparent', border: x === 'Settings' && t > 0.2 ? `3px solid ${C.ink}` : '3px solid transparent' }}>{x}</div>))}
          </div>
          <div style={{ flex: 1, borderLeft: `3px dashed ${C.mist}`, paddingLeft: 30 }}>
            <div style={{ font: `800 44px ${F.head}`, letterSpacing: '-.03em', display: 'flex', alignItems: 'center', gap: 14 }}><ClaudeMark size={46} /> Connect Claude</div>
            <div style={{ font: `600 28px/1.35 ${F.body}`, color: '#555', margin: '14px 0 26px' }}>Run automations, sales and DMs by chatting with Claude.</div>
            <Btn active={t > 1.3 && t < 1.6} style={{ fontSize: 36 }}>Create Claude link</Btn>
            {t > 1.6 && <Drop at={1.6}><div style={{ marginTop: 26, display: 'flex', gap: 12, alignItems: 'center' }}>
              <span style={{ flex: 1, background: C.mist, border: `3px solid ${C.ink}`, borderRadius: 14, padding: '10px 16px', font: `700 24px ${F.mono}` }}>replyinbox.in/mcp/••••••</span>
              <Pill bg={C.win} color="#fff" style={{ fontSize: 24 }}>Copied ✓</Pill></div></Drop>}
          </div>
        </div>
      </Window>
      <Cursor path={[[0, 820, 980], [1.1, 420, 740], [1.3, 410, 745]]} clickAt={[1.3]} />
    </Stage>
  );
};

const S4: React.FC = () => {  // starts 7.75
  const t = useT();
  const cust = t > 0.95, conn = t > 1.9;
  return (
    <Stage>
      <StepTag n={2} text="Claude" />
      <Window url="claude.ai" style={{ width: 920 }}>
        <div style={{ display: 'flex', gap: 30, minHeight: 380 }}>
          <div style={{ width: 250, display: 'flex', flexDirection: 'column', gap: 12, font: `700 30px ${F.body}` }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, font: `800 34px ${F.head}`, marginBottom: 8 }}><ClaudeMark size={38} />Claude</div>
            {['New chat', 'Chats', 'Projects', 'Customize'].map(x => (
              <div key={x} style={{ padding: '10px 16px', borderRadius: 14, background: x === 'Customize' && cust ? C.volt : 'transparent', border: x === 'Customize' && cust ? `3px solid ${C.ink}` : '3px solid transparent' }}>{x}</div>))}
          </div>
          <div style={{ flex: 1, borderLeft: `3px dashed ${C.mist}`, paddingLeft: 30 }}>
            {!cust ? <div style={{ font: `800 48px ${F.head}`, color: '#999', marginTop: 120 }}>Good morning ✳</div> : <>
              <div style={{ font: `800 44px ${F.head}`, marginBottom: 20 }}>Customize</div>
              {['Skills', 'Connectors', 'Styles'].map(x => (
                <div key={x} style={{ padding: '18px 20px', marginBottom: 14, borderRadius: 18, font: `700 32px ${F.body}`, border: `4px solid ${C.ink}`,
                  background: x === 'Connectors' && conn ? C.volt : '#fff', boxShadow: x === 'Connectors' && conn ? `6px 6px 0 ${C.ink}` : 'none' }}>{x} <span style={{ float: 'right' }}>›</span></div>))}
            </>}
          </div>
        </div>
      </Window>
      <Cursor path={[[0, 860, 1000], [0.8, 160, 740], [1.0, 150, 745], [1.7, 560, 760], [1.9, 560, 765]]} clickAt={[0.95, 1.9]} />
    </Stage>
  );
};

const S5: React.FC = () => {  // starts 10.62
  const t = useT();
  return (
    <Stage>
      <StepTag n={2} text="Claude" />
      <Drop at={0.15}><Card style={{ width: 900, padding: 40 }}>
        <div style={{ font: `800 50px ${F.head}`, letterSpacing: '-.03em', marginBottom: 28 }}>Add custom connector</div>
        <div style={{ font: `700 28px ${F.mono}`, color: '#555', marginBottom: 10 }}>NAME</div>
        <div style={{ border: `4px solid ${C.ink}`, borderRadius: 16, padding: '16px 20px', font: `800 40px ${F.body}`, minHeight: 82, background: t > 1.4 && t < 2.9 ? '#FAFFE6' : '#fff' }}>
          <Typed text="ReplyInbox" from={1.5} to={2.6} /></div>
        <div style={{ font: `700 28px ${F.mono}`, color: '#555', margin: '26px 0 10px' }}>REMOTE MCP SERVER URL</div>
        <div style={{ border: `4px solid ${C.ink}`, borderRadius: 16, padding: '16px 20px', font: `700 32px ${F.mono}`, minHeight: 78, background: t > 3.0 && t < 4.1 ? '#FAFFE6' : '#fff' }}>
          {t > 3.2 ? <Stamp at={3.2} rot={0}>https://replyinbox.in/mcp/••••</Stamp> : null}</div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 20, marginTop: 32 }}>
          <Btn bg="#fff" color={C.ink} style={{ fontSize: 34 }}>Cancel</Btn><Btn active={t > 4.25 && t < 4.6} style={{ fontSize: 34 }}>Add</Btn></div>
      </Card></Drop>
      <Cursor path={[[0, 900, 1000], [1.2, 400, 560], [2.8, 400, 560], [3.1, 400, 740], [3.9, 400, 740], [4.2, 790, 905]]} clickAt={[1.3, 3.15, 4.28]} />
    </Stage>
  );
};

const S6: React.FC = () => {  // starts 15.36
  const t = useT();
  return (
    <Stage>
      <Window url="claude.ai · Connectors" style={{ width: 900 }}>
        {['Google Drive', 'Gmail', 'ReplyInbox'].map(x => (
          <div key={x} style={{ display: 'flex', alignItems: 'center', gap: 18, padding: '18px 20px', marginBottom: 14, borderRadius: 18, border: `4px solid ${C.ink}`,
            background: x === 'ReplyInbox' && t > 0.5 ? '#F4FFD6' : '#fff', font: `800 36px ${F.body}` }}>
            {x === 'ReplyInbox' ? <Logo size={52} /> : <span style={{ width: 52, height: 52, borderRadius: 12, background: C.mist, border: `3px solid ${C.ink}` }} />}
            <span style={{ flex: 1 }}>{x}</span>
            {x === 'ReplyInbox' ? (t > 0.5 ? <Pill bg={C.win} color="#fff" style={{ fontSize: 26 }}>✓ Connected</Pill> : null) : <span style={{ font: `700 26px ${F.mono}`, color: '#888' }}>Connect</span>}
          </div>))}
      </Window>
      <Stamp at={0.05} style={{ position: 'absolute', top: 40, right: 20 }} rot={8}>
        <span style={{ display: 'inline-block', background: C.volt, border: `6px solid ${C.ink}`, borderRadius: 22, boxShadow: `10px 10px 0 ${C.ink}`, padding: '10px 30px', font: `800 84px ${F.head}`, letterSpacing: '-.04em' }}>HO GAYA!</span></Stamp>
    </Stage>
  );
};

const ROWS = [['Reel · Claude tips', 92, 61, '₹1,490'], ['Reel · DM hacks', 68, 44, '₹745'], ['Carousel · prompts', 41, 18, '₹0']] as const;
const S7: React.FC = () => {  // starts 17.95
  const t = useT();
  return (
    <Stage>
      <Window url="claude.ai · ReplyInbox" style={{ width: 920 }}>
        <div style={{ alignSelf: 'flex-end', marginLeft: 'auto', width: 'fit-content', background: C.mist, border: `3px solid ${C.ink}`, borderRadius: 22, padding: '12px 22px', font: `700 30px ${F.body}`, marginBottom: 22 }}>Meri profile study karo</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, font: `800 34px ${F.head}`, marginBottom: 16 }}><ClaudeMark size={36} /> Reel report <Pill bg={C.mist} style={{ fontSize: 20, padding: '4px 14px', marginLeft: 'auto' }}>Illustration</Pill></div>
        {ROWS.map(([name, fol, sale, rev], i) => {
          const k = ease(t, 0.9 + i * 0.35, 1.8 + i * 0.35);
          return (
            <div key={name} style={{ marginBottom: 18 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', font: `700 28px ${F.body}`, marginBottom: 6 }}><span>{name}</span><b style={{ font: `700 28px ${F.mono}` }}>{t > 3.4 ? rev : '…'}</b></div>
              <div style={{ height: 30, border: `3px solid ${C.ink}`, borderRadius: 999, background: '#fff', overflow: 'hidden' }}>
                <div style={{ width: `${fol * k}%`, height: '100%', background: i === 0 ? C.cobalt : '#9AA3FF' }} /></div>
            </div>);
        })}
        <div style={{ font: `700 22px ${F.mono}`, color: '#666' }}>FOLLOWS / 1K VIEWS · SALES PER REEL</div>
      </Window>
      <Stamp at={2.9} style={{ position: 'absolute', top: -30, left: 10 }} rot={-5}>
        <span style={{ display: 'inline-block', background: C.volt, border: `6px solid ${C.ink}`, borderRadius: 20, boxShadow: `10px 10px 0 ${C.ink}`, padding: '8px 26px', font: `800 64px ${F.head}` }}>FOLLOWERS + SALES</span></Stamp>
    </Stage>
  );
};

const S8: React.FC = () => {  // starts 23.50
  const t = useT();
  const items = [['Hook', 1.98], ['Script', 2.43], ['Caption', 3.04], ['Comment keyword', 3.62]] as const;
  return (
    <Stage>
      <Drop at={0.05}><Card style={{ width: 880, padding: 40 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 26 }}><Pill>Reel draft</Pill><span style={{ font: `800 44px ${F.head}` }}>Tue · 7 PM</span></div>
        {items.map(([x, at]) => (
          <div key={x} style={{ display: 'flex', alignItems: 'center', gap: 22, padding: '14px 0', font: `800 52px ${F.head}`, letterSpacing: '-.03em', opacity: t > at - 0.1 ? 1 : 0.25 }}>
            <span style={{ width: 70, height: 70, borderRadius: 18, border: `5px solid ${C.ink}`, background: t > at ? C.volt : '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', font: `800 46px ${F.head}`,
              transform: `scale(${t > at ? 1 + 0.25 * Math.max(0, 1 - (t - at) * 4) : 1})` }}>{t > at ? '✓' : ''}</span>{x}
            {x === 'Comment keyword' && t > at ? <Pill bg={C.cobalt} color="#fff" style={{ fontSize: 28 }}>SETUP</Pill> : null}
          </div>))}
      </Card></Drop>
    </Stage>
  );
};

const S9: React.FC = () => {  // starts 28.10
  const t = useT();
  const frame = useCurrentFrame();
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  return (
    <Stage>
      <Card style={{ width: 940, padding: 34 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24 }}><span style={{ font: `800 46px ${F.head}`, letterSpacing: '-.03em' }}>This week's reels</span>
          <Pill bg={C.mist} style={{ marginLeft: 'auto', fontSize: 22 }}>Your brand</Pill></div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 12 }}>
          {days.map((d, i) => {
            const at = 0.25 + i * 0.22; const p = pop(frame, at);
            return (
              <div key={d} style={{ textAlign: 'center' }}>
                <div style={{ font: `700 24px ${F.mono}`, marginBottom: 8 }}>{d}</div>
                <div style={{ height: 230, border: `4px solid ${C.ink}`, borderRadius: 16, background: i % 2 ? '#E9EBFF' : '#F4FFD6', transform: `scale(${Math.min(p, 1.05)})`, opacity: p > 0.02 ? 1 : 0,
                  display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', padding: 8 }}>
                  <div style={{ height: 10, background: C.ink, borderRadius: 6, marginBottom: 8, width: '80%' }} /><div style={{ height: 10, background: '#888', borderRadius: 6, width: '55%' }} /></div>
              </div>);
          })}
        </div>
        <div style={{ marginTop: 28, textAlign: 'center', opacity: t > 3.05 ? 1 : 0 }}>
          <Stamp at={3.05} rot={0}><Pill bg={C.volt} style={{ fontSize: 30 }}>⏳ Waiting for your approval</Pill></Stamp></div>
      </Card>
      <Stamp at={0.2} style={{ position: 'absolute', top: -20, right: 0 }} rot={7}>
        <span style={{ display: 'inline-block', background: C.cobalt, color: '#fff', border: `6px solid ${C.ink}`, borderRadius: 20, boxShadow: `10px 10px 0 ${C.ink}`, padding: '6px 24px', font: `800 60px ${F.head}` }}>1 WEEK</span></Stamp>
    </Stage>
  );
};

const S10: React.FC = () => (  // starts 32.55
  <Stage>
    <Stamp at={0.05} rot={-4}>
      <div style={{ background: C.coral, border: `7px solid ${C.ink}`, borderRadius: 34, boxShadow: `16px 16px 0 ${C.ink}`, padding: '40px 54px', textAlign: 'center', color: '#fff' }}>
        <div style={{ font: `800 118px/0.95 ${F.head}`, letterSpacing: '-.05em' }}>SABSE<br /><span style={{ background: C.volt, color: C.ink, padding: '0 16px', borderRadius: 16 }}>MAST</span> PART?</div>
      </div></Stamp>
  </Stage>
);

const S11: React.FC = () => {  // starts 33.55
  const t = useT();
  return (
    <Stage>
      <div style={{ width: 920, display: 'flex', flexDirection: 'column', gap: 26 }}>
        <Drop at={0.1}><Card style={{ padding: 28 }}>
          <div style={{ font: `700 24px ${F.mono}`, color: '#666', marginBottom: 10 }}>COMMENTS ON YOUR REEL</div>
          {[['riya.creates', 'SETUP 🙌'], ['ankit_fit', 'setup pls'], ['meera.ai', 'SETUP']].map(([u, c], i) => (
            <div key={u} style={{ display: 'flex', gap: 14, alignItems: 'center', font: `700 34px ${F.body}`, padding: '6px 0', opacity: t > 0.3 + i * 0.35 ? 1 : 0 }}>
              <span style={{ width: 46, height: 46, borderRadius: '50%', background: ['#FFB199', '#9AA3FF', '#D4FF3A'][i], border: `3px solid ${C.ink}` }} /><b>{u}</b><span>{c}</span>
              {t > 1.6 + i * 0.4 ? <Pill bg={C.win} color="#fff" style={{ fontSize: 20, marginLeft: 'auto', padding: '4px 14px' }}>DM sent</Pill> : null}</div>))}
        </Card></Drop>
        <div style={{ textAlign: 'center', font: `800 60px ${F.head}`, opacity: t > 1.1 ? 1 : 0 }}>↓</div>
        <Drop at={2.4}><Card style={{ padding: 28, background: '#F7F8FF' }}>
          <div style={{ font: `700 24px ${F.mono}`, color: '#666', marginBottom: 12 }}>AUTO DM</div>
          <div style={{ background: C.cobalt, color: '#fff', border: `4px solid ${C.ink}`, borderRadius: 26, borderBottomRightRadius: 8, padding: '18px 24px', font: `700 36px/1.3 ${F.body}`, marginLeft: 120 }}>
            Ye raha tumhara link 👇<div style={{ marginTop: 12, background: '#fff', color: C.cobalt, borderRadius: 14, padding: '10px 16px', font: `800 30px ${F.body}`, textAlign: 'center' }}>Open the guide</div></div>
        </Card></Drop>
      </div>
    </Stage>
  );
};

const S12: React.FC = () => {  // starts 37.78
  const t = useT();
  return (
    <Stage>
      <Window url="claude.ai · ReplyInbox" style={{ width: 920 }}>
        <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start', font: `700 36px/1.35 ${F.body}` }}><ClaudeMark size={44} />
          <span>Is reel pe <b>comment-to-DM</b> set karun? Keyword: <b style={{ color: C.cobalt }}>SETUP</b></span></div>
        <div style={{ display: 'flex', gap: 22, marginTop: 30 }}>
          <Btn active={t > 0.55 && t < 0.9} bg={C.volt} color={C.ink}>Haan ✓</Btn><Btn bg="#fff" color={C.ink}>Nahi</Btn></div>
        {t > 0.9 && <Drop at={0.9}><div style={{ marginTop: 26 }}><Pill bg={C.win} color="#fff">✓ Automation on</Pill></div></Drop>}
      </Window>
      <div style={{ marginTop: 34, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14 }}>
        <Pill bg={C.ink} color="#fff" style={{ fontSize: 26 }}>Claude har change se pehle poochta hai</Pill>
        <Pill bg={C.mist} style={{ fontSize: 26 }}>Connect Claude: Pro plan</Pill></div>
      <Cursor path={[[0, 860, 980], [0.45, 250, 470], [0.6, 245, 475]]} clickAt={[0.6]} />
    </Stage>
  );
};

const S13: React.FC = () => {  // starts 39.05, cobalt
  const fr = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Dots color={C.cobalt} dot="rgba(255,255,255,.14)" />
      <Stage>
        <Drop at={0.05}><div style={{ font: `800 120px ${F.head}`, color: '#fff', letterSpacing: '-.05em', textAlign: 'center' }}>Comment</div></Drop>
        <Stamp at={0.2} rot={-3}><div style={{ margin: '24px 0 40px', background: C.volt, border: `7px solid ${C.ink}`, borderRadius: 34, boxShadow: `16px 16px 0 ${C.ink}`, padding: '16px 56px', font: `700 170px ${F.mono}`, color: C.ink }}>SETUP</div></Stamp>
        <div style={{ opacity: ease(fr / FPS, 1.0, 1.4), font: `800 58px/1.15 ${F.head}`, color: '#fff', textAlign: 'center', letterSpacing: '-.03em' }}>Main poora setup<br /><span style={{ color: C.volt }}>DM</span> kar dunga 📩</div>
      </Stage>
    </AbsoluteFill>
  );
};

const FollowCard: React.FC = () => {
  const fr = useCurrentFrame();
  const p = pop(fr, 0.02);
  return (
    <AbsoluteFill>
      <Dots />
      <div style={{ position: 'absolute', left: 90, right: 90, top: 560, transform: `scale(${Math.min(p, 1.03)})`, opacity: p > 0.02 ? 1 : 0 }}>
        <Card style={{ padding: 56, textAlign: 'center' }}>
          <Logo size={170} />
          <div style={{ font: `800 86px ${F.head}`, letterSpacing: '-.045em', marginTop: 20 }}>Reply<span style={{ color: C.cobalt }}>Inbox</span></div>
          <div style={{ font: `700 40px ${F.mono}`, margin: '8px 0 34px' }}>@replyinbox.in</div>
          <div style={{ font: `700 36px/1.4 ${F.body}`, color: '#444', marginBottom: 36 }}>Comment → DM · Store · Courses · AI</div>
          <Btn style={{ fontSize: 52, padding: '22px 80px' }}>Follow</Btn>
        </Card>
      </div>
    </AbsoluteFill>
  );
};

const SCENES: [number, number, React.FC][] = [
  [0, 2.30, S1], [2.30, 5.30, S2], [5.30, 7.75, S3], [7.75, 10.62, S4], [10.62, 15.36, S5], [15.36, 17.95, S6], [17.95, 23.50, S7],
  [23.50, 28.10, S8], [28.10, 32.55, S9], [32.55, 33.55, S10], [33.55, 37.78, S11], [37.78, 39.05, S12],
];

export const Reel: React.FC = () => (
  <AbsoluteFill style={{ fontFamily: F.body, color: C.ink }}>
    <Dots />
    {SCENES.map(([a, b, S], i) => <Sequence key={i} from={f(a)} durationInFrames={f(b) - f(a)}><S /></Sequence>)}
    <Sequence from={f(39.05)} durationInFrames={f(TL.vo) - f(39.05)}><S13 /></Sequence>
    <Sequence from={0} durationInFrames={f(TL.vo)}><Header /><Character /></Sequence>
    <Sequence from={0} durationInFrames={f(TL.vo)}><Captions /></Sequence>
    <Sequence from={f(TL.vo)}><FollowCard /></Sequence>
    <Audio src={staticFile('mix.wav')} />
  </AbsoluteFill>
);
