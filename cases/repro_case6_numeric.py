"""Repro for case6: raw-moment vs centered expanding R^2."""
import math

def naive(y):
    xs = x2 = sy = sy2 = sxy = 0.0
    out = []
    for i, v in enumerate(y, 1):
        xs += i; x2 += i*i; sy += v; sy2 += v*v; sxy += i*v
        num = i*sxy - xs*sy
        den2 = (i*x2 - xs*xs) * (i*sy2 - sy*sy)
        if den2 <= 0:
            out.append(float('nan'))
        else:
            out.append((num / math.sqrt(den2))**2)
    return out

def centered(y):
    out = []
    for n in range(1, len(y)+1):
        a = y[:n]
        if n < 2:
            out.append(float('nan')); continue
        xm = sum(range(1, n+1))/n
        ym = sum(a)/n
        vx = sum((i-xm)**2 for i in range(1, n+1))
        vy = sum((v-ym)**2 for v in a)
        cov = sum((i-xm)*(v-ym) for i, v in zip(range(1, n+1), a))
        out.append((cov/math.sqrt(vx*vy))**2 if vx*vy > 0 else float('nan'))
    return out

def var_both(y):
    n = len(y); ym = sum(y)/n
    centered_v = sum((v-ym)**2 for v in y)/n
    naive_v = sum(v*v for v in y)/n - ym*ym
    return naive_v, centered_v

if __name__ == '__main__':
    small = [100 + 1e-6*i for i in range(6)]
    big = [1e10 + i for i in range(6)]
    print('small naive   ', [round(v, 6) for v in naive(small)])
    print('small centered', [round(v, 6) for v in centered(small)])
    print('big naive     ', naive(big))
    print('big centered  ', [round(v, 6) for v in centered(big)])
    nv, cv = var_both(small)
    print('var naive %.4e centered %.4e relerr %.1f%%' % (nv, cv, (nv-cv)/cv*100))
