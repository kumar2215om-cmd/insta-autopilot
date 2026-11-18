"""A code-drawn comic cartoon of Om (SVG), built from reusable parts so new poses are combinations, not new drawings.

    from character import svg
    svg(pose="pointing", expression="smug", outfit="black", sticker="#1FC75A", size=520)

Parts: head (face, ears, hair, beard, moustache), expression (eyes, brows, mouth, extras), torso (outfit), two arms
(shoulder → elbow → hand, in front of or behind the body, with a hand shape), and props (phone boom, laptop, chai,
pointer, confetti, sweat, thought dots, sunglasses). A pose picks arms + props + a default expression.
The whole figure gets a white sticker outline plus an outer coloured one (an SVG filter).

Add a pose: write a new entry in POSES (arms + props). Add a prop: write a function returning SVG and list it in PROPS.
"""

INK = "#141210"
SKIN, SKIN_SH = "#C08460", "#9C6444"
HAIR, HAIR_HI = "#1C1715", "#3A302B"
OUTFITS = {
    "black": dict(fill="#26262A", shade="#1A1A1D", line="#000000", collar=None),
    "blue": dict(fill="#2F6FE0", shade="#2459BC", line=INK, collar="#2459BC"),
    "white": dict(fill="#F4F2EC", shade="#D9D5CA", line=INK, collar=None),
}
W = 4  # outline width in figure units (the figure is 440 wide; at ~500px on a 1080 slide this is ~4.5px)


def _p(d, fill, stroke=INK, w=W, extra=""):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round" {extra}/>'


# ---------- head ----------

def head():
    ears = (_p("M134,190 Q112,180 114,206 Q116,232 140,228 Z", SKIN) + _p("M306,190 Q328,180 326,206 Q324,232 300,228 Z", SKIN)
            + _p("M124,200 Q128,212 134,216", "none", w=3) + _p("M316,200 Q312,212 306,216", "none", w=3))
    neck = _p("M190,268 L190,312 Q220,326 250,312 L250,268 Z", SKIN) + '<path d="M192,290 Q220,304 248,290 L248,272 L192,272 Z" fill="%s"/>' % SKIN_SH
    face = _p("M140,165 Q140,92 220,90 Q300,92 300,165 L300,214 Q300,292 220,296 Q140,292 140,214 Z", SKIN)
    cheek = '<path d="M146,200 Q150,250 176,270 L160,214 Z" fill="%s" opacity=".5"/>' % SKIN_SH
    # hair: short sides, volume swept up at the front
    hair = _p("M142,182 L142,140 Q144,104 172,88 L178,64 L198,76 L212,48 L230,68 L250,46 L262,70 L282,62 L284,86 "
              "Q300,104 298,140 L298,182 Q292,150 282,140 Q250,122 214,126 Q182,124 162,138 Q148,150 142,182 Z", HAIR)
    hair_hi = ('<path d="M200,84 Q222,72 246,76" stroke="%s" stroke-width="5" fill="none" stroke-linecap="round"/>'
               '<path d="M178,104 Q200,94 222,96" stroke="%s" stroke-width="4" fill="none" stroke-linecap="round"/>') % (HAIR_HI, HAIR_HI)
    # full, neat beard: sideburns down the jaw to a rounded chin, open around the mouth
    beard = _p("M140,178 L146,180 Q148,226 166,242 Q190,232 220,234 Q250,232 274,242 Q292,226 294,180 L300,178 "
               "Q304,252 280,284 Q254,312 220,314 Q186,312 160,284 Q136,252 140,178 Z", HAIR)
    beard_hi = '<path d="M186,292 Q220,304 254,292" stroke="%s" stroke-width="4" fill="none" stroke-linecap="round"/>' % HAIR_HI
    moustache = _p("M182,246 Q200,232 220,240 Q240,232 258,246 Q246,256 220,251 Q194,256 182,246 Z", HAIR, w=3)
    nose = _p("M222,186 Q218,212 208,222 Q216,230 232,224", "none", w=3.5)
    return ears, neck, face + cheek, hair + hair_hi, beard + beard_hi, moustache, nose


# ---------- expressions: eyes, brows, mouth (+ extras) ----------

