import React from 'react';
import { AbsoluteFill, Audio, Img, Sequence, interpolate, staticFile, useCurrentFrame } from 'remotion';
import TL from './timeline.json';
import { C, F } from './brand';
import { FPS, f, useT, pop, ease, Dots, Card, Pill, Logo, ClaudeMark, Drop, Stamp, Cursor, Typed, Window, Btn } from './kit';

export const TOTAL = Math.round(TL.end * FPS);

// ---------- shared pieces ----------
const IGLogo: React.FC<{ size: number }> = ({ size }) => (
  <div style={{ width: size, height: size, borderRadius: size * 0.27, border: `5px solid ${C.ink}`, boxShadow: `8px 8px 0 ${C.ink}`, background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
    <svg width={size * 0.62} height={size * 0.62} viewBox="0 0 24 24" fill="none" stroke={C.ink} strokeWidth="2.2"><rect x="3" y="3" width="18" height="18" rx="5" /><circle cx="12" cy="12" r="4" /><circle cx="17.5" cy="6.5" r="1.2" fill={C.ink} /></svg>
  </div>
);
const ClaudeTile: React.FC<{ size: number }> = ({ size }) => (
  <div style={{ width: size, height: size, borderRadius: size * 0.27, border: `5px solid ${C.ink}`, boxShadow: `8px 8px 0 ${C.ink}`, background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
    <ClaudeMark size={size * 0.66} /></div>
);

// Instagram ⟷ Claude link line; `progress` 0..1 fills the dotted line, `live` lights it up cobalt with the ReplyInbox tile in the middle
const Link: React.FC<{ progress: number; live?: number }> = ({ progress, live = 0 }) => (
  <div style={{ position: 'relative', width: 760, height: 170, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
    <IGLogo size={150} />
    <div style={{ position: 'absolute', left: 165, width: 430 * progress, height: 10, top: 80, borderTop: `10px dotted ${live > 0.5 ? C.cobalt : C.ink}`, opacity: 0.85 }} />
    {live > 0 && <div style={{ position: 'absolute', left: 380 - 50, top: 35, transform: `scale(${Math.min(live, 1.05)})` }}><Logo size={100} /></div>}
    <ClaudeTile size={150} />
  </div>
);

const Shot: React.FC<{ src: string; crop: [number, number, number, number]; width: number; zoomFrom?: number; zoomTo?: number; dur?: number }> = ({ src, crop, width, zoomFrom = 1, zoomTo = 1.06, dur = 3 }) => {
  const t = useT();
  const [x, y, w, h] = crop;
  const k = width / w;
  const z = zoomFrom + (zoomTo - zoomFrom) * ease(t, 0, dur);
  return (
    <div style={{ width, height: h * k, overflow: 'hidden', position: 'relative', borderRadius: 14 }}>
      <Img src={staticFile(`shots/${src}`)} style={{ position: 'absolute', width: 1280 * k * (src.startsWith('wizard') ? 560 / 1280 : 1), left: -x * k, top: -y * k,
        transform: `scale(${z})`, transformOrigin: '50% 40%' }} />
    </div>
  );
};

const Stage: React.FC<{ children: React.ReactNode; top?: number; h?: number }> = ({ children, top = 360, h = 790 }) => (
  <div style={{ position: 'absolute', left: 60, right: 60, top, height: h, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>{children}</div>
);

const Tick: React.FC<{ at: number; children: React.ReactNode }> = ({ at, children }) => (
  <Drop at={at} from={-40}><div style={{ display: 'inline-flex', alignItems: 'center', gap: 16, background: '#fff', border: `4px solid ${C.ink}`, borderRadius: 999, boxShadow: `6px 6px 0 ${C.ink}`,
    padding: '10px 28px 10px 14px', font: `800 40px ${F.body}`, margin: '8px 0' }}>
    <span style={{ width: 48, height: 48, borderRadius: '50%', background: C.win, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', font: `800 30px ${F.body}`, border: `3px solid ${C.ink}` }}>✓</span>{children}</div></Drop>
);

const Big: React.FC<{ children: React.ReactNode; size?: number; color?: string }> = ({ children, size = 120, color = C.ink }) => (
  <div style={{ font: `800 ${size}px/0.98 ${F.head}`, letterSpacing: '-.05em', color, textAlign: 'center' }}>{children}</div>
);
const HL: React.FC<{ children: React.ReactNode; bg?: string }> = ({ children, bg = C.volt }) => (
  <span style={{ background: bg, padding: '0 14px', border: `5px solid ${C.ink}`, borderRadius: 16, boxShadow: `7px 7px 0 ${C.ink}`, display: 'inline-block', transform: 'rotate(-1.5deg)' }}>{children}</span>
);

// ---------- persistent layers ----------
const Header: React.FC = () => (
  <div style={{ position: 'absolute', top: 262, left: 50, right: 50, display: 'flex', justifyContent: 'space-between', zIndex: 30 }}>
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 12, background: C.ink, color: '#fff', borderRadius: 999, padding: '12px 26px', font: `700 28px ${F.mono}`, letterSpacing: '.05em' }}>
      <span style={{ width: 18, height: 18, borderRadius: '50%', background: C.volt }} />@REPLYINBOX.IN</span>
    <span style={{ background: C.ink, color: '#fff', borderRadius: 999, padding: '12px 26px', font: `700 28px ${F.mono}`, letterSpacing: '.05em' }}>CLAUDE × INSTA</span>
  </div>
);

const Captions: React.FC = () => {
  const t = useT();
  const ph = TL.phrases.find(p => t >= p.s - 0.05 && t < p.e + 0.18);
  if (!ph) return null;
  const k = ph.words.filter(w => t >= w.s).length - 1;
  return (
    <div style={{ position: 'absolute', left: 60, right: 60, top: 1190, display: 'flex', justifyContent: 'center', zIndex: 40 }}>
      <div style={{ background: C.ink, borderRadius: 26, padding: '16px 30px', maxWidth: 960, textAlign: 'center', font: `800 54px/1.18 ${F.head}`, letterSpacing: '-.02em', boxShadow: `8px 8px 0 ${C.cobalt}` }}>
        {ph.words.map((w, i) => (
          <span key={i} style={{ color: i <= k ? (w.key ? C.volt : '#fff') : 'rgba(255,255,255,.35)', marginRight: 20, display: 'inline-block', transform: i === k ? 'scale(1.08)' : 'none' }}>{w.w}</span>
        ))}
      </div>
    </div>
  );
};

type Ch = { at: number; until: number; pose: string; side: 'l' | 'r'; h?: number };
const CHARS: Ch[] = [
  { at: 0, until: 3.0, pose: 'portrait-pointing-at-the-viewer', side: 'r' },
  { at: 3.0, until: 7.7, pose: 'portrait-reading-the-phone', side: 'l' },
  { at: 7.7, until: 10.7, pose: 'scratching-head-sheepish-smile', side: 'r' },
  { at: 10.7, until: 12.5, pose: 'portrait-stop-gesture', side: 'l' },
  { at: 12.5, until: 13.6, pose: 'arms-crossed-big-smile', side: 'r' },
  { at: 13.6, until: 16.75, pose: 'looking-at-the-phone-smiling', side: 'l', h: 560 },
  { at: 16.75, until: 21.15, pose: 'on-a-beanbag-with-a-laptop', side: 'r', h: 560 },
  { at: 21.15, until: 24.5, pose: 'hand-on-chin-arm-crossed-smirk', side: 'l', h: 560 },
  { at: 24.5, until: 26.55, pose: 'presenting-with-one-hand-other-in-pocket', side: 'r', h: 560 },
  { at: 26.55, until: 28.7, pose: 'holding-a-laptop-typing', side: 'l', h: 560 },
  { at: 28.7, until: 30.55, pose: 'portrait-thumbs-up', side: 'r' },
  { at: 30.55, until: 31.8, pose: 'portrait-peace-sign-wink', side: 'l' },
  { at: 31.8, until: 34.76, pose: 'jumping-fists-up', side: 'r' },
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

// ---------- scenes (each runs in its own Sequence; times inside are relative) ----------
const S1: React.FC = () => {  // 0–7.7: hook + 3 ticks
  const t = useT();
  return (
    <Stage top={340} h={830}>
      <div style={{ transform: `scale(${t > 2.9 ? 0.72 : 1})`, transition: 'none', marginBottom: t > 2.9 ? -40 : 0 }}><Link progress={ease(t, 0.2, 1.6)} /></div>
      <div style={{ height: 30 }} />
      <Drop at={0.1}><Big size={t > 2.9 ? 84 : 100}>Claude ko <HL>Instagram</HL> se connect karo</Big></Drop>
      <div style={{ marginTop: 30, opacity: t > 1.9 ? 1 : 0 }}><Stamp at={1.9} rot={-2}><Pill bg={C.coral} color="#fff" style={{ fontSize: 34 }}>kuch hi minute mein</Pill></Stamp></div>
      <div style={{ marginTop: 26, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        {t > 3.03 && <Tick at={3.03}>kya post karna hai</Tick>}
        {t > 5.22 && <Tick at={5.22}>kaunsi reel chal rahi</Tick>}
        {t > 6.46 && <Tick at={6.46}>DMs sambhale</Tick>}
      </div>
    </Stage>
  );
};

const S2: React.FC = () => {  // 7.7–10.7: Instagram isn't in Connectors
  const t = useT();
  const none = t > 1.72;
  return (
    <Stage>
      <Window url="claude.ai · Connectors" style={{ width: 920 }}>
        <div style={{ border: `4px solid ${C.ink}`, borderRadius: 16, padding: '14px 20px', font: `700 36px ${F.body}`, marginBottom: 22, display: 'flex', gap: 14 }}>🔍 <Typed text="Instagram" from={0.9} to={1.6} /></div>
        {!none ? ['Google Drive', 'Gmail', 'Notion', 'Slack'].map(x => (
          <div key={x} style={{ padding: '14px 18px', marginBottom: 10, border: `3px solid ${C.mist}`, borderRadius: 14, font: `700 32px ${F.body}`, color: '#555' }}>{x} <span style={{ float: 'right', color: C.cobalt }}>+</span></div>
        )) : <Stamp at={1.72} rot={0}><div style={{ textAlign: 'center', padding: '60px 0' }}>
          <div style={{ font: `800 56px ${F.head}`, color: C.loss }}>No results for "Instagram"</div>
          <div style={{ font: `700 30px ${F.mono}`, color: '#777', marginTop: 10 }}>not in the list</div></div></Stamp>}
      </Window>
    </Stage>
  );
};

const S3: React.FC = () => (  // 10.7–12.5
  <Stage>
    <Drop at={0.05}><div style={{ fontSize: 120, textAlign: 'center' }}>✋</div></Drop>
    <Drop at={0.15}><Big size={120}>Zyadatar log</Big></Drop>
    <Stamp at={0.75} rot={-3}><Big size={120} color={C.coral}>yahin ruk jaate hain.</Big></Stamp>
  </Stage>
);

const S4: React.FC = () => (  // 12.5–13.6
  <Stage>
    <Drop at={0.0}><div style={{ font: `700 40px ${F.mono}`, letterSpacing: '.2em', textAlign: 'center', color: '#555' }}>ASLI</div></Drop>
    <Stamp at={0.1} rot={-2}><Big size={170}><HL>MOVE</HL></Big></Stamp>
    <Drop at={0.35}><div style={{ marginTop: 26, width: 220, height: 14, background: C.cobalt, borderRadius: 8, border: `3px solid ${C.ink}` }} /></Drop>
  </Stage>
);

const S5: React.FC = () => {  // 13.6–16.75: ReplyInbox login → Settings → Create Claude link
  const t = useT();
  const settings = t > 1.75;
  return (
    <Stage>
      <Drop at={0}><Pill style={{ marginBottom: 26 }}>Step 1 · ReplyInbox</Pill></Drop>
      {!settings ? (
        <Window url="replyinbox.in" style={{ width: 900 }}>
          <div style={{ textAlign: 'center', padding: '24px 0' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 22 }}><Logo size={86} /><span style={{ font: `800 62px ${F.head}`, letterSpacing: '-.04em' }}>Reply<span style={{ color: C.cobalt }}>Inbox</span></span></div>
            <div style={{ height: 36 }} />
            <Btn active={t > 1.15 && t < 1.45}>📸 Continue with Instagram</Btn>
          </div>
        </Window>
      ) : (
        <Window url="replyinbox.in/app/settings" style={{ width: 900 }}>
          <div style={{ font: `800 46px ${F.head}`, display: 'flex', alignItems: 'center', gap: 14 }}><ClaudeMark size={48} /> Connect Claude</div>
          <div style={{ font: `600 28px/1.35 ${F.body}`, color: '#555', margin: '12px 0 24px' }}>Full access or read-only. Every change is logged.</div>
          <Btn active={t > 2.45 && t < 2.75} style={{ fontSize: 38 }}>Create Claude link</Btn>
          {t > 2.75 && <Drop at={2.75}><div style={{ marginTop: 22, display: 'flex', gap: 12, alignItems: 'center' }}>
            <span style={{ flex: 1, background: C.mist, border: `3px solid ${C.ink}`, borderRadius: 14, padding: '10px 16px', font: `700 26px ${F.mono}` }}>replyinbox.in/mcp/••••••</span>
            <Pill bg={C.win} color="#fff" style={{ fontSize: 24 }}>Copied ✓</Pill></div></Drop>}
        </Window>
      )}
      <Cursor path={[[0, 860, 1000], [1.0, 520, 640], [1.15, 515, 645], [2.2, 330, 690], [2.45, 320, 695]]} clickAt={[1.15, 2.45]} />
    </Stage>
  );
};

const S6: React.FC = () => {  // 16.75–21.15: Claude custom connector, then connected
  const t = useT();
  const fr = useCurrentFrame();
  const done = t > 3.85;
  return (
    <Stage>
      <Drop at={0}><Pill style={{ marginBottom: 26 }}>Step 2 · Claude</Pill></Drop>
      {!done ? (
        <Card style={{ width: 900, padding: 38 }}>
          <div style={{ font: `800 48px ${F.head}`, letterSpacing: '-.03em', marginBottom: 22 }}>Add custom connector</div>
          <div style={{ font: `700 26px ${F.mono}`, color: '#555', marginBottom: 8 }}>NAME</div>
          <div style={{ border: `4px solid ${C.ink}`, borderRadius: 16, padding: '14px 20px', font: `800 40px ${F.body}`, minHeight: 78 }}><Typed text="ReplyInbox" from={1.72} to={2.4} /></div>
          <div style={{ font: `700 26px ${F.mono}`, color: '#555', margin: '22px 0 8px' }}>REMOTE MCP SERVER URL</div>
          <div style={{ border: `4px solid ${C.ink}`, borderRadius: 16, padding: '14px 20px', font: `700 32px ${F.mono}`, minHeight: 74 }}>{t > 2.62 ? <Stamp at={2.62} rot={0}>https://replyinbox.in/mcp/••••</Stamp> : null}</div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 28 }}><Btn active={t > 3.4 && t < 3.75} style={{ fontSize: 34 }}>Add</Btn></div>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 36 }}>
          <Link progress={1} live={pop(fr, 3.9)} />
          <Stamp at={4.0} rot={-3}><Pill bg={C.win} color="#fff" style={{ fontSize: 44, padding: '14px 36px' }}>✓ Connected</Pill></Stamp>
        </div>
      )}
      {!done && <Cursor path={[[0, 880, 1000], [1.5, 420, 560], [2.4, 420, 560], [2.55, 420, 740], [3.2, 760, 900], [3.4, 750, 905]]} clickAt={[1.6, 2.6, 3.42]} />}
    </Stage>
  );
};

const ShotScene: React.FC<{ label: string; src: string; crop: [number, number, number, number]; width?: number; tag?: string; dur?: number }> = ({ label, src, crop, width = 920, tag = 'REAL SCREEN · DEMO DATA', dur = 3 }) => (
  <Stage>
    <Drop at={0}><Pill style={{ marginBottom: 22 }}>{label}</Pill></Drop>
    <Drop at={0.08}><Card style={{ padding: 14, overflow: 'hidden' }}><Shot src={src} crop={crop} width={width - 28} dur={dur} /></Card></Drop>
    <div style={{ marginTop: 18 }}><Pill bg={C.mist} style={{ fontSize: 22 }}>{tag}</Pill></div>
  </Stage>
);

const S7: React.FC = () => <ShotScene label="Top reels breakdown" src="reel-report.jpg" crop={[270, 60, 1000, 640]} dur={2} />;        // 21.15–23.1
const S8: React.FC = () => <ShotScene label="Followers + sales per reel" src="sales.jpg" crop={[270, 90, 1000, 640]} dur={1.4} />;   // 23.1–24.5

const S9: React.FC = () => {  // 24.5–25.2: week content plan
  const fr = useCurrentFrame();
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  return (
    <Stage>
      <Card style={{ width: 920, padding: 30 }}>
        <div style={{ font: `800 46px ${F.head}`, marginBottom: 18 }}>Content plan · this week</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7,1fr)', gap: 10 }}>
          {days.map((d, i) => { const p = pop(fr, 0.03 + i * 0.07); return (
            <div key={d} style={{ textAlign: 'center' }}><div style={{ font: `700 22px ${F.mono}` }}>{d}</div>
              <div style={{ height: 200, marginTop: 6, border: `4px solid ${C.ink}`, borderRadius: 14, background: i % 2 ? '#E9EBFF' : '#F4FFD6', transform: `scale(${Math.min(p, 1.05)})`, opacity: p > 0.02 ? 1 : 0 }} /></div>); })}
        </div>
      </Card>
    </Stage>
  );
};

const S10: React.FC = () => <ShotScene label="Comment-to-DM for every reel" src="wizard-keyword.jpg" crop={[0, 150, 560, 520]} width={760} dur={1.3} />;  // 25.2–26.55
const S11: React.FC = () => <ShotScene label="DM replies, drafted" src="ai-inbox.jpg" crop={[270, 180, 1000, 620]} dur={2} />;                         // 26.55–28.7

const S12: React.FC = () => {  // 28.7–30.55: one yes
  const t = useT();
  return (
    <Stage>
      <Window url="claude.ai · ReplyInbox" style={{ width: 920 }}>
        <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start', font: `700 36px/1.35 ${F.body}` }}><ClaudeMark size={44} />
          <span>Plan ready: <b>7 reels</b>, comment-to-DM and <b>3 DM replies</b>. Kar doon?</span></div>
        <div style={{ display: 'flex', gap: 22, marginTop: 28 }}><Btn active={t > 0.95 && t < 1.3} bg={C.volt} color={C.ink}>Haan ✓</Btn><Btn bg="#fff" color={C.ink}>Nahi</Btn></div>
      </Window>
      <div style={{ marginTop: 26, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
        <Pill bg={C.ink} color="#fff" style={{ fontSize: 24 }}>Claude asks before every change</Pill>
        <Pill bg={C.mist} style={{ fontSize: 24 }}>Connect Claude: Pro plan · Illustration</Pill></div>
      <Cursor path={[[0, 860, 980], [0.8, 250, 500], [0.95, 245, 505]]} clickAt={[0.95]} />
    </Stage>
  );
};

const S13: React.FC = () => {  // 30.55–31.8: like this reel
  const t = useT();
  return (
    <Stage>
      <Drop at={0}><div style={{ width: 520, height: 760, border: `7px solid ${C.ink}`, borderRadius: 60, background: C.paper, boxShadow: `14px 14px 0 ${C.ink}`, position: 'relative', overflow: 'hidden', padding: 30 }}>
        <div style={{ font: `800 50px/1.05 ${F.head}`, letterSpacing: '-.04em', marginTop: 120, textAlign: 'center' }}>Claude ko <span style={{ background: C.volt }}>Insta</span> se connect karo</div>
        <div style={{ position: 'absolute', left: 24, right: 24, bottom: 30, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ background: '#fff', border: `3px solid ${C.ink}`, borderRadius: 18, padding: '10px 14px', font: `700 26px ${F.body}` }}>@riya.creates: <b>CLAUDE</b></div>
          {t > 0.45 && <Stamp at={0.45} rot={0}><div style={{ background: C.cobalt, color: '#fff', border: `3px solid ${C.ink}`, borderRadius: 18, padding: '10px 14px', font: `700 26px ${F.body}` }}>📩 DM sent: setup + prompts</div></Stamp>}
        </div></div></Drop>
    </Stage>
  );
};

const S14: React.FC = () => {  // 31.8–34.76 CTA
  const t = useT();
  return (
    <AbsoluteFill>
      <Dots color={C.cobalt} dot="rgba(255,255,255,.14)" />
      <Stage>
        <Drop at={0.05}><Big size={120} color="#fff">Comment</Big></Drop>
        <Stamp at={0.2} rot={-3}><div style={{ margin: '24px 0 36px', background: C.volt, border: `7px solid ${C.ink}`, borderRadius: 34, boxShadow: `16px 16px 0 ${C.ink}`, padding: '14px 50px', font: `700 150px ${F.mono}`, color: C.ink }}>CLAUDE</div></Stamp>
        <div style={{ opacity: ease(t, 1.0, 1.4) }}><Pill bg="#fff" style={{ fontSize: 34, padding: '12px 30px' }}>📩 DM: setup + ready prompts</Pill></div>
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
  [0, 7.7, S1], [7.7, 10.7, S2], [10.7, 12.5, S3], [12.5, 13.6, S4], [13.6, 16.75, S5], [16.75, 21.15, S6], [21.15, 23.1, S7], [23.1, 24.5, S8],
  [24.5, 25.2, S9], [25.2, 26.55, S10], [26.55, 28.7, S11], [28.7, 30.55, S12], [30.55, 31.8, S13],
];

export const Reel: React.FC = () => (
  <AbsoluteFill style={{ fontFamily: F.body, color: C.ink }}>
    <Dots />
    {SCENES.map(([a, b, S], i) => <Sequence key={i} from={f(a)} durationInFrames={f(b) - f(a)}><S /></Sequence>)}
    <Sequence from={f(31.8)} durationInFrames={f(TL.vo) - f(31.8)}><S14 /></Sequence>
    <Sequence from={0} durationInFrames={f(TL.vo)}><Header /><Character /></Sequence>
    <Sequence from={0} durationInFrames={f(TL.vo)}><Captions /></Sequence>
    <Sequence from={f(TL.vo)}><FollowCard /></Sequence>
    <Audio src={staticFile('mix.wav')} />
  </AbsoluteFill>
);
