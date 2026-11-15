"""Pen engine: skeleton strokes -> TrueType quadratic contours.

Every glyph in Clawd Mono is drawn by one virtual pen (an axis-aligned ellipse,
slightly wider than tall).  A stroke is a G1-continuous chain of cubic Bezier
segments (its centre line) plus a width profile.  Outlines are the envelope of
the pen swept along the centre line, fitted with clamped quadratic B-splines,
which map 1:1 onto TrueType's implied-on-curve point sequences.

Point structure must be identical in every weight master, so all structural
decisions (how many control points per side) are made once on the "plan"
master and replayed for the others (see PLAN).
"""
import math
import numpy as np

# ---------------------------------------------------------------- plan cache
PLAN = {}          # key -> int (control-point count) ; filled by the plan master
PLAN_MODE = {'record': True, 'prefix': ''}
FIT_TOL = {'tol': 1.1}


def plan_key(*parts):
    return PLAN_MODE['prefix'] + '|' + '|'.join(str(p) for p in parts)


# ---------------------------------------------------------------- beziers
def cubic_eval(seg, u):
    u = np.asarray(u, float)[:, None]
    mu = 1.0 - u
    p0, p1, p2, p3 = seg
    return mu ** 3 * p0 + 3 * mu * mu * u * p1 + 3 * mu * u * u * p2 + u ** 3 * p3


def cubic_d1(seg, u):
    u = np.asarray(u, float)[:, None]
    mu = 1.0 - u
    p0, p1, p2, p3 = seg
    return 3 * mu * mu * (p1 - p0) + 6 * mu * u * (p2 - p1) + 3 * u * u * (p3 - p2)


def is_line(seg, eps=1e-6):
    p0, p1, p2, p3 = seg
    d = p3 - p0
    L = math.hypot(*d)
    if L < eps:
        return True
    n = np.array([-d[1], d[0]]) / L
    return abs(np.dot(p1 - p0, n)) < 1e-6 * max(1, L) and abs(np.dot(p2 - p0, n)) < 1e-6 * max(1, L)