def _eye(cx, cy, look=(0, 0), r=13, lid=0):
    out = f'<ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="{r + 2}" fill="#fff" stroke="{INK}" stroke-width="3"/>'
    out += f'<circle cx="{cx + look[0]}" cy="{cy + look[1]}" r="{r * .55:.1f}" fill="{INK}"/>'
    out += f'<circle cx="{cx + look[0] + 2}" cy="{cy + look[1] - 3}" r="2.4" fill="#fff"/>'
    if lid:   # half-closed lid for smug
        out += f'<path d="M{cx - r - 2},{cy - r - 4} L{cx + r + 2},{cy - r - 4} L{cx + r + 2},{cy - r + lid} Q{cx},{cy - r + lid + 4} {cx - r - 2},{cy - r + lid} Z" fill="{SKIN}" stroke="{INK}" stroke-width="3"/>'
    return out


def _brow(x1, y1, x2, y2, bend=-6):
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + bend
    return f'<path d="M{x1},{y1} Q{mx},{my} {x2},{y2}" stroke="{HAIR}" stroke-width="9" fill="none" stroke-linecap="round"/>'


def _mouth(d, inside=True):
    fill = "#5B1F1A" if inside else "none"
    out = _p(d, fill, w=3.5)
    return out


SUNGLASSES = ('<g><path d="M154,170 L286,170" stroke="%s" stroke-width="6"/>'
              '<path d="M158,168 Q156,200 184,202 Q208,202 212,170 Z" fill="%s" stroke="%s" stroke-width="4"/>'
              '<path d="M228,170 Q232,202 256,202 Q284,200 282,168 Z" fill="%s" stroke="%s" stroke-width="4"/>'
              '<path d="M168,176 L180,176" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity=".7"/>'
              '<path d="M238,176 L250,176" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity=".7"/></g>') % (INK, INK, INK, INK, INK)


def expression(name):
    L, R, Y = 188, 252, 184
    if name == "happy":
        eyes = _eye(L, Y, (0, 1)) + _eye(R, Y, (0, 1))
        brows = _brow(170, 158, 204, 154) + _brow(236, 154, 270, 158)
        mouth = _mouth("M190,256 Q220,250 250,256 Q246,284 220,286 Q194,284 190,256 Z") + _p("M200,276 Q220,268 240,276 Q232,284 220,284 Q208,284 200,276 Z", "#D9645A", w=0)
    elif name == "smug":
        eyes = _eye(L, Y, (4, 2), lid=11) + _eye(R, Y, (4, 2), lid=11)
        brows = _brow(170, 162, 204, 162, bend=-2) + _brow(236, 152, 272, 148, bend=-8)
        mouth = _mouth("M196,262 Q226,268 250,252", inside=False)
    elif name == "worried":
        eyes = _eye(L, Y + 2, (0, 3), r=12) + _eye(R, Y + 2, (0, 3), r=12)
        brows = _brow(168, 162, 206, 150, bend=4) + _brow(234, 150, 272, 162, bend=4)
        mouth = _mouth("M196,266 Q206,258 214,266 Q222,274 230,266 Q238,258 246,266", inside=False)
    elif name == "thinking":
        eyes = _eye(L, Y, (5, -5)) + _eye(R, Y, (5, -5))
        brows = _brow(170, 160, 204, 160, bend=-2) + _brow(236, 150, 272, 152, bend=-10)
        mouth = _mouth("M204,264 Q224,262 240,258", inside=False)
    elif name == "shocked":
        eyes = _eye(L, Y, (0, 0), r=16) + _eye(R, Y, (0, 0), r=16)
        brows = _brow(168, 148, 206, 144, bend=-8) + _brow(234, 144, 272, 148, bend=-8)
        mouth = _mouth("M206,258 Q220,250 234,258 Q238,282 220,286 Q202,282 206,258 Z")
    elif name == "cool":
        eyes = SUNGLASSES
        brows = _brow(170, 156, 204, 154) + _brow(236, 152, 272, 150, bend=-8)
        mouth = _mouth("M194,256 Q222,262 250,250 Q244,278 220,280 Q200,278 194,256 Z") + _p("M200,258 Q222,262 246,254 L244,262 Q222,268 202,264 Z", "#fff", w=0)
    else:
        raise ValueError(f"Unknown expression {name!r}; use one of {EXPRESSIONS}")
    return eyes, brows, mouth


