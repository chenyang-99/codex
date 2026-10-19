const EASE = {
  lin: (x) => x,
  io: (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
  i: (x) => x * x * x,
  o: (x) => 1 - Math.pow(1 - x, 3),
  whip: (x) => (x < 0.5 ? 16 * Math.pow(x, 5) : 1 - Math.pow(-2 * x + 2, 5) / 2),
  so: (x) => 1 - Math.pow(1 - x, 2),
  si: (x) => x * x,
  back: (x) => 1 + 2.2 * Math.pow(x - 1, 3) + 1.2 * Math.pow(x - 1, 2),
};
export const BASE_DURATION = 10;
const BASE_KEYS=[
 {t:0,yaw:130,pitch:32,roll:-18,zoom:1.35,focus:"body",panX:0,panY:0,apart:0,press:0,glow:[0.7,0.6,0.65]},
 {t:1.3,yaw:-30,pitch:39,roll:0,zoom:1.95,ease:"io"},
 {t:2.1,yaw:-35,pitch:40,roll:0,zoom:3.3,focus:"escape",ease:"io"},
 {t:3.1,yaw:-22,pitch:30,roll:0,zoom:3.65,focus:"space",press:0,ease:"io"},
 {t:3.9,press:1,yaw:-22,pitch:30,roll:0,zoom:3.65,ease:"io"},
 {t:4.55,press:0,zoom:2.1,focus:"body",ease:"io"},
 {t:5.2,yaw:-34,pitch:42,zoom:1.8,apart:0,ease:"io"},
 {t:6.6,apart:1,yaw:-36,pitch:38,zoom:1.18,panY:-12,ease:"o"},
 {t:7.6,apart:1,yaw:-48,pitch:34,zoom:1.18,ease:"lin"},
 {t:9.0,apart:0,yaw:-28,pitch:38,zoom:1.9,panY:0,ease:"io"},
 {t:10,apart:0,yaw:-30,pitch:38,zoom:2.0,ease:"o"}
];
const BASE_LABELS=[
 {t:0,hint:"Mechanical keyboard",readout:"60% layout · 61 keys"},
 {t:1.9,hint:"Keycaps",readout:"61 independently modeled solids"},
 {t:3.0,hint:"Spacebar",readout:"press to actuate"},
 {t:4.9,hint:"Exploded layers",readout:"keycaps · switches · plate · PCB"},
 {t:8.8,hint:"Mechanical keyboard",readout:"{parts} parts · {assemblies} assemblies"}
];
const REQUESTED = typeof DATA !== "undefined" && DATA.duration ? DATA.duration : BASE_DURATION;
function retimer(keys, duration) {
  const segments = [];
  let fixed = 0;
  for (let i = 1; i < keys.length; i++) {
    const whip = keys[i].ease === "whip";
    segments.push({ a: keys[i - 1].t, b: keys[i].t, whip });
    if (whip) fixed += keys[i].t - keys[i - 1].t;
  }
  const scale = Math.max(0.35, (duration - fixed) / (BASE_DURATION - fixed));
  return (t) => {
    let out = 0;
    for (const s of segments) {
      if (t <= s.a) break;
      const part = Math.min(t, s.b) - s.a;
      out += s.whip ? part : part * scale;
    }
    return out + Math.max(0, t - BASE_DURATION) * scale;
  };
}
const RETIME = retimer(BASE_KEYS, REQUESTED);
export const DURATION = RETIME(BASE_DURATION);
export const KEYS = BASE_KEYS.map((k) => ({ ...k, t: RETIME(k.t) }));
export const LABELS = BASE_LABELS.map((l) => ({ ...l, t: RETIME(l.t) }));
const CHANNELS = ["yaw", "pitch", "roll", "zoom", "panX", "panY", "apart", ...Object.keys(FEATURE_DEFAULTS)];
const DEFAULTS = { yaw: 0, pitch: 0, roll: 0, zoom: 1, panX: 0, panY: 0, apart: 0, ...FEATURE_DEFAULTS };
function track(name) {
  const list = KEYS.filter((k) => k[name] !== void 0).map((k) => ({ t: k.t, v: k[name], ease: k.ease ?? "io" }));
  if (!list.length || list[0].t > 0) list.unshift({ t: 0, v: list.length ? list[0].v : DEFAULTS[name], ease: "lin" });
  return list;
}
const TRACKS = Object.fromEntries(CHANNELS.map((c) => [c, track(c)]));
const FOCUS = KEYS.filter((k) => k.focus !== void 0).map((k) => ({ t: k.t, v: k.focus, ease: k.ease ?? "io" }));
const GLOW = KEYS.filter((k) => k.glow !== void 0).map((k) => ({ t: k.t, v: k.glow, ease: k.ease ?? "io" }));
function sample(list, t, log = false) {
  if (t <= list[0].t) return { a: list[0].v, b: list[0].v, e: 0 };
  for (let i = 1; i < list.length; i++) {
    if (t <= list[i].t) {
      const x = (t - list[i - 1].t) / (list[i].t - list[i - 1].t || 1);
      return { a: list[i - 1].v, b: list[i].v, e: EASE[list[i].ease](x), log };
    }
  }
  const last = list[list.length - 1].v;
  return { a: last, b: last, e: 0 };
}
const mix = (a, b, e) => a + (b - a) * e;
const FRAME = typeof DATA !== "undefined" && DATA.W ? [DATA.W, DATA.H] : [540, 960];
const WIDE_FIT = Math.min(1, FRAME[0] / 540, FRAME[1] / 760);
function fitZoom(z) {
  const x = Math.max(0, Math.min(1, (z - 2.6) / 2));
  return z * Math.pow(WIDE_FIT, 1 - x * x * (3 - 2 * x));
}
export function at(t) {
  const out = {};
  for (const c of CHANNELS) {
    const { a, b, e } = sample(TRACKS[c], t);
    out[c] = c === "zoom" ? Math.exp(mix(Math.log(a), Math.log(b), e)) : mix(a, b, e);
  }
  out.zoom = fitZoom(out.zoom);
  const f = sample(FOCUS, t);
  out.focus = { a: f.a, b: f.b, e: f.e };
  const g = sample(GLOW, t);
  out.glow = g.a.map((v, i) => mix(v, g.b[i], g.e));
  let label = LABELS[0];
  for (const l of LABELS) if (t >= l.t) label = l;
  out.label = label;
  return out;
}
