/* Small shared helpers: seeded random numbers, maths, a binary heap. */
const U = (() => {
  const TAU = Math.PI * 2;
  function rng(seed) {
    let s = seed >>> 0 || 1;
    const f = () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
    f.range = (a, b) => a + (b - a) * f();
    f.int = (a, b) => Math.floor(a + (b - a + 1) * f());
    f.pick = arr => arr[Math.floor(f() * arr.length)];
    return f;
  }
  const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
  const lerp = (a, b, t) => a + (b - a) * t;
  const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
  const dist2 = (ax, ay, bx, by) => (ax - bx) * (ax - bx) + (ay - by) * (ay - by);
  const angNorm = a => Math.atan2(Math.sin(a), Math.cos(a));
  const angTo = (a, b) => Math.atan2(b.y - a.y, b.x - a.x);
  /* turn angle a toward b by at most step */
  function turnTo(a, b, step) { const d = angNorm(b - a); return Math.abs(d) <= step ? b : a + Math.sign(d) * step; }
  /* move a plain number toward a target by at most step (not an angle: no wrap-around) */
  function approach(a, b, step) { return Math.abs(b - a) <= step ? b : a + Math.sign(b - a) * step; }
  /* value from a [near, mid, far] profile at distance d */
  function profile(arr, rng, d) {
    if (d <= rng[0]) return arr[0];
    if (d <= rng[1]) return lerp(arr[0], arr[1], (d - rng[0]) / Math.max(1e-6, rng[1] - rng[0]));
    return lerp(arr[1], arr[2], Math.min(1, (d - rng[1]) / Math.max(1e-6, rng[2] - rng[1])));
  }
  /* segment-segment and point-segment */
  function segDist2(px, py, ax, ay, bx, by) {
    const dx = bx - ax, dy = by - ay, l = dx * dx + dy * dy;
    let t = l ? ((px - ax) * dx + (py - ay) * dy) / l : 0; t = clamp(t, 0, 1);
    return dist2(px, py, ax + dx * t, ay + dy * t);
  }
  function segX(ax, ay, bx, by, cx, cy, dx, dy) {
    const d = (bx - ax) * (dy - cy) - (by - ay) * (dx - cx);
    if (Math.abs(d) < 1e-9) return false;
    const t = ((cx - ax) * (dy - cy) - (cy - ay) * (dx - cx)) / d, u = ((cx - ax) * (by - ay) - (cy - ay) * (bx - ax)) / d;
    return t >= 0 && t <= 1 && u >= 0 && u <= 1;
  }
  class Heap {
    constructor() { this.k = []; this.v = []; }
    get size() { return this.k.length; }
    push(key, val) {
      const k = this.k, v = this.v; let i = k.length; k.push(key); v.push(val);
      while (i > 0) { const p = (i - 1) >> 1; if (k[p] <= key) break; k[i] = k[p]; v[i] = v[p]; i = p; }
      k[i] = key; v[i] = val;
    }
    pop() {
      const k = this.k, v = this.v, top = v[0], lk = k.pop(), lv = v.pop(), n = k.length;
      if (n) {
        let i = 0;
        for (;;) {
          let c = 2 * i + 1; if (c >= n) break;
          if (c + 1 < n && k[c + 1] < k[c]) c++;
          if (k[c] >= lk) break;
          k[i] = k[c]; v[i] = v[c]; i = c;
        }
        k[i] = lk; v[i] = lv;
      }
      return top;
    }
  }
  const fmtTime = s => { s = Math.max(0, Math.floor(s)); return String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0'); };
  return { TAU, rng, clamp, lerp, dist, dist2, angNorm, angTo, turnTo, approach, profile, segDist2, segX, Heap, fmtTime };
})();
if (typeof module !== 'undefined') module.exports = U;