EXPRESSIONS = ("happy", "smug", "worried", "thinking", "shocked", "cool")


# ---------- torso + arms ----------

def torso(outfit):
    o = OUTFITS[outfit]
    body = _p("M86,520 L86,402 Q86,334 150,318 L192,308 Q220,330 248,308 L290,318 Q354,334 354,402 L354,520 Z", o["fill"], o["line"])
    fold = f'<path d="M150,380 Q160,450 152,520" stroke="{o["shade"]}" stroke-width="10" fill="none"/><path d="M296,380 Q284,450 292,520" stroke="{o["shade"]}" stroke-width="10" fill="none"/>'
    if o["collar"]:   # shirt collar + buttons
        collar = (_p("M192,306 L220,346 L204,356 L178,318 Z", o["fill"], o["line"], 3.5) + _p("M248,306 L220,346 L236,356 L262,318 Z", o["fill"], o["line"], 3.5)
                  + "".join(f'<circle cx="220" cy="{y}" r="4" fill="#fff" stroke="{INK}" stroke-width="2"/>' for y in (380, 420, 460)))
    else:             # crew neck
        collar = _p("M192,308 Q220,334 248,308", "none", o["line"], 7) + f'<path d="M194,310 Q220,330 246,310" stroke="{o["shade"]}" stroke-width="3" fill="none"/>'
    return body + fold + collar


def _hand(x, y, kind, angle=0):
    if kind == "point":
        return (f'<g transform="rotate({angle} {x} {y})">' + _p(f"M{x},{y - 8} L{x + 44},{y - 8} Q{x + 52},{y - 2} {x + 44},{y + 4} L{x},{y + 4} Z", SKIN, w=3.5)
                + f'<circle cx="{x}" cy="{y + 4}" r="20" fill="{SKIN}" stroke="{INK}" stroke-width="{W}"/></g>')
    if kind == "fist":
        return f'<circle cx="{x}" cy="{y}" r="22" fill="{SKIN}" stroke="{INK}" stroke-width="{W}"/>' + _p(f"M{x - 12},{y - 6} Q{x},{y - 12} {x + 12},{y - 6}", "none", w=3)
    if kind == "open":
        fingers = "".join(_p(f"M{x + dx},{y - 10} L{x + dx * 1.5},{y - 34}", "none", w=11) + _p(f"M{x + dx},{y - 10} L{x + dx * 1.5},{y - 34}", "none", SKIN, 6)
                          for dx in (-12, -4, 4, 12))
        return f'<g transform="rotate({angle} {x} {y})">{fingers}<circle cx="{x}" cy="{y}" r="20" fill="{SKIN}" stroke="{INK}" stroke-width="{W}"/></g>'
    return ""   # hidden (behind head, behind an object)


def arm(outfit, pts, hand="fist", angle=0, sleeve=0.55):
    """pts: shoulder, elbow, hand (x, y). Upper arm partly in the sleeve; forearm skin."""
    o = OUTFITS[outfit]
    (sx, sy), (ex, ey), (hx, hy) = pts
    mx, my = sx + (ex - sx) * sleeve, sy + (ey - sy) * sleeve
    line = f"M{sx},{sy} L{ex},{ey} L{hx},{hy}"
    out = f'<path d="{line}" stroke="{INK}" stroke-width="{38 + 2 * W}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
    out += f'<path d="{line}" stroke="{SKIN}" stroke-width="38" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
    out += f'<path d="M{sx},{sy} L{mx:.0f},{my:.0f}" stroke="{o["line"] if o["line"] != "#000000" else INK}" stroke-width="{52 + 2 * W}" fill="none" stroke-linecap="butt"/>'
    out += f'<path d="M{sx},{sy} L{mx:.0f},{my:.0f}" stroke="{o["fill"]}" stroke-width="52" fill="none" stroke-linecap="butt"/>'
    return out + _hand(hx, hy, hand, angle)


# ---------- props ----------