def line_seg(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    return np.array([a, a + (b - a) / 3, a + 2 * (b - a) / 3, b])


def unit(v):
    L = math.hypot(v[0], v[1])
    if L < 1e-12:
        return np.array([1.0, 0.0])
    return np.asarray(v, float) / L


# ---------------------------------------------------------------- B-spline fit
def _bs_matrix(tau, n):
    """Clamped quadratic B-spline with n+1 control points, uniform interior
    knots (== TrueType implied-midpoint sequence).  tau in [0,1]."""
    m = n - 1
    tau = np.asarray(tau, float)
    N = len(tau)
    A = np.zeros((N, n + 1))
    s = np.clip(tau * m, 0, m - 1e-9)
    i = s.astype(int)
    u = s - i
    b0 = (1 - u) ** 2
    b1 = 2 * u * (1 - u)
    b2 = u * u
    rows = np.arange(N)
    first = (i == 0)
    last = (i == m - 1)
    A[rows, i] = np.where(first, b0, 0.5 * b0)
    A[rows, i + 1] = np.where(first, 0.0, 0.5 * b0) + b1 + np.where(last, 0.0, 0.5 * b2)
    A[rows, np.minimum(i + 2, n)] += np.where(last, b2, 0.5 * b2)
    return A


def _bs_eval(C, tau):
    return _bs_matrix(tau, len(C) - 1) @ C


def _bs_deriv(C, tau):
    n = len(C) - 1
    m = n - 1
    tau = np.asarray(tau, float)
    s = np.clip(tau * m, 0, m - 1e-9)
    i = np.floor(s).astype(int)
    u = (s - i)[:, None]
    Cm = np.vstack([C, C[-1:]])
    q0 = np.where((i == 0)[:, None], C[0], (Cm[i] + Cm[i + 1]) / 2)
    q1 = Cm[i + 1]
    q2 = np.where((i == m - 1)[:, None], C[n], (Cm[i + 1] + Cm[np.minimum(i + 2, n)]) / 2)
    return (2 * (1 - u) * (q1 - q0) + 2 * u * (q2 - q1)) * m


def _chord_tau(S):
    d = np.hypot(*np.diff(S, axis=0).T)
    c = np.concatenate([[0], np.cumsum(d)])
    if c[-1] < 1e-9:
        return np.linspace(0, 1, len(S))
    return c / c[-1]


def _solve(S, T0, T1, n, tau):
    S0, SN = S[0], S[-1]
    if n == 2:
        # single quadratic: control point = intersection of end tangents
        M = np.array([T0, T1]).T
        det = np.linalg.det(M)
        if abs(det) < 1e-9:
            return None
        ab = np.linalg.solve(M, SN - S0)   # S0 + a T0 = SN - b T1  ->  a T0 + b T1 = SN - S0
        a, b = ab
        chord = math.hypot(*(SN - S0))
        if a <= 0 or b <= 0 or a > 3 * chord or b > 3 * chord:
            return None
        return np.array([S0, S0 + a * T0, SN])
    A = _bs_matrix(tau, n)
    rhs = S - np.outer(A[:, 0], S0) - np.outer(A[:, n], SN) - np.outer(A[:, 1], S0) - np.outer(A[:, n - 1], SN)
    nfree = n - 3
    cols = 2 + 2 * nfree
    N = len(S)
    M = np.zeros((2 * N, cols))
    M[:N, 0] = A[:, 1] * T0[0]
    M[N:, 0] = A[:, 1] * T0[1]
    M[:N, 1] = -A[:, n - 1] * T1[0]
    M[N:, 1] = -A[:, n - 1] * T1[1]
    for j in range(nfree):
        col = A[:, 2 + j]
        M[:N, 2 + 2 * j] = col
        M[N:, 3 + 2 * j] = col
    b = np.concatenate([rhs[:, 0], rhs[:, 1]])
    MtM = M.T @ M
    try:
        x = np.linalg.solve(MtM + 1e-9 * np.eye(cols), M.T @ b)
    except np.linalg.LinAlgError:
        x, *_ = np.linalg.lstsq(M, b, rcond=None)
    a, bb = x[0], x[1]
    C = np.zeros((n + 1, 2))
    C[0] = S0
    C[n] = SN
    C[1] = S0 + a * T0
    C[n - 1] = SN - bb * T1
    for j in range(nfree):
        C[2 + j] = x[2 + 2 * j:4 + 2 * j]
    if a <= 0 or bb <= 0:
        return None
    return C


def _reparam(C, S, tau, iters=2):
    tau = tau.copy()
    for _ in range(iters):
        P = _bs_eval(C, tau)
        D = _bs_deriv(C, tau)
        num = np.einsum('ij,ij->i', P - S, D)
        den = np.einsum('ij,ij->i', D, D) + 1e-9
        tau = np.clip(tau - num / den, 0, 1)
        tau[0], tau[-1] = 0, 1
        tau = np.maximum.accumulate(tau)
    return tau


def _err(C, S, tau=None):
    n = len(C) - 1
    M = max(24, 12 * (n - 1))
    Q = _bs_eval(C, np.linspace(0, 1, M))
    A = Q[:-1]
    D = Q[1:] - A
    dd = np.einsum('ij,ij->i', D, D) + 1e-12
    W = S[:, None, :] - A[None, :, :]
    t = np.clip(np.einsum('kij,ij->ki', W, D) / dd, 0, 1)
    Pp = A[None] + t[..., None] * D[None]
    dist = np.min(np.hypot(*(Pp - S[:, None, :]).transpose(2, 0, 1)), axis=1)
    return float(np.max(dist))


def fit_side(S, T0, T1, key, tol=None):
    """Fit sample polyline S (with end tangents T0,T1, unit, direction of
    travel) -> control points array (n+1,2), first/last on-curve, rest off."""
    tol = FIT_TOL['tol'] if tol is None else tol
    S = np.asarray(S, float)
    rec = PLAN_MODE['record']
    if not rec and key in PLAN:
        n = PLAN[key]
        return _fit_n(S, T0, T1, n)
    # plan: choose n
    chord = S[-1] - S[0]
    L = math.hypot(*chord)
    if L > 1e-9:
        nrm = np.array([-chord[1], chord[0]]) / L
        dev = np.max(np.abs((S - S[0]) @ nrm))
    else:
        dev = 0
    if dev < 0.35:
        n = 1
    else:
        d = np.diff(S, axis=0)
        ang = np.unwrap(np.arctan2(d[:, 1], d[:, 0]))
        turn = float(np.sum(np.abs(np.diff(ang)))) if len(ang) > 1 else 0.0
        n0 = 2 if turn < math.radians(62) else int(math.ceil(turn / math.radians(48))) + 1
        n = None
        best = None
        for cand in range(n0, n0 + 6):
            C = _fit_n(S, T0, T1, cand, check=True)
            if C is None:
                continue
            e = _err(C, S)
            if best is None or e < best[0]:
                best = (e, cand)
            if e <= tol:
                n = cand
                break
        if n is None:
            n = best[1] if best else n0 + 1
    PLAN[key] = n
    return _fit_n(S, T0, T1, n)


def _fit_n(S, T0, T1, n, check=False):
    if n == 1:
        return np.array([S[0], S[-1]])
    if n == 2:
        C = _solve(S, T0, T1, 2, None)
        if C is None and not check:
            C = _solve_free(S, T0, T1, 2, None)
        return C
    tau = _chord_tau(S)
    C = _solve(S, T0, T1, n, tau)
    if C is None:
        if check:
            return None
        # fallback: free least squares without tangent sign constraint
        C = _solve_free(S, T0, T1, n, tau)
        return C
    for _ in range(1):
        tau = _reparam(C, S, tau, 1)
        C2 = _solve(S, T0, T1, n, tau)
        if C2 is None:
            break
        C = C2
    return C


def _solve_free(S, T0, T1, n, tau):
    if n == 2:
        # midpoint control fallback (shouldn't normally happen)
        mid = S[len(S) // 2]
        c = 2 * mid - (S[0] + S[-1]) / 2
        return np.array([S[0], c, S[-1]])
    A = _bs_matrix(tau, n)
    S0, SN = S[0], S[-1]
    rhs = S - np.outer(A[:, 0], S0) - np.outer(A[:, n], SN)
    x, *_ = np.linalg.lstsq(A[:, 1:n], rhs, rcond=None)
    C = np.zeros((n + 1, 2))
    C[0], C[n] = S0, SN
    C[1:n] = x
    return C


# ---------------------------------------------------------------- strokes
class Profile:
    """Width factor along a stroke, as a function of distance (font units)
    from the stroke start (d0) and end (d1)."""

    def __init__(self, start=None, end=None, mid=None, scale=1.0):
        self.start = start   # (factor, length)
        self.end = end
        self.mid = mid       # callable(s in 0..1) -> factor, optional
        self.scale = scale

    def __call__(self, d0, d1, s):
        f = np.full_like(d0, self.scale, dtype=float)
        if self.start:
            k, L = self.start
            t = np.clip(d0 / L, 0, 1)
            t = t * t * (3 - 2 * t)
            f *= k + (1 - k) * t
        if self.end:
            k, L = self.end
            t = np.clip(d1 / L, 0, 1)
            t = t * t * (3 - 2 * t)
            f *= k + (1 - k) * t
        if self.mid:
            f *= self.mid(s)
        return f


CONST = Profile()


def _arc_ctrl(center, r, a0, sweep, m):
    """Off-curve points approximating a circular arc from angle a0 sweeping
    by `sweep` (signed) using m quadratic pieces (circumscribed polygon)."""
    d = sweep / m
    R = r / math.cos(d / 2)
    return [center + R * np.array([math.cos(a0 + (i + 0.5) * d), math.sin(a0 + (i + 0.5) * d)]) for i in range(m)]


class Stroke:
    __slots__ = ('segs', 'closed', 'caps', 'prof', 'scale', 'merge')

    def __init__(self, segs, closed=False, caps=('round', 'round'), prof=None, scale=1.0, merge=False):
        self.segs = [np.asarray(s, float) for s in segs]
        self.closed = closed
        self.caps = caps
        self.prof = prof or CONST
        self.scale = scale
        self.merge = merge


NS_CURVE = 26
NS_MERGE = 10


def stroke_contours(st, pen, key):
    """Return list of contours; a contour is a list of (x, y, on)."""
    a, b = pen[0] * st.scale, pen[1] * st.scale
    k = a / b
    segs = []
    for s in st.segs:
        s2 = s.copy()
        s2[:, 1] *= k
        segs.append(s2)
    prof = st.prof
    varying = prof.start is not None or prof.end is not None or prof.mid is not None
    ns_curve = NS_MERGE if st.merge else NS_CURVE
    samples = []
    for s in segs:
        line = is_line(s)
        if line and not varying and not st.merge:
            u = np.array([0.0, 1.0])
        elif line:
            u = np.linspace(0, 1, 6 if not varying else 14)
        else:
            u = np.linspace(0, 1, ns_curve)
        P = cubic_eval(s, u)
        D = cubic_d1(s, u)
        for idx, uu in ((0, 1e-4), (-1, 1 - 1e-4)):
            if math.hypot(*D[idx]) < 1e-7:
                D[idx] = cubic_d1(s, [uu])[0]
        T = D / np.maximum(np.hypot(D[:, 0], D[:, 1])[:, None], 1e-12)
        samples.append((P, T))
    lens = []
    total = 0.0
    for P, T in samples:
        dd = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
        lens.append(total + dd)
        total += dd[-1]
    total = max(total, 1e-9)

    def radius(dist):
        dist = np.asarray(dist, float)
        if not varying:
            return np.full(dist.shape, a * prof.scale)
        return a * prof(dist, total - dist, dist / total)

    eps = 0.5

    def offsets(P, T, dist):
        r = radius(dist)
        if varying:
            rp = np.clip((radius(dist + eps) - radius(dist - eps)) / (2 * eps), -0.5, 0.5)
        else:
            rp = np.zeros_like(r)
        Nrm = np.stack([-T[:, 1], T[:, 0]], axis=1)
        cc = np.sqrt(1 - rp * rp)
        base = P - (r * rp)[:, None] * T
        off = (r * cc)[:, None] * Nrm
        return base + off, base - off

    def end_tangents(si, which):
        """Unit tangents (direction of travel) of L and R sides at segment
        si's start (which=0) or end (which=1)."""
        s = segs[si]
        h = 1e-3
        u2 = np.array([0.0, h]) if which == 0 else np.array([1.0 - h, 1.0])
        PP = cubic_eval(s, u2)
        DD = cubic_d1(s, u2)
        for j in range(2):
            if math.hypot(*DD[j]) < 1e-9:
                DD[j] = cubic_d1(s, [0.5])[0]
        TT = DD / np.hypot(DD[:, 0], DD[:, 1])[:, None]
        d0 = lens[si][0] if which == 0 else lens[si][-1]
        dl = math.hypot(*(PP[1] - PP[0]))
        dist = np.array([d0, d0 + dl]) if which == 0 else np.array([d0 - dl, d0])
        Lq, Rq = offsets(PP, TT, dist)
        out = []
        for Q in (Lq, Rq):
            v = Q[1] - Q[0]
            out.append(unit(v) if math.hypot(*v) > 1e-9 else unit(TT[0]))
        return out

    sides_L, sides_R = [], []
    if st.merge:
        Ps, Ts, Ds = [], [], []
        for si, ((P, T), dist) in enumerate(zip(samples, lens)):
            sl = slice(None) if si == 0 else slice(1, None)
            Ps.append(P[sl]); Ts.append(T[sl]); Ds.append(dist[sl])
        P = np.vstack(Ps); T = np.vstack(Ts); dist = np.concatenate(Ds)
        Lp, Rp = offsets(P, T, dist)
        tL0, tR0 = end_tangents(0, 0)
        tL1, tR1 = end_tangents(len(segs) - 1, 1)
        if st.closed:
            # closed merged loops: fit as two halves to keep tangent continuity
            raise ValueError('merge+closed unsupported')
        sides_L.append(fit_side(Lp, tL0, tL1, plan_key(key, 'mL')))
        sides_R.append(fit_side(Rp, tR0, tR1, plan_key(key, 'mR')))
    else:
        for si, ((P, T), dist) in enumerate(zip(samples, lens)):
            Lp, Rp = offsets(P, T, dist)
            tL0, tR0 = end_tangents(si, 0)
            tL1, tR1 = end_tangents(si, 1)
            sides_L.append(fit_side(Lp, tL0, tL1, plan_key(key, si, 'L')))
            sides_R.append(fit_side(Rp, tR0, tR1, plan_key(key, si, 'R')))

    def unT(p):
        return (p[0], p[1] / k)

    def emit_side(C_list):
        pts = []
        for ci, C in enumerate(C_list):
            if ci == 0:
                pts.append((C[0], True))
            for q in C[1:-1]:
                pts.append((q, False))
            pts.append((C[-1], True))
        return pts

    contours = []
    if st.closed:
        L = emit_side(sides_L)[:-1]
        R = emit_side(sides_R)[:-1]
        for side in (L, R):
            contours.append([(*unT(p), on) for p, on in side])
    else:
        L = emit_side(sides_L)
        R = emit_side(sides_R)
        P_end = samples[-1][0][-1]
        P_start = samples[0][0][0]
        r_end = float(radius([total])[0])
        r_start = float(radius([0.0])[0])
        cont = list(L)
        cont += _cap(st.caps[1], P_end, L[-1][0], R[-1][0], r_end, samples[-1][1][-1], end=True)
        cont += list(reversed(R))
        cont += _cap(st.caps[0], P_start, R[0][0], L[0][0], r_start, samples[0][1][0], end=False)
        contours.append([(*unT(p), on) for p, on in cont])
    return contours


def _cap(kind, center, p_from, p_to, r, tan, end, m=3):
    """Points strictly between p_from and p_to (both on-curve already emitted)
    going clockwise around `center`."""
    if kind == 'round':
        a0 = math.atan2(p_from[1] - center[1], p_from[0] - center[0])
        a1 = math.atan2(p_to[1] - center[1], p_to[0] - center[0])
        sweep = a1 - a0
        # clockwise => negative sweep
        while sweep >= 0:
            sweep -= 2 * math.pi
        while sweep < -2 * math.pi:
            sweep += 2 * math.pi
        rr = 0.5 * (math.hypot(*(p_from - center)) + math.hypot(*(p_to - center)))
        return [(q, False) for q in _arc_ctrl(center, rr, a0, sweep, m)]
    if kind == 'flat':
        return []
    if kind == 'square':
        t = unit(tan) * (1 if end else -1)
        return [(p_from + t * r, True), (p_to + t * r, True)]
    if isinstance(kind, tuple) and kind[0] == 'cut':
        # angled flat cut: direction angle (deg) of the cut line, absolute
        return []
    raise ValueError(kind)


# ---------------------------------------------------------------- shapes
def ellipse_contour(cx, cy, rx, ry):
    """Clockwise ellipse with on-curve extrema + 2 off-curve per quadrant."""
    pts = []
    c = np.array([0.0, 0.0])
    # clockwise starting at top: angles 90 -> 0 -> -90 -> -180
    for q in range(4):
        a0 = math.pi / 2 - q * math.pi / 2
        p_on = np.array([math.cos(a0), math.sin(a0)])
        pts.append((cx + rx * p_on[0], cy + ry * p_on[1], True))
        for off in _arc_ctrl(c, 1.0, a0, -math.pi / 2, 2):
            pts.append((cx + rx * off[0], cy + ry * off[1], False))
    return pts


def polygon(points):
    """Polygon -> clockwise contour of on-curve points."""
    pts = [(float(x), float(y), True) for x, y in points]
    if signed_area(pts) > 0:
        pts.reverse()
    return pts


def rounded_polygon(points, radius):
    """Polygon with circular-arc rounded corners, clockwise."""
    P = [np.array(p, float) for p in points]
    if _poly_area(P) > 0:
        P.reverse()
    n = len(P)
    out = []
    for i in range(n):
        p_prev, p, p_next = P[i - 1], P[i], P[(i + 1) % n]
        v1 = unit(p_prev - p)
        v2 = unit(p_next - p)
        ang = math.acos(max(-1, min(1, float(np.dot(v1, v2)))))
        rad = radius[i] if isinstance(radius, (list, tuple)) else radius
        if rad <= 0 or ang > math.pi - 1e-3:
            out.append((p[0], p[1], True))
            continue
        t = rad / math.tan(ang / 2)
        t = min(t, 0.5 * math.hypot(*(p_prev - p)), 0.5 * math.hypot(*(p_next - p)))
        rad_eff = t * math.tan(ang / 2)
        a = p + v1 * t
        bpt = p + v2 * t
        bis = unit(v1 + v2)
        c = p + bis * (rad_eff / math.sin(ang / 2))
        a0 = math.atan2(a[1] - c[1], a[0] - c[0])
        a1 = math.atan2(bpt[1] - c[1], bpt[0] - c[0])
        sweep = a1 - a0
        while sweep > math.pi:
            sweep -= 2 * math.pi
        while sweep < -math.pi:
            sweep += 2 * math.pi
        m = max(1, int(math.ceil(abs(sweep) / (math.pi / 4) - 1e-6)))
        out.append((a[0], a[1], True))
        for q in _arc_ctrl(c, rad_eff, a0, sweep, m):
            out.append((q[0], q[1], False))
        out.append((bpt[0], bpt[1], True))
    return out


def _poly_area(P):
    s = 0.0
    for i in range(len(P)):
        x0, y0 = P[i - 1][0], P[i - 1][1]
        x1, y1 = P[i][0], P[i][1]
        s += x0 * y1 - x1 * y0
    return s / 2


def signed_area(contour):
    """Approximate signed area (positive = counter-clockwise, y up), using the
    polygon of all points (good enough to decide orientation)."""
    return _poly_area([(p[0], p[1]) for p in contour])


def reverse_contour(c):
    # keep first point first so on-curve start is preserved
    return [c[0]] + list(reversed(c[1:]))


def transform_contour(c, m):
    """m = (a, b, c, d, e, f): x' = a x + c y + e ; y' = b x + d y + f"""
    A, B, C, D, E, F = m
    return [(A * x + C * y + E, B * x + D * y + F, on) for x, y, on in c]


# ---------------------------------------------------------------- fast path
def refine_quad(P, max_turn_deg=28.0, passes=2):
    """Knot insertion on a clamped uniform quadratic B-spline control polygon
    (TrueType style) where the control polygon turns sharply.  Inserting at
    the middle of a span replaces off-curve C_i with two points at the
    quarter positions -- the curve is unchanged."""
    P = [np.asarray(p, float) for p in P]
    for _ in range(passes):
        n = len(P) - 1
        if n < 2:
            return P
        flags = []
        for i in range(1, n):
            a, b = P[i] - P[i - 1], P[i + 1] - P[i]
            la, lb = math.hypot(*a), math.hypot(*b)
            if la < 1e-9 or lb < 1e-9:
                flags.append(False)
                continue
            c = (a[0] * b[0] + a[1] * b[1]) / (la * lb)
            flags.append(math.degrees(math.acos(max(-1, min(1, c)))) > max_turn_deg)
        if not any(flags):
            return P
        out = [P[0]]
        for i in range(1, n):
            if flags[i - 1]:
                # split the quadratic piece at its control point C_i
                a = P[i - 1] if i == 1 else (P[i - 1] + P[i]) / 2
                b = P[i + 1] if i == n - 1 else (P[i] + P[i + 1]) / 2
                out.append((a + P[i]) / 2 if i != 1 else (P[0] + P[1]) / 2)
                out.append((P[i] + b) / 2 if i != n - 1 else (P[i] + P[n]) / 2)
            else:
                out.append(P[i])
        out.append(P[n])
        P = out
    return P


def quad_stroke(P, pen, caps=('round', 'round'), cap_m=2):
    """Stroke a clamped quadratic B-spline skeleton (control points P, first
    and last on-curve) with an elliptical pen via Tiller-Hanson offsets.
    Returns one clockwise contour.  Point count depends only on len(P)."""
    a, b = pen
    k = a / b
    Q = np.array(P, float)
    Q[:, 1] *= k
    n = len(Q) - 1
    r = a
    d = np.diff(Q, axis=0)
    L = np.hypot(d[:, 0], d[:, 1])
    L = np.maximum(L, 1e-9)
    u = d / L[:, None]
    nr = np.stack([-u[:, 1], u[:, 0]], axis=1)
    off = np.zeros_like(Q)
    off[0] = nr[0]
    off[-1] = nr[-1]
    if n >= 2:
        s = nr[:-1] + nr[1:]
        den = 1 + np.einsum('ij,ij->i', nr[:-1], nr[1:])
        off[1:-1] = s / np.maximum(den, 0.35)[:, None]
    Lp = Q + r * off
    Rp = Q - r * off
    pts = [(Lp[0], True)] + [(p, False) for p in Lp[1:-1]] + [(Lp[-1], True)]
    pts += _cap(caps[1], Q[-1], Lp[-1], Rp[-1], r, u[-1], end=True, m=cap_m)
    pts += [(Rp[-1], True)] + [(p, False) for p in Rp[-2:0:-1]] + [(Rp[0], True)]
    pts += _cap(caps[0], Q[0], Rp[0], Lp[0], r, u[0], end=False, m=cap_m)
    return [(p[0], p[1] / k, on) for p, on in pts]
