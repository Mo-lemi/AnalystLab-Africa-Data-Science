"""Shared chart style for the Week 5 notebook (Plotly first, Matplotlib for
statsmodels diagnostics).

Every Plotly figure is saved twice: an interactive HTML file in
``Visualizations/interactive/`` (hover shows exact values) and a static PNG in
``Visualizations/`` for the PDF report.

Colours: the three zones always use the same three categorical slots (blue,
orange, aqua), in that order, in every chart. These three pass colour-vision
deficiency checks for all pairs. Aqua is below 3:1 contrast on the light
surface, so every chart also carries a legend or direct labels, and the values
are in the CSV tables in ``Outputs/``.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import plotly.graph_objects as go
import plotly.io as pio

PROJECT_DIR = Path(__file__).resolve().parent
VIS_DIR = PROJECT_DIR / "Visualizations"
HTML_DIR = VIS_DIR / "interactive"

SURFACE = "#fcfcfb"
GRID = "#e4e3de"
AXIS = "#c9c8c1"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
MUTED = "#8a8983"

ZONE_COLORS = {"Zone1": "#2a78d6", "Zone2": "#eb6834", "Zone3": "#1baf7a"}
ZONE_LABELS = {"Zone1": "Zone 1", "Zone2": "Zone 2", "Zone3": "Zone 3"}
ACCENT = "#2a78d6"
SECOND = "#eb6834"
NEUTRAL = "#8a8983"
# Diverging blue <-> red with a grey midpoint (for correlation heatmaps)
DIVERGING = [[0.0, "#184f95"], [0.25, "#6da7ec"], [0.5, "#f0efec"],
             [0.75, "#ec8a89"], [1.0, "#a82c2c"]]
# Sequential single-hue blue (for magnitude heatmaps)
SEQUENTIAL = [[0.0, "#cde2fb"], [0.25, "#86b6ef"], [0.5, "#3987e5"],
              [0.75, "#1c5cab"], [1.0, "#0d366b"]]

FONT = "Inter, Segoe UI, Helvetica Neue, Arial, sans-serif"

_axis = dict(
    showgrid=True, gridcolor=GRID, gridwidth=1, zeroline=False,
    showline=True, linecolor=AXIS, linewidth=1, ticks="outside",
    tickcolor=AXIS, ticklen=4, tickfont=dict(color=TEXT_2, size=12),
    title=dict(font=dict(color=TEXT_2, size=13)),
)

pio.templates["week5"] = go.layout.Template(
    layout=dict(
        font=dict(family=FONT, color=TEXT, size=13),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        colorway=list(ZONE_COLORS.values()),
        title=dict(x=0, xanchor="left", font=dict(size=17, color=TEXT)),
        xaxis=_axis, yaxis=_axis,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, xanchor="left",
                    font=dict(color=TEXT_2, size=12), bgcolor="rgba(0,0,0,0)",
                    title=dict(text="")),
        hoverlabel=dict(bgcolor="white", bordercolor=AXIS, font=dict(color=TEXT, family=FONT)),
        hovermode="closest",
        margin=dict(l=70, r=30, t=90, b=60),
    ),
    data=dict(
        scatter=[go.Scatter(line=dict(width=2), marker=dict(size=8, line=dict(width=2, color=SURFACE)))],
        bar=[go.Bar(marker=dict(line=dict(width=0)))],
    ),
)
pio.templates.default = "week5"

# Keep one headless Chrome open for all PNG exports (about 0.5 s per chart
# instead of 10-15 s when kaleido starts a new browser for every image).
try:
    import kaleido
    kaleido.start_sync_server(silence_warnings=True)
except Exception:  # older kaleido: fall back to one browser per export
    pass


def title(main: str, sub: str | None = None) -> dict:
    """Two-line chart title: the finding in bold-ish primary ink, context in secondary."""
    text = main if sub is None else f"{main}<br><span style='font-size:13px;color:{TEXT_2}'>{sub}</span>"
    return dict(text=text)


def save(fig: go.Figure, name: str, width: int = 1000, height: int = 560, show: bool = True):
    """Write ``name``.png (static, 2x) and ``name``.html (interactive), then show the PNG.

    The notebook displays the static PNG rather than the live figure so that it
    renders on GitHub (which strips Plotly's JavaScript) and stays small. The
    interactive version, with hover values, is the HTML file.
    """
    VIS_DIR.mkdir(exist_ok=True)
    HTML_DIR.mkdir(exist_ok=True)
    # Fixed pixel positions from the top edge, so the title, the legend and any
    # subplot titles never overlap whatever the chart height.
    has_legend = fig.layout.showlegend is not False and any(
        t.showlegend is not False and t.name for t in fig.data)
    top = 125 if has_legend else 95
    if fig.layout.annotations and any(a.yref == "paper" and (a.y or 0) >= 1 for a in fig.layout.annotations):
        top += 20  # room for subplot titles
    fig.update_layout(
        width=width, height=height, margin_t=top,
        title=dict(yref="container", y=1 - 26 / height, yanchor="top"),
        legend=dict(yref="container", y=1 - 84 / height, yanchor="top", traceorder="normal"),
    )
    fig.write_image(VIS_DIR / f"{name}.png", width=width, height=height, scale=2)
    html = fig.to_html(include_plotlyjs="cdn", full_html=True,
                       config={"displaylogo": False, "responsive": True})
    (HTML_DIR / f"{name}.html").write_text(html, encoding="utf-8")
    if show:
        from IPython.display import Image, display
        display(Image(filename=str(VIS_DIR / f"{name}.png"), width=width))
    return fig


def zone_name(z: str) -> str:
    return ZONE_LABELS.get(z, z)


def kw_axis(fig: go.Figure, title_text: str = "Average load (kW)", **where):
    """Format a y axis for loads in kW with compact ticks (20k, 30k)."""
    fig.update_yaxes(title_text=title_text, tickformat="~s", **where)
    return fig


# Matplotlib style for the statsmodels diagnostic plots (ACF, Q-Q)
MPL_RC = {
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.labelcolor": TEXT_2, "axes.titlecolor": TEXT,
    "axes.titlesize": 12, "axes.titleweight": "normal", "axes.titlelocation": "left",
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": TEXT_2, "ytick.color": TEXT_2, "font.size": 10,
    "font.family": "sans-serif", "lines.linewidth": 1.6,
    "axes.prop_cycle": mpl.cycler(color=list(ZONE_COLORS.values())),
    "figure.dpi": 110, "savefig.dpi": 200, "savefig.bbox": "tight",
}
mpl.rcParams.update(MPL_RC)


def save_mpl(fig, name: str):
    VIS_DIR.mkdir(exist_ok=True)
    fig.savefig(VIS_DIR / f"{name}.png")
    return fig