def boom(x=360, y=190):
    pts = []
    import math
    for k in range(16):
        r = 70 if k % 2 == 0 else 40
        a = math.pi * 2 * k / 16
        pts.append(f"{x + r * math.cos(a):.0f},{y + r * math.sin(a):.0f}")
    return (f'<polygon points="{" ".join(pts)}" fill="#FFD21F" stroke="{INK}" stroke-width="{W}" stroke-linejoin="round"/>'
            + f'<circle cx="{x}" cy="{y}" r="28" fill="#FF7A1F" stroke="{INK}" stroke-width="3"/>'
            + _p(f"M{x - 22},{y + 40} L{x - 34},{y + 80} L{x + 6},{y + 70} Z", "#2B2B30")   # phone flying apart
            + f'<rect x="{x - 30}" y="{y - 22}" width="34" height="56" rx="7" fill="#2B2B30" stroke="{INK}" stroke-width="{W}" transform="rotate(-20 {x} {y})"/>')


def laptop(x=220, y=440):
    return (_p(f"M{x - 150},{y - 120} L{x + 110},{y - 120} L{x + 130},{y + 20} L{x - 130},{y + 20} Z", "#C9CDD6")
            + f'<circle cx="{x - 10}" cy="{y - 50}" r="14" fill="#fff" stroke="{INK}" stroke-width="3"/>'
            + _p(f"M{x - 180},{y + 20} L{x + 180},{y + 20} L{x + 166},{y + 50} L{x - 166},{y + 50} Z", "#A9AEB9"))


def chai(x=96, y=330):
    return (f'<path d="M{x - 6},{y - 70} q10,-14 0,-28 M{x + 12},{y - 66} q10,-14 0,-28" stroke="#9A9A9A" stroke-width="5" fill="none" stroke-linecap="round"/>'
            + _p(f"M{x - 28},{y - 50} L{x + 28},{y - 50} L{x + 22},{y + 8} L{x - 22},{y + 8} Z", "#E9F3F5")
            + f'<path d="M{x - 25},{y - 30} L{x + 25},{y - 30} L{x + 22},{y + 5} L{x - 22},{y + 5} Z" fill="#B5652A"/>'
            + _p(f"M{x - 28},{y - 50} L{x + 28},{y - 50} L{x + 22},{y + 8} L{x - 22},{y + 8} Z", "none"))


def pointer(x1=318, y1=318, x2=430, y2=150):
    return (f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{INK}" stroke-width="14" stroke-linecap="round"/>'
            f'<path d="M{x1},{y1} L{x2},{y2}" stroke="#B5652A" stroke-width="7" stroke-linecap="round"/>'
            f'<circle cx="{x2}" cy="{y2}" r="9" fill="#FF3B3B" stroke="{INK}" stroke-width="3"/>')


def confetti():
    bits = [(60, 70, "#FFD21F", 20), (390, 60, "#1FC75A", -30), (40, 200, "#FF5DA2", 40), (410, 230, "#2F6FE0", 10),
            (110, 30, "#2F6FE0", -15), (340, 20, "#FF5DA2", 25), (20, 300, "#1FC75A", 60), (420, 330, "#FFD21F", -45)]
    return "".join(f'<rect x="{x}" y="{y}" width="22" height="12" rx="3" fill="{c}" stroke="{INK}" stroke-width="3" transform="rotate({a} {x} {y})"/>' for x, y, c, a in bits)


def sweat():
    return "".join(_p(f"M{x},{y} Q{x - 9},{y + 18} {x},{y + 24} Q{x + 9},{y + 18} {x},{y} Z", "#7FD3FF", w=3)
                   for x, y in ((124, 120), (312, 112), (330, 150)))


def thought():
    return "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" stroke="{INK}" stroke-width="3"/>' for x, y, r in ((318, 110, 8), (342, 82, 12), (374, 50, 17)))


PROPS = {"boom": boom, "laptop": laptop, "chai": chai, "pointer": pointer, "confetti": confetti, "sweat": sweat, "thought": thought}

# ---------- poses: arms (behind/front) + props + default expression ----------
# Shoulders sit at about (130, 350) and (310, 350).

