"""Welch's t-test: exam scores, tutoring program vs control."""
import csv
import math
import statistics


def t_cdf(t: float, df: float) -> float:
    # Student t CDF by Simpson integration of the density.
    c = math.gamma((df + 1) / 2) / (math.sqrt(df * math.pi) * math.gamma(df / 2))
    f = lambda x: c * (1 + x * x / df) ** (-(df + 1) / 2)
    n, a, b = 2000, 0.0, abs(t)
    h = (b - a) / n
    s = f(a) + f(b) + sum((4 if i % 2 else 2) * f(a + i * h) for i in range(1, n))
    half = s * h / 3
    return 0.5 + half if t >= 0 else 0.5 - half


groups = {"tutoring": [], "control": []}
for row in csv.DictReader(open("data/scores.csv")):
    groups[row["group"]].append(float(row["score"]))

a, b = groups["tutoring"], groups["control"]
ma, mb = statistics.mean(a), statistics.mean(b)
va, vb = statistics.variance(a), statistics.variance(b)
se = math.sqrt(va / len(a) + vb / len(b))
t = (ma - mb) / se
df = (va / len(a) + vb / len(b)) ** 2 / ((va / len(a)) ** 2 / (len(a) - 1) + (vb / len(b)) ** 2 / (len(b) - 1))
p = 2 * (1 - t_cdf(abs(t), df))
d = (ma - mb) / math.sqrt((va + vb) / 2)

print(f"tutoring: n={len(a)} mean={ma:.1f}")
print(f"control:  n={len(b)} mean={mb:.1f}")
print(f"Welch t = {t:.2f}, df = {df:.1f}, p = {p:.3f} (two-sided)")
print(f"Cohen's d = {d:.2f}")
