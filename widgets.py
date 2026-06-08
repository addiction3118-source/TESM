# ─────────────────────────────────────────────────────────────
# widgets.py — визуальные компоненты (SVG/HTML-строки).
# Чистые функции без обращения к Streamlit-состоянию.
# ─────────────────────────────────────────────────────────────
import re


def _color(v):
    return "#3fb950" if v < 60 else "#e3b341" if v < 85 else "#f85149"


def sparkline(values, color="#bf5fff", h=32):
    if not values: return '<span style="color:#6e7681;font-size:10px">—</span>'
    vals=values[-40:]
    mx=max(vals) if max(vals)>0 else 1
    n=len(vals); w=120
    step=w/max(1,n-1)
    pts=[(i*step, h-(v/mx*(h-3))-1.5) for i,v in enumerate(vals)]
    poly=" ".join(f"{x:.1f},{y:.1f}" for x,y in pts)
    area=f"0,{h} "+poly+f" {w},{h}"
    last=vals[-1]; col=_color(last)
    uid=str(abs(hash((tuple(vals), color)))%99999)
    svg=(f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="none">'
         f'<defs><linearGradient id="sp{uid}" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0%" stop-color="{col}" stop-opacity="0.5"/>'
         f'<stop offset="100%" stop-color="{col}" stop-opacity="0"/></linearGradient></defs>'
         f'<polygon points="{area}" fill="url(#sp{uid})"/>'
         f'<polyline points="{poly}" fill="none" stroke="{col}" stroke-width="1.6" '
         f'stroke-linejoin="round" style="filter:drop-shadow(0 0 3px {col})"/></svg>')
    return (f'<div style="display:flex;align-items:center;gap:8px">{svg}'
            f'<span style="font-size:11px;font-weight:600;color:{col};font-family:JetBrains Mono">{last:.0f}%</span></div>')


def bar(pct, color):
    return f'<div class="nd-bar-wrap"><div class="nd-bar-fill" style="width:{min(pct,100):.0f}%;background:{color}"></div></div>'


def radial_gauge(pct, label, color, size=108):
    """Радиальный гейдж (SVG-кольцо) с градиентом и свечением."""
    import math
    pct=max(0.0, min(100.0, float(pct)))
    r=42.0; circ=2*math.pi*r
    off=circ*(1-pct/100.0)
    uid=re.sub(r'\W','',label) or 'g'
    return (
        f'<div class="gauge">'
        f'<svg viewBox="0 0 100 100" width="{size}" height="{size}">'
        f'<defs><linearGradient id="gg{uid}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0%" stop-color="{color}"/><stop offset="100%" stop-color="#22d3ee"/></linearGradient></defs>'
        f'<circle cx="50" cy="50" r="{r}" fill="none" stroke="#2a1a3d" stroke-width="8"/>'
        f'<circle cx="50" cy="50" r="{r}" fill="none" stroke="url(#gg{uid})" stroke-width="8" '
        f'stroke-linecap="round" stroke-dasharray="{circ:.1f}" stroke-dashoffset="{off:.1f}" '
        f'transform="rotate(-90 50 50)" style="filter:drop-shadow(0 0 5px {color});'
        f'transition:stroke-dashoffset .6s ease"/>'
        f'<text x="50" y="50" text-anchor="middle" dominant-baseline="central" fill="#e6edf3" '
        f'font-size="21" font-family="JetBrains Mono,monospace" font-weight="600">{pct:.0f}</text>'
        f'</svg><div class="gauge-label">{label}</div></div>'
    )