POSES = {
    "stressed": dict(expression="worried", props_back=["boom"], props_front=["sweat"],
                     arms=[dict(pts=[(124, 350), (96, 250), (150, 140)], hand="open", angle=-30, front=False),
                           dict(pts=[(316, 350), (360, 300), (350, 220)], hand="fist", front=True)]),
    "pointing": dict(expression="smug", props_front=["laptop"],
                     arms=[dict(pts=[(126, 352), (110, 420), (160, 380)], hand="fist", front=True),
                           dict(pts=[(314, 352), (366, 330), (398, 300)], hand="point", angle=-35, front=True)]),
    "chilling": dict(expression="cool", props_front=["chai"],
                     arms=[dict(pts=[(126, 352), (76, 370), (96, 300)], hand="fist", front=True),
                           dict(pts=[(316, 348), (376, 230), (300, 150)], hand="hidden", front=False)]),
    "thinking": dict(expression="thinking", props_back=["thought"],
                     arms=[dict(pts=[(126, 352), (170, 450), (270, 430)], hand="fist", front=True, sleeve=.4),
                           dict(pts=[(314, 352), (290, 440), (238, 300)], hand="fist", front=True)]),
    "celebrating": dict(expression="happy", props_back=["confetti"],
                        arms=[dict(pts=[(124, 348), (70, 250), (80, 140)], hand="open", angle=-10, front=False),
                              dict(pts=[(316, 348), (370, 250), (360, 140)], hand="open", angle=10, front=False)]),
    "presenting": dict(expression="happy", props_back=["pointer"],
                       arms=[dict(pts=[(126, 352), (100, 430), (150, 470)], hand="fist", front=True),
                             dict(pts=[(314, 352), (340, 400), (318, 318)], hand="fist", front=True)]),
}


def svg(pose="presenting", expression_name=None, outfit="black", sticker="#1FC75A", size=None, uid="om", head_only=False):
    """The figure as an <svg> string (viewBox 440x520, cropped at the waist). size = width in px (height = size*520/440)."""
    if pose not in POSES:
        raise ValueError(f"Unknown pose {pose!r}; use one of {tuple(POSES)}")
    p = POSES[pose]
    ex = expression_name or p["expression"]
    ears, neck, face, hair, beard, moustache, nose = head()
    eyes, brows, mouth = expression(ex)
    back = "".join(PROPS[k]() for k in p.get("props_back", []))
    arms_back = "".join(arm(outfit, a["pts"], a.get("hand", "fist"), a.get("angle", 0), a.get("sleeve", .55)) for a in p["arms"] if not a["front"])
    arms_front = "".join(arm(outfit, a["pts"], a.get("hand", "fist"), a.get("angle", 0), a.get("sleeve", .55)) for a in p["arms"] if a["front"])
    front = "".join(PROPS[k]() for k in p.get("props_front", []))
    body = back + arms_back + neck + torso(outfit) + ears + face + beard + moustache + mouth + nose + eyes + brows + hair + arms_front + front
    w = f' width="{size}" height="{round(size * 540 / 480)}"' if size else ""
    flt = (f'<filter id="{uid}-st" x="-15%" y="-15%" width="130%" height="130%">'
           f'<feMorphology in="SourceAlpha" operator="dilate" radius="17" result="o2"/><feFlood flood-color="{sticker}"/><feComposite in2="o2" operator="in" result="c"/>'
           f'<feMorphology in="SourceAlpha" operator="dilate" radius="9" result="o1"/><feFlood flood-color="#fff"/><feComposite in2="o1" operator="in" result="w"/>'
           f'<feMerge><feMergeNode in="c"/><feMergeNode in="w"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    box = "90 20 260 320" if head_only else "-20 0 480 540"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}"{w}><defs>{flt}</defs>'
            f'<g filter="url(#{uid}-st)">{body}</g></svg>')


def bubble_html(text, tail="left"):
    """Speech bubble: white, thick black border, hard shadow, bold italic condensed caps; tail points to the character."""
    side = "left:60px" if tail == "left" else "right:60px"
    return (f'<div style="position:relative;display:inline-block;background:#fff;border:6px solid #111;border-radius:30px;'
            f'box-shadow:10px 10px 0 #111;padding:22px 30px;font:italic 400 52px/1.02 Anton,\'Bebas Neue\',Impact,sans-serif;'
            f'text-transform:uppercase;letter-spacing:.01em;color:#111;max-width:460px">{text}'
            f'<span style="position:absolute;bottom:-34px;{side};width:0;height:0;border-left:22px solid transparent;'
            f'border-right:22px solid transparent;border-top:34px solid #111"></span>'
            f'<span style="position:absolute;bottom:-22px;{side.replace("60", "66")};width:0;height:0;border-left:16px solid transparent;'
            f'border-right:16px solid transparent;border-top:24px solid #fff"></span></div>')
