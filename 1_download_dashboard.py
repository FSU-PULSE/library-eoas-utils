"""Dash dashboard for browsing, downloading, and visualizing satellite products."""

import os
import sys
# Ensure download_data is on the path so sub-modules can import each other
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "download_data"))

import re
import yaml
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import plotly.graph_objects as go

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State

# ----------------------------------------------------------------------
# 1. Global Configurations and Paths
# ----------------------------------------------------------------------
CONFIG_FILE = "config.yml"
DEFAULT_DATA_DIR = "./test_data/Satellite_Data_Examples"


def get_data_folder() -> str:
    """Resolve the local satellite data root from ``config.yml`` or defaults.

    Returns:
        Absolute or relative path to the data directory.
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                cfg = yaml.safe_load(f)
                if cfg:
                    return cfg.get("data_folder") or cfg.get("download_folder") or DEFAULT_DATA_DIR
        except Exception as e:
            print(f"Error reading config.yml: {e}")
    return DEFAULT_DATA_DIR

# ----------------------------------------------------------------------
# 2. Product metadata from download_data
# ----------------------------------------------------------------------
from download_data.dashboard_loader import (
    MAX_GRID_AXIS_POINTS,
    invalidate_slice_cache,
    load_dataset_slice,
)
from download_data.dashboard_products import (
    SATELLITE_PRODUCTS,
    SATELLITE_SUMMARY,
    format_product_date_hint,
    get_best_local_product_date,
    get_product_availability,
    get_product_file_path,
    get_product_processing_level,
    get_product_satellite_sensor,
)

DEFAULT_PRODUCT_SELECTION_COUNT = 1

# ----------------------------------------------------------------------
# 3. Metadata Layout Generator
# ----------------------------------------------------------------------
def render_metadata_layout(sensor, product_id, stats=None):
    meta = SATELLITE_PRODUCTS[sensor][product_id]
    
    # Left column: Info
    info_rows = [
        html.Div([html.Span("Source: ", className="fw-bold text-muted"), html.Span(meta["source"])]),
        html.Div([
            html.Span("Satellite / Sensor: ", className="fw-bold text-muted"),
            html.Span(get_product_satellite_sensor(meta)),
        ]),
        html.Div([
            html.Span("Processing Level: ", className="fw-bold text-muted"),
            html.Span(get_product_processing_level(meta)),
        ]),
        html.Div([html.Span("Resolution: ", className="fw-bold text-muted"), html.Span(meta["resolution"])]),
        html.Div([html.Span("Coverage: ", className="fw-bold text-muted"), html.Span(meta["period"])]),
        html.Div([html.Span("Availability: ", className="fw-bold text-muted"), html.Span(get_product_availability(product_id))]),
        html.Div([html.Span("Description: ", className="fw-bold text-muted small italic"), html.Span(meta["desc"], className="small text-muted")])
    ]
    
    # Right column: Stats
    if stats:
        val_min, val_max, val_mean, shape = stats
        shape_label = f"{shape[0]}x{shape[1]}" if len(shape) >= 2 else f"{shape[0]} points"
        stats_rows = [
            html.Div([html.Span("Min Value: ", className="fw-bold text-muted"), html.Span(f"{val_min:.3f}")]),
            html.Div([html.Span("Max Value: ", className="fw-bold text-muted"), html.Span(f"{val_max:.3f}")]),
            html.Div([html.Span("Mean Value: ", className="fw-bold text-muted"), html.Span(f"{val_mean:.3f}")]),
            html.Div([html.Span("Grid Size: ", className="fw-bold text-muted"), html.Span(shape_label)])
        ]
    else:
        stats_rows = [
            html.Div("No local file data loaded", className="text-warning small"),
            html.Div("Run the download scripts under download_data before refreshing this view.", className="text-muted small")
        ]
        
    return dbc.Row([
        dbc.Col(info_rows, md=6, className="border-end border-secondary border-opacity-25"),
        dbc.Col(stats_rows, md=6, className="ps-3")
    ], className="mt-2 pt-2 border-top border-secondary border-opacity-25 small text-muted")


_KM_PER_DEGREE = 111.0


def _format_metric_distance(km: float) -> str:
    """Format a ground distance in km or metres for display.

    Args:
        km: Distance in kilometres.

    Returns:
        Human-readable distance string such as ``~2 km`` or ``~300 m``.
    """
    if km < 1.0:
        metres = km * 1000.0
        if metres >= 100.0:
            return f"~{metres:.0f} m"
        return f"~{metres:.1f} m"
    if km < 10.0:
        return f"~{km:.1f} km"
    return f"~{km:.0f} km"


def format_resolution_with_metric(resolution: str) -> str:
    """Append km/m hints after degree values that lack a nearby metric distance.

    Args:
        resolution: Free-text resolution description from the summary table.

    Returns:
        The same text with ``(~X km)`` or ``(~X m)`` added after bare degree values.
    """
    if not resolution or "°" not in resolution:
        return resolution

    degree_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*°")
    metric_pattern = re.compile(
        r"(?:\(\s*)?~?\s*\d+(?:\.\d+)?\s*(?:km|m\b|mts|meters?)",
        re.IGNORECASE,
    )

    parts: list[str] = []
    last_index = 0
    for match in degree_pattern.finditer(resolution):
        parts.append(resolution[last_index:match.start()])
        degree_text = match.group(0)
        lookahead = resolution[match.end(): min(len(resolution), match.end() + 40)]
        if metric_pattern.search(lookahead):
            parts.append(degree_text)
        else:
            km = float(match.group(1)) * _KM_PER_DEGREE
            parts.append(f"{degree_text} ({_format_metric_distance(km)})")
        last_index = match.end()
    parts.append(resolution[last_index:])
    return "".join(parts)


def render_satellite_summary_table(summary):
    header = html.Thead(html.Tr([
        html.Th("Satellite"),
        html.Th("Instrument"),
        html.Th("Dates"),
        html.Th("L3 resolution"),
        html.Th("L4 resolution"),
        html.Th("Source"),
        html.Th("Notes"),
    ]))

    body_rows = []
    for row in summary["rows"]:
        source_link = html.A(
            row["source"],
            href=row["url"],
            target="_blank",
            rel="noopener noreferrer",
            className="summary-source-link",
        )
        body_rows.append(html.Tr([
            html.Td(row["satellite"]),
            html.Td(row["instrument"]),
            html.Td(row["dates"]),
            html.Td(format_resolution_with_metric(row["l3_resolution"])),
            html.Td(format_resolution_with_metric(row["l4_resolution"])),
            html.Td(source_link),
            html.Td(row["notes"]),
        ]))

    return dbc.Table(
        [header, html.Tbody(body_rows)],
        bordered=True,
        hover=True,
        responsive=True,
        className="summary-table",
    )


def render_satellite_summary_layout():
    sections = []
    for variable_key, summary in SATELLITE_SUMMARY.items():
        sections.append(
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.H5(summary["title"], className="mb-0 fw-bold text-white"),
                        html.Span(variable_key, className="badge-style badge bg-info text-dark"),
                    ], className="d-flex justify-content-between align-items-center")
                ], className="bg-transparent border-bottom border-secondary py-3"),
                dbc.CardBody([
                    render_satellite_summary_table(summary)
                ], className="p-0")
            ], className="panel-card mb-4")
        )

    return html.Div([
        dbc.Alert([
            html.Strong("Satellite summary metadata. "),
            html.Span("Sources were checked on 2026-06-22; links open the product or mission pages used for the table.")
        ], color="secondary", className="mb-4 panel-card"),
        html.Div(sections)
    ])


def render_satellite_summary_banner():
    return html.Div([
        html.Span("Reference Mode: ", className="text-white"),
        html.Strong("Current Satellite Instruments", className="text-info me-3"),
        html.Span("Variables: ", className="text-white"),
        html.Strong("SST, SSS, SSH, Chl-a", className="text-success")
    ], className="d-flex align-items-center w-100 justify-content-between")

# ----------------------------------------------------------------------
# 5. Data loading delegated to download_data.dashboard_loader
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# 6. Dash UI Layout (Modern Dark theme)
# ----------------------------------------------------------------------
PLOTLY_GRAPH_CONFIG = {
    "displayModeBar": True,
    "scrollZoom": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "zoomIn2d", "zoomOut2d"],
}

MAP_UIREVISION = "shared-map-viewport"

VARIABLE_COLOR_LIMITS: dict[str, tuple[float, float]] = {
    "sst": (20.0, 30.0),
    "sss": (30.5, 37.5),
    "chlora": (-1.0, 1.5),
}


def get_variable_color_limits(variable_tab: str) -> tuple[float | None, float | None]:
    """Return shared color-scale limits for all panels in a variable tab.

    Args:
        variable_tab: Dashboard tab id such as ``sst``, ``sss``, or ``chlora``.

    Returns:
        Tuple ``(zmin, zmax)`` when fixed limits exist, otherwise ``(None, None)``.
    """
    limits = VARIABLE_COLOR_LIMITS.get(variable_tab)
    if limits is None:
        return None, None
    return limits


def apply_map_viewport_to_figure(fig: go.Figure, viewport: dict | None) -> go.Figure:
    """Apply a shared lon/lat viewport to a dashboard map figure.

    Args:
        fig: Plotly figure for a satellite product panel.
        viewport: Stored viewport dict with ``autorange`` or ``x_range`` / ``y_range``.

    Returns:
        The same figure with axis limits updated when a viewport is available.
    """
    if not viewport:
        return fig

    if viewport.get("autorange"):
        fig.update_layout(
            xaxis_autorange=True,
            yaxis_autorange=True,
            uirevision=MAP_UIREVISION,
        )
        return fig

    x_range = viewport.get("x_range")
    y_range = viewport.get("y_range")
    if not x_range and not y_range:
        return fig

    layout_kwargs: dict = {"uirevision": MAP_UIREVISION}
    if x_range:
        layout_kwargs["xaxis"] = dict(range=x_range, autorange=False)
    if y_range:
        layout_kwargs["yaxis"] = dict(
            range=y_range,
            autorange=False,
            scaleanchor="x",
            scaleratio=1,
        )
    fig.update_layout(**layout_kwargs)
    return fig

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    title="EOAS Satellite Data Dashboard"
)

# Custom premium styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                background: linear-gradient(135deg, #090d16 0%, #111827 100%);
                background-attachment: fixed;
                font-family: 'Outfit', 'Inter', system-ui, -apple-system, sans-serif;
                color: #f8fafc;
            }
            .sidebar-card {
                background: rgba(17, 24, 39, 0.7);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
            }
            .panel-card {
                background: rgba(31, 41, 55, 0.6);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 16px;
                transition: all 0.3s ease;
            }
            .panel-card:hover {
                border-color: rgba(99, 102, 241, 0.3);
                box-shadow: 0 12px 20px -10px rgba(99, 102, 241, 0.2);
            }
            .glow-btn {
                background: linear-gradient(90deg, #6366f1 0%, #06b6d4 100%);
                border: none;
                border-radius: 8px;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            .glow-btn:hover {
                transform: scale(1.02);
                box-shadow: 0 0 15px rgba(99, 102, 241, 0.5);
            }
            .badge-style {
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.75rem;
                font-weight: 600;
            }
            .console-footer {
                margin-top: 0.5rem;
            }
            .console-output {
                background: #030712;
                border: 1px solid #1f2937;
                border-radius: 8px;
                font-family: 'Fira Code', monospace;
                font-size: 0.8rem;
                padding: 12px;
                min-height: 120px;
                height: 200px;
                max-height: 50vh;
                resize: vertical;
                overflow: auto;
                color: #38bdf8;
                width: 100%;
                margin-bottom: 0;
                white-space: pre-wrap;
                word-break: break-word;
            }
            .nav-pills .nav-link {
                background: rgba(31, 41, 55, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.05);
                color: #9ca3af;
                margin-right: 8px;
                border-radius: 8px;
                transition: all 0.2s ease;
            }
            .nav-pills .nav-link.active {
                background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%);
                color: white;
                box-shadow: 0 4px 10px rgba(99, 102, 241, 0.3);
            }
            .loading-status {
                min-height: 1.5rem;
            }
            .summary-table {
                color: #e5e7eb;
                font-size: 0.95rem;
                margin-bottom: 0;
            }
            .summary-table th {
                color: #a5b4fc;
                background: rgba(15, 23, 42, 0.9);
                border-color: rgba(148, 163, 184, 0.22);
                white-space: nowrap;
            }
            .summary-table td {
                background: rgba(15, 23, 42, 0.35);
                border-color: rgba(148, 163, 184, 0.18);
                vertical-align: top;
            }
            .summary-source-link {
                color: #67e8f9;
                text-decoration: none;
                font-weight: 600;
            }
            .summary-source-link:hover {
                color: #a5f3fc;
                text-decoration: underline;
            }
            ._dash-loading {
                margin: 0 auto;
            }
            ._dash-loading-callback {
                font-family: 'Outfit', 'Inter', system-ui, -apple-system, sans-serif;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.layout = dbc.Container([
    # Header Row
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H1("EOAS Satellite Data Dashboard", className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400 fw-bold mb-0 mt-3", style={"backgroundImage": "linear-gradient(to right, #818cf8, #22d3ee)", "-webkit-background-clip": "text", "-webkit-text-fill-color": "transparent"}),
                html.P("Gulf of Mexico Variable-Grouped Satellite Remote Sensing Portal", className="text-muted small mb-3")
            ], className="border-bottom border-secondary mb-3 pb-2")
        ])
    ]),
    
    # Tabs Row (stretches full width, high up in the page)
    dbc.Row([
        dbc.Col([
            dbc.Tabs([
                dbc.Tab(label="Sea Surface Temperature (SST)", tab_id="sst"),
                dbc.Tab(label="Sea Surface Salinity (SSS)", tab_id="sss"),
                dbc.Tab(label="Sea Surface Height (SSH/ADT)", tab_id="ssh"),
                dbc.Tab(label="Chlorophyll-A", tab_id="chlora"),
                dbc.Tab(label="Satellite summary", tab_id="satellite-summary"),
            ], id="variable-tabs", active_tab="sst", className="nav-pills mb-4")
        ], width=12)
    ]),
    
    # Main Content Row (Sidebar on left, Panels container on right)
    dbc.Row([
        # Sidebar Controls
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Dashboard Controls", className="card-title text-indigo-300 fw-bold border-bottom pb-2 mb-3", style={"color": "#a5b4fc"}),
                    
                    # Target Folder Info
                    html.Label("Local Data Directory", className="fw-bold small text-muted"),
                    html.Div(get_data_folder(), className="small bg-dark text-info p-2 rounded mb-3 border border-secondary", style={"wordBreak": "break-all"}),
                    

                    
                    # Subsample Stride Selector
                    html.Label("Subsample Ratio (Visualization)", className="fw-bold small text-muted"),
                    html.Div([
                        dcc.Dropdown(
                            id="subsample-stride",
                            options=[
                                {"label": "1/1 (Full Resolution)", "value": 1},
                                {"label": "1/2 Subsample", "value": 2},
                                {"label": "1/4 Subsample (Default)", "value": 4},
                                {"label": "1/8 Subsample", "value": 8},
                                {"label": "1/16 Subsample", "value": 16},
                            ],
                            value=4,
                            clearable=False,
                            className="text-dark mb-3"
                        )
                    ]),
                    
                    # Hover Toggle Selector
                    html.Label("Tooltip Options", className="fw-bold small text-muted"),
                    dbc.Checklist(
                        options=[
                            {"label": "Enable Hover Tooltips", "value": "hover"}
                        ],
                        value=[],
                        id="hover-toggle",
                        switch=True,
                        className="small mb-2 text-white"
                    ),
                    dbc.Checklist(
                        options=[
                            {"label": "Compute Loop Current overlay (SSH)", "value": "lc"}
                        ],
                        value=[],
                        id="loop-current-toggle",
                        switch=True,
                        className="small mb-3 text-white"
                    ),
                    html.Label("Region of Interest (GoM Bounds)", className="fw-bold small text-muted"),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Lon Min", className="small text-muted mb-0"),
                            dcc.Input(id="lon-min", type="number", value=-98.0, className="form-control form-control-sm bg-dark text-white border-secondary")
                        ], width=6),
                        dbc.Col([
                            html.Label("Lon Max", className="small text-muted mb-0"),
                            dcc.Input(id="lon-max", type="number", value=-60.0, className="form-control form-control-sm bg-dark text-white border-secondary")
                        ], width=6)
                    ], className="mb-2"),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Lat Min", className="small text-muted mb-0"),
                            dcc.Input(id="lat-min", type="number", value=7.5, className="form-control form-control-sm bg-dark text-white border-secondary")
                        ], width=6),
                        dbc.Col([
                            html.Label("Lat Max", className="small text-muted mb-0"),
                            dcc.Input(id="lat-max", type="number", value=50.0, className="form-control form-control-sm bg-dark text-white border-secondary")
                        ], width=6)
                    ], className="mb-3"),
                    
                    html.Label("Product Filter", className="fw-bold small text-muted mb-2"),
                    dbc.RadioItems(
                        options=[
                            {"label": "Present Only", "value": "present"},
                            {"label": "All", "value": "all"},
                        ],
                        value="present",
                        id="product-filter",
                        inline=True,
                        className="small mb-3 text-white"
                    ),

                    # Dynamic Checklist label and checklist
                    html.Label("Select Satellite / Products", className="fw-bold small text-muted mb-2", id="checklist-label", style={"color": "#a5b4fc"}),
                    dbc.Checklist(
                        options=[],
                        value=[],
                        id="product-checklist",
                        className="small mb-2 text-white"
                    ),
                    dbc.ButtonGroup([
                        dbc.Button("Select all", id="btn-select-all", size="sm", outline=True, color="info"),
                        dbc.Button("Clear", id="btn-clear-selection", size="sm", outline=True, color="secondary"),
                    ], className="w-100 mb-4"),

                    html.Label("Panel Layout", className="fw-bold small text-muted mb-2"),
                    dcc.Dropdown(
                        id="panel-layout-mode",
                        options=[
                            {"label": "Auto grid", "value": "auto"},
                            {"label": "Stack top to bottom", "value": "vertical"},
                            {"label": "Stack left to right", "value": "horizontal"},
                        ],
                        value="auto",
                        clearable=False,
                        className="text-dark mb-3",
                    ),
                    html.Label("Reorder Panels", className="fw-bold small text-muted mb-2"),
                    dcc.Dropdown(
                        id="panel-order-product",
                        options=[],
                        placeholder="Select a panel to move",
                        className="text-dark mb-2",
                    ),
                    dbc.ButtonGroup([
                        dbc.Button("Move earlier / up", id="btn-panel-earlier", size="sm", outline=True, color="info"),
                        dbc.Button("Move later / down", id="btn-panel-later", size="sm", outline=True, color="info"),
                    ], className="w-100 mb-2"),
                    dbc.Button(
                        "Reset panel order",
                        id="btn-panel-reset-order",
                        size="sm",
                        outline=True,
                        color="secondary",
                        className="w-100 mb-4",
                    ),
                    
                    dbc.Button(
                        "Download Selected",
                        id="btn-download",
                        className="w-100 glow-btn mb-2 py-2 text-white"
                    ),
                    dcc.ConfirmDialogProvider(
                        children=dbc.Button(
                            "Delete Local Files",
                            id="btn-delete-data",
                            color="danger",
                            outline=True,
                            className="w-100 mb-2 py-2"
                        ),
                        id="confirm-delete-data",
                        message="Delete all files and folders inside the download directory?"
                    ),
                    # Refresh Button
                    dbc.Button(
                        "Refresh Local Files",
                        id="btn-refresh",
                        className="w-100 glow-btn mb-2 py-2 text-white"
                    ),
                    html.Div(id="visualization-loading-status", className="loading-status text-center small mb-3"),
                ])
            ], className="sidebar-card mb-4")
        ], md=3, lg=2),
        
        # Dynamic Panels Container
        dbc.Col([
            dcc.Loading(
                id="loading-main",
                type="circle",
                color="#6366f1",
                children=html.Div([
                    dbc.Alert(
                        id="status-banner",
                        color="info",
                        className="mb-4 d-flex justify-content-between align-items-center py-2 px-3 panel-card",
                        style={"border": "1px solid rgba(255, 255, 255, 0.05)"},
                    ),
                    html.Div(id="main-panels-container"),
                    dcc.Store(id="data-revision", data=0),
                    dcc.Store(id="map-viewport-sync", storage_type="session"),
                    dcc.Store(id="panel-order-sync", storage_type="session"),
                ]),
            ),
        ], md=9, lg=10)
    ]),

    # Activity Log Footer (full width)
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Label("Activity Log Console", className="fw-bold small text-muted mb-2"),
                    html.Pre(id="console-log", className="console-output", children="System initialized. Ready for operations.")
                ], className="py-3")
            ], className="sidebar-card console-footer mb-4")
        ], width=12)
    ])
], fluid=True, className="px-4 py-2")

# ----------------------------------------------------------------------
# 7. Callback logic
# ----------------------------------------------------------------------

# Callback 1: Dynamically update product checklist options and values depending on active tab
@app.callback(
    [
        Output("product-checklist", "options"),
        Output("product-checklist", "value"),
        Output("checklist-label", "children")
    ],
    [
        Input("variable-tabs", "active_tab"),
        Input("product-filter", "value"),
    ]
)
def update_checklist_options(active_tab, product_filter):
    if active_tab == "satellite-summary":
        return [], [], "Satellite summary"

    options = []
    visible_product_keys = []
    for key, info in SATELLITE_PRODUCTS[active_tab].items():
        is_present = "present" in info.get("period", "").lower()
        if product_filter == "present" and not is_present:
            continue

        res_str = info["resolution"].split("(")[0].strip()
        label_text = f"{info['name']} ({res_str}) (Date: {format_product_date_hint(info)})"
        options.append({"label": label_text, "value": key})
        visible_product_keys.append(key)

    # By default, select only the first visible product for faster initial load.
    value = visible_product_keys[:DEFAULT_PRODUCT_SELECTION_COUNT]
    
    label_mapping = {
        "sst": "Select SST Satellites",
        "sss": "Select SSS Satellites",
        "ssh": "Select SSH Products",
        "chlora": "Select Chlorophyll Satellites",
        "satellite-summary": "Satellite summary",
    }
    label = label_mapping.get(active_tab, "Select Satellite / Products")
    
    return options, value, label


def apply_panel_order(
    selected_prods: list[str] | None,
    active_tab: str,
    panel_order_store: dict | None,
) -> list[str]:
    """Return selected products sorted by the user-defined panel order.

    Args:
        selected_prods: Product ids currently checked in the sidebar.
        active_tab: Active dashboard variable tab id.
        panel_order_store: Session store mapping tab ids to ordered product ids.

    Returns:
        Product ids in display order.
    """
    if not selected_prods:
        return []

    order = (panel_order_store or {}).get(active_tab, [])
    ordered = [prod_id for prod_id in order if prod_id in selected_prods]
    for prod_id in selected_prods:
        if prod_id not in ordered:
            ordered.append(prod_id)
    return ordered


def resolve_panel_col_width(num_selected: int, layout_mode: str) -> int:
    """Resolve Bootstrap column width for one product panel.

    Args:
        num_selected: Number of selected products in the current tab.
        layout_mode: One of ``auto``, ``vertical``, or ``horizontal``.

    Returns:
        Bootstrap column width between 3 and 12.
    """
    if layout_mode == "vertical":
        return 12
    if layout_mode == "horizontal":
        return max(3, 12 // max(num_selected, 1))
    if num_selected == 1:
        return 12
    if num_selected == 2:
        return 6
    return 4


def execute_downloads(
    active_tab: str,
    ordered_prods: list[str],
    root_dir: str,
    bbox: tuple[float, float, float, float],
) -> list[str]:
    """Download selected products and return activity-log lines."""
    log_messages = [
        f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Starting download for {len(ordered_prods)} product(s)..."
    ]
    std_bbox = (bbox[0], bbox[2], bbox[1], bbox[3])

    for prod_id in ordered_prods:
        prod_info = SATELLITE_PRODUCTS[active_tab][prod_id]
        log_messages.append(
            f"Downloading {prod_info['name']} (Type: {prod_info.get('download_type', 'unknown')})"
        )
        dtype = prod_info.get("download_type", "")
        try:
            d_date = get_best_local_product_date(prod_info, root_dir)
            output_filename = prod_info["file_fmt"](d_date)
            target_path = os.path.join(root_dir, prod_info.get("dir_rel", ""), output_filename)
            if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
                log_messages.append(f"File {output_filename} already exists locally. Skipping download.")
                continue

            if dtype == "copernicus_marine":
                cop_ds = {
                    "id": prod_info.get("dataset_id"),
                    "version": prod_info.get("version", ""),
                    "variables": prod_info.get("variables", []),
                    "name": prod_info["name"],
                    "short_name": prod_info.get("short_name", ""),
                }
                target_dir = os.path.join(root_dir, prod_info.get("dir_rel", ""))
                import download_data.Download_COPERNICUS as dl_copernicus
                dl_copernicus.download_by_day(d_date, cop_ds, std_bbox, target_dir, output_filename=output_filename)
                log_messages.append(f"Success! Downloaded Copernicus dataset: {prod_info['name']}")
            elif dtype == "podaac":
                import download_data.Download_EARTH_DATA as dl_earthdata
                from io_utils.io_common import dotdict
                earth_config = dotdict({
                    "name": prod_info.get("dataset_id", prod_info.get("name", "")),
                    "output_folder": os.path.join(root_dir, prod_info.get("dir_rel", "")),
                    "rename_files": lambda fn: output_filename,
                })
                dl_earthdata.download_by_day(d_date, earth_config, std_bbox)
                log_messages.append(f"Success! Downloaded EarthData dataset: {prod_info['name']}")
            elif dtype.startswith("erddap_"):
                import download_data.Download_ERDDAP as dl_erddap
                target_dir = os.path.join(root_dir, prod_info.get("dir_rel", ""))
                dl_erddap.download_by_day(d_date, dtype, std_bbox, target_dir, output_filename)
                log_messages.append(f"Success! Downloaded ERDDAP dataset: {prod_info['name']}")
            elif dtype == "remss_sss":
                import download_data.Download_SSS_SMAP_satellite as dl_remss
                target_dir = os.path.join(root_dir, prod_info.get("dir_rel", ""))
                dl_remss.download_by_day(d_date, target_dir, output_filename=output_filename)
                log_messages.append(f"Success! Downloaded REMSS SSS dataset: {prod_info['name']}")
            elif dtype == "coastwatch_smap_sss_daily":
                import download_data.Download_SSS_SMAP_satellite as dl_coastwatch_sss
                target_dir = os.path.join(root_dir, prod_info.get("dir_rel", ""))
                dl_coastwatch_sss.download_coastwatch_daily_by_day(
                    d_date, std_bbox, target_dir, output_filename=output_filename
                )
                log_messages.append(
                    f"Success! Downloaded CoastWatch SMAP daily SSS dataset: {prod_info['name']}"
                )
            elif dtype == "goes_abi_sst":
                import download_data.Download_GOES as dl_goes
                target_dir = os.path.join(root_dir, prod_info.get("dir_rel", ""))
                dl_goes.download_for_dashboard(
                    d_date,
                    prod_info.get("goes_product", "g19_l3c"),
                    std_bbox,
                    target_dir,
                    output_filename,
                    hour=prod_info.get("download_hour", 12),
                )
                log_messages.append(f"Success! Downloaded GOES ABI SST dataset: {prod_info['name']}")
            elif dtype == "viirs_acspo_l2p":
                import download_data.Download_VIIRS as dl_viirs
                target_dir = os.path.join(root_dir, prod_info.get("dir_rel", ""))
                dl_viirs.download_for_dashboard(d_date, std_bbox, target_dir, output_filename)
                log_messages.append(f"Success! Downloaded VIIRS ACSPO L2P SST dataset: {prod_info['name']}")
            elif dtype == "swot_karin_l2":
                import download_data.Download_SWOT as dl_swot
                target_dir = os.path.join(root_dir, prod_info.get("dir_rel", ""))
                dl_swot.download_for_dashboard(d_date, std_bbox, target_dir, output_filename)
                log_messages.append(f"Success! Downloaded SWOT KaRIn L2 SSH dataset: {prod_info['name']}")
            else:
                log_messages.append(f"Warning: Download logic for {dtype} is not wired to a download script yet.")
        except Exception as exc:
            log_messages.append(f"Error downloading {prod_info['name']}: {exc}")

    return log_messages


def load_product_panel_data(
    active_tab: str,
    prod_id: str,
    root_dir: str,
    bbox: tuple[float, float, float, float],
    stride_val: int,
    compute_loop_current: bool,
) -> dict:
    """Load one product's local file metadata and sliced values."""
    prod_info = SATELLITE_PRODUCTS[active_tab][prod_id]
    date_val = get_best_local_product_date(prod_info, root_dir)
    exists = os.path.exists(get_product_file_path(prod_info, date_val, root_dir))
    data = None
    err = None
    if exists:
        data, err = load_dataset_slice(
            active_tab,
            prod_id,
            date_val,
            root_dir,
            bbox,
            stride=stride_val,
            compute_loop_current=compute_loop_current,
        )
    return {
        "prod_id": prod_id,
        "prod_info": prod_info,
        "date_val": date_val,
        "exists": exists,
        "data": data,
        "err": err,
    }


_VISUALIZATION_LOADING_INDICATOR = html.Div(
    "Reading local files, please wait...",
    className="text-info text-center",
)

_STATUS_BANNER_LOADING = html.Div(
    "Reading satellite data...",
    className="text-white",
)


# Callback 2: Download and delete (does not block visualization)
@app.callback(
    [
        Output("console-log", "children"),
        Output("data-revision", "data"),
    ],
    [
        Input("btn-download", "n_clicks"),
        Input("confirm-delete-data", "submit_n_clicks"),
    ],
    [
        State("product-checklist", "value"),
        State("panel-order-sync", "data"),
        State("variable-tabs", "active_tab"),
        State("lon-min", "value"),
        State("lon-max", "value"),
        State("lat-min", "value"),
        State("lat-max", "value"),
        State("console-log", "children"),
        State("data-revision", "data"),
    ],
    running=[
        (Output("btn-download", "disabled"), True, False),
        (Output("btn-delete-data", "disabled"), True, False),
        (Output("visualization-loading-status", "children"), html.Div("Downloading data, please wait...", className="text-info text-center"), ""),
    ],
    prevent_initial_call=True,
)
def handle_data_operations(
    download_n_clicks,
    delete_n_clicks,
    selected_prods,
    panel_order_store,
    active_tab,
    lon_min,
    lon_max,
    lat_min,
    lat_max,
    existing_log,
    data_revision,
):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
    root_dir = get_data_folder()
    bbox = (lon_min, lon_max, lat_min, lat_max)
    ordered_prods = apply_panel_order(selected_prods, active_tab, panel_order_store)
    log_messages = []
    revision_out = data_revision or 0

    if triggered_id == "confirm-delete-data" and delete_n_clicks:
        import shutil
        try:
            for item in os.listdir(root_dir):
                item_path = os.path.join(root_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            invalidate_slice_cache()
            revision_out += 1
            log_messages.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Deleted all data inside {root_dir}")
        except Exception as exc:
            log_messages.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Failed to delete data: {exc}")
    elif triggered_id == "btn-download" and download_n_clicks and ordered_prods and active_tab != "satellite-summary":
        log_messages.extend(execute_downloads(active_tab, ordered_prods, root_dir, bbox))
        invalidate_slice_cache()
        revision_out += 1

    full_log = "\n".join(log_messages) + "\n\n" + (existing_log if existing_log else "")
    return full_log[:5000], revision_out


@app.callback(
    Output("product-checklist", "value", allow_duplicate=True),
    [
        Input("btn-select-all", "n_clicks"),
        Input("btn-clear-selection", "n_clicks"),
    ],
    [
        State("product-checklist", "options"),
        State("product-checklist", "value"),
    ],
    prevent_initial_call=True,
)
def update_product_selection(select_all_clicks, clear_clicks, options, current_value):
    triggered = dash.callback_context.triggered[0]["prop_id"].split(".")[0] if dash.callback_context.triggered else ""
    if triggered == "btn-select-all":
        return [option["value"] for option in (options or [])]
    if triggered == "btn-clear-selection":
        return []
    return current_value or []


# Callback 3: Render selected local products in a dynamic grid
@app.callback(
    [
        Output("status-banner", "children"),
        Output("main-panels-container", "children"),
        Output("map-viewport-sync", "data", allow_duplicate=True),
    ],
    [
        Input("btn-refresh", "n_clicks"),
        Input("product-checklist", "value"),
        Input("panel-layout-mode", "value"),
        Input("panel-order-sync", "data"),
        Input("subsample-stride", "value"),
        Input("hover-toggle", "value"),
        Input("loop-current-toggle", "value"),
        Input("data-revision", "data"),
    ],
    [
        State("variable-tabs", "active_tab"),
        State("lon-min", "value"),
        State("lon-max", "value"),
        State("lat-min", "value"),
        State("lat-max", "value"),
        State("map-viewport-sync", "data"),
    ],
    running=[
        (Output("btn-refresh", "disabled"), True, False),
        (Output("visualization-loading-status", "children", allow_duplicate=True), _VISUALIZATION_LOADING_INDICATOR, ""),
        (Output("status-banner", "children", allow_duplicate=True), _STATUS_BANNER_LOADING, ""),
    ],
    prevent_initial_call="initial_duplicate",
)
def render_panels(
    refresh_n_clicks,
    selected_prods,
    panel_layout_mode,
    panel_order_store,
    stride,
    hover_toggle,
    loop_current_toggle,
    data_revision,
    active_tab,
    lon_min,
    lon_max,
    lat_min,
    lat_max,
    map_viewport_sync,
):
    del refresh_n_clicks, data_revision
    try:
        stride_val = int(stride)
    except (ValueError, TypeError):
        stride_val = 4

    root_dir = get_data_folder()
    bbox = (lon_min, lon_max, lat_min, lat_max)
    ordered_prods = apply_panel_order(selected_prods, active_tab, panel_order_store)
    viewport_for_figures = map_viewport_sync
    compute_loop_current = "lc" in (loop_current_toggle or [])

    if active_tab == "satellite-summary":
        return render_satellite_summary_banner(), render_satellite_summary_layout(), dash.no_update

    if not ordered_prods:
        banner_content = html.Div([
            html.Span("Visualization Mode: ", className="text-white"),
            html.Strong("Dataset Dates", className="text-info me-3"),
            html.Span("No products selected", className="text-warning"),
        ], className="d-flex align-items-center w-100 justify-content-between")
        placeholder_layout = dbc.Card([
            dbc.CardBody([
                html.H4("No Products Selected", className="text-warning text-center fw-bold mb-2"),
                html.P(
                    "Please check one or more satellite products in the sidebar, then click Refresh.",
                    className="text-muted text-center small mb-0",
                ),
            ], className="py-5"),
        ], className="panel-card")
        return banner_content, placeholder_layout, dash.no_update

    panel_data_by_id: dict[str, dict] = {}
    max_workers = min(6, max(1, len(ordered_prods)))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                load_product_panel_data,
                active_tab,
                prod_id,
                root_dir,
                bbox,
                stride_val,
                compute_loop_current,
            ): prod_id
            for prod_id in ordered_prods
        }
        for future in as_completed(futures):
            payload = future.result()
            panel_data_by_id[payload["prod_id"]] = payload

    panel_cards = []
    found_count = 0
    num_selected = len(ordered_prods)
    col_width = resolve_panel_col_width(num_selected, panel_layout_mode or "auto")

    for prod_id in ordered_prods:
        payload = panel_data_by_id[prod_id]
        prod_info = payload["prod_info"]
        date_str = payload["date_val"].strftime("%Y-%m-%d")
        exists = payload["exists"]
        data = payload["data"]
        err = payload["err"]

        badge_label = "Available" if exists else "Not Found"
        badge_class = "badge-style badge bg-success text-light" if exists else "badge-style badge bg-danger text-light"

        if exists:
            if err:
                fig = go.Figure().update_layout(
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#f8fafc"),
                )
                fig.add_annotation(text=err, showarrow=False, font=dict(color="red", size=14))
                meta_layout = html.Div([
                    html.Div(f"Error details: {err}", className="text-danger fw-bold small mb-2"),
                    render_metadata_layout(active_tab, prod_id, stats=None),
                ])
            else:
                found_count += 1
                if active_tab == "ssh":
                    lons, lats, values, colorscale, title_name, lc_coords = data
                else:
                    lons, lats, values, colorscale, title_name = data
                    lc_coords = None

                nan_mask = np.isnan(values)
                valid_values = values[~nan_mask]
                val_min = np.min(valid_values) if len(valid_values) > 0 else 0
                val_max = np.max(valid_values) if len(valid_values) > 0 else 0
                val_mean = np.mean(valid_values) if len(valid_values) > 0 else 0

                zmin, zmax = get_variable_color_limits(active_tab)
                show_hover = "hover" in (hover_toggle or [])
                hover_info_val = None if show_hover else "skip"
                hover_tmpl_val = (
                    "Lon: %{x:.2f}°<br>Lat: %{y:.2f}°<br>Value: %{z:.3f}<extra></extra>"
                    if show_hover else None
                )
                colorbar_cfg = dict(title=dict(text=title_name, side="right"), thickness=15, len=0.85)

                grid_points = int(values.size) if values.ndim >= 2 else len(values)
                use_heatmap = values.ndim >= 2 and grid_points <= MAX_GRID_AXIS_POINTS * MAX_GRID_AXIS_POINTS
                if use_heatmap:
                    fig = go.Figure(data=go.Heatmap(
                        z=values,
                        x=lons,
                        y=lats,
                        colorscale=colorscale,
                        zmin=zmin,
                        zmax=zmax,
                        hoverinfo=hover_info_val,
                        hovertemplate=hover_tmpl_val,
                        colorbar=colorbar_cfg,
                    ))
                else:
                    if values.ndim >= 2:
                        lon_grid, lat_grid = np.meshgrid(lons, lats)
                        plot_x = lon_grid.ravel()
                        plot_y = lat_grid.ravel()
                        plot_z = values.ravel()
                    else:
                        plot_x = lons
                        plot_y = lats
                        plot_z = values
                    marker_kwargs = dict(color=plot_z, colorscale=colorscale, colorbar=colorbar_cfg, size=4)
                    if zmin is not None:
                        marker_kwargs["cmin"] = zmin
                    if zmax is not None:
                        marker_kwargs["cmax"] = zmax
                    fig = go.Figure(data=go.Scattergl(
                        x=plot_x,
                        y=plot_y,
                        mode="markers",
                        marker=marker_kwargs,
                        hoverinfo=hover_info_val,
                        hovertemplate=hover_tmpl_val,
                    ))

                if active_tab == "ssh" and lc_coords and len(lc_coords) > 0:
                    lc_lons = [pt[0] for pt in lc_coords]
                    lc_lats = [pt[1] for pt in lc_coords]
                    fig.add_trace(go.Scatter(
                        x=lc_lons,
                        y=lc_lats,
                        mode="lines",
                        name="Loop Current",
                        line=dict(color="#ef4444", width=3),
                        showlegend=True,
                    ))

                fig.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#cbd5e1"),
                    dragmode="pan",
                    uirevision=MAP_UIREVISION,
                    xaxis=dict(showgrid=True, gridcolor="#334155", zeroline=False),
                    yaxis=dict(showgrid=True, gridcolor="#334155", zeroline=False, scaleanchor="x", scaleratio=1),
                )
                fig = apply_map_viewport_to_figure(fig, viewport_for_figures)
                meta_layout = render_metadata_layout(
                    active_tab, prod_id, stats=(val_min, val_max, val_mean, values.shape)
                )
        else:
            fig = go.Figure().update_layout(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#f8fafc"),
            )
            fig.add_annotation(
                text="No local data file found. Run a download script under download_data, then refresh.",
                showarrow=False,
                font=dict(color="#94a3b8", size=14),
            )
            meta_layout = render_metadata_layout(active_tab, prod_id, stats=None)

        panel_cards.append(dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.Span(f"{prod_info['name']} ({date_str})", className="fw-bold text-white small"),
                        html.Span(badge_label, className=badge_class),
                    ], className="d-flex justify-content-between align-items-center"),
                ], className="bg-transparent border-bottom border-secondary py-2"),
                dbc.CardBody([
                    dcc.Graph(
                        id={"type": "graph", "index": prod_id},
                        figure=fig,
                        config=PLOTLY_GRAPH_CONFIG,
                        style={"height": "380px"},
                    ),
                    html.Div(meta_layout),
                ]),
            ], className="panel-card mb-4"),
        ], md=col_width))

    banner_content = html.Div([
        html.Span("Visualization Mode: ", className="text-white"),
        html.Strong("Dataset Dates", className="text-info me-3"),
        html.Span("Loaded Products: ", className="text-white"),
        html.Strong(
            f"{found_count} of {num_selected} selected",
            className="text-success" if found_count == num_selected else "text-warning",
        ),
    ], className="d-flex align-items-center w-100 justify-content-between")

    return banner_content, dbc.Row(panel_cards), dash.no_update


@app.callback(
    [
        Output("panel-order-product", "options"),
        Output("panel-order-product", "value"),
    ],
    [
        Input("product-checklist", "value"),
        Input("variable-tabs", "active_tab"),
    ],
)
def update_panel_order_dropdown(
    selected_prods: list[str] | None,
    active_tab: str,
) -> tuple[list[dict[str, str]], str | None]:
    """Populate the panel reorder dropdown from the active product checklist.

    Args:
        selected_prods: Product ids currently checked in the sidebar.
        active_tab: Active dashboard variable tab id.

    Returns:
        Dropdown options and the currently selected product id.
    """
    if active_tab == "satellite-summary" or not selected_prods:
        return [], None

    options = []
    for prod_id in selected_prods:
        prod_info = SATELLITE_PRODUCTS[active_tab][prod_id]
        options.append({"label": prod_info["name"], "value": prod_id})
    return options, selected_prods[0]


@app.callback(
    Output("panel-order-sync", "data"),
    [
        Input("btn-panel-earlier", "n_clicks"),
        Input("btn-panel-later", "n_clicks"),
        Input("btn-panel-reset-order", "n_clicks"),
        Input("product-checklist", "value"),
    ],
    [
        State("panel-order-product", "value"),
        State("panel-order-sync", "data"),
        State("variable-tabs", "active_tab"),
    ],
    prevent_initial_call=True,
)
def update_panel_order_store(
    earlier_clicks: int | None,
    later_clicks: int | None,
    reset_clicks: int | None,
    selected_prods: list[str] | None,
    panel_product: str | None,
    panel_order_store: dict | None,
    active_tab: str,
) -> dict:
    """Update the stored panel order when the user reorders or changes selection.

    Args:
        earlier_clicks: Click count for the move-earlier button.
        later_clicks: Click count for the move-later button.
        reset_clicks: Click count for the reset-order button.
        selected_prods: Product ids currently checked in the sidebar.
        panel_product: Product id selected in the reorder dropdown.
        panel_order_store: Session store mapping tab ids to ordered product ids.
        active_tab: Active dashboard variable tab id.

    Returns:
        Updated panel order store.
    """
    store = dict(panel_order_store or {})
    selected = list(selected_prods or [])
    current_order = [prod_id for prod_id in store.get(active_tab, []) if prod_id in selected]
    for prod_id in selected:
        if prod_id not in current_order:
            current_order.append(prod_id)

    triggered = dash.callback_context.triggered[0]["prop_id"].split(".")[0] if dash.callback_context.triggered else ""

    if triggered == "btn-panel-reset-order":
        store[active_tab] = list(selected)
        return store

    if triggered == "product-checklist":
        store[active_tab] = current_order
        return store

    if not panel_product or panel_product not in current_order:
        store[active_tab] = current_order
        return store

    index = current_order.index(panel_product)
    if triggered == "btn-panel-earlier" and index > 0:
        current_order[index - 1], current_order[index] = current_order[index], current_order[index - 1]
    elif triggered == "btn-panel-later" and index < len(current_order) - 1:
        current_order[index + 1], current_order[index] = current_order[index], current_order[index + 1]

    store[active_tab] = current_order
    return store


app.clientside_callback(
    """
    function(relayout_data_list, current_figures) {
        const ctx = window.dash_clientside.callback_context;
        if (!ctx.triggered || ctx.triggered.length === 0) {
            return [window.dash_clientside.no_update, window.dash_clientside.no_update];
        }

        const triggeredProp = ctx.triggered[0].prop_id;
        if (!triggeredProp.includes('.')) {
            return [window.dash_clientside.no_update, window.dash_clientside.no_update];
        }

        const triggeredIdStr = triggeredProp.split('.')[0];
        let triggeredId;
        try {
            triggeredId = JSON.parse(triggeredIdStr);
        } catch (e) {
            return [window.dash_clientside.no_update, window.dash_clientside.no_update];
        }

        const inputs = ctx.inputs_list[0];
        const triggeredIndex = inputs.findIndex(inp => {
            return inp.id && inp.id.index === triggeredId.index && inp.id.type === triggeredId.type;
        });

        if (triggeredIndex === -1) {
            return [window.dash_clientside.no_update, window.dash_clientside.no_update];
        }

        const relayout_data = relayout_data_list[triggeredIndex];
        if (!relayout_data) {
            return [window.dash_clientside.no_update, window.dash_clientside.no_update];
        }

        let update_x = false;
        let update_y = false;
        let x_range = null;
        let y_range = null;
        let x_auto = false;
        let y_auto = false;
        let is_auto = false;

        if (relayout_data['xaxis.autorange'] !== undefined || relayout_data['yaxis.autorange'] !== undefined) {
            is_auto = true;
            x_auto = relayout_data['xaxis.autorange'] !== false;
            y_auto = relayout_data['yaxis.autorange'] !== false;
        } else {
            if (relayout_data['xaxis.range'] !== undefined) {
                x_range = relayout_data['xaxis.range'];
                update_x = true;
            } else if (relayout_data['xaxis.range[0]'] !== undefined) {
                x_range = [relayout_data['xaxis.range[0]'], relayout_data['xaxis.range[1]']];
                update_x = true;
            }

            if (relayout_data['yaxis.range'] !== undefined) {
                y_range = relayout_data['yaxis.range'];
                update_y = true;
            } else if (relayout_data['yaxis.range[0]'] !== undefined) {
                y_range = [relayout_data['yaxis.range[0]'], relayout_data['yaxis.range[1]']];
                update_y = true;
            }
        }

        if (!is_auto && !update_x && !update_y) {
            return [window.dash_clientside.no_update, window.dash_clientside.no_update];
        }

        let viewport_data;
        if (is_auto) {
            viewport_data = {autorange: true};
        } else {
            viewport_data = {autorange: false};
            if (x_range) {
                viewport_data.x_range = x_range;
            }
            if (y_range) {
                viewport_data.y_range = y_range;
            }
        }

        let any_change = false;
        const new_figures = current_figures.map((fig, idx) => {
            if (!fig) return fig;
            if (idx === triggeredIndex) {
                return fig;
            }

            const current_x_range = fig.layout && fig.layout.xaxis ? fig.layout.xaxis.range : undefined;
            const current_y_range = fig.layout && fig.layout.yaxis ? fig.layout.yaxis.range : undefined;
            const current_x_auto = fig.layout && fig.layout.xaxis ? fig.layout.xaxis.autorange : undefined;
            const current_y_auto = fig.layout && fig.layout.yaxis ? fig.layout.yaxis.autorange : undefined;

            let fig_needs_update = false;

            if (is_auto) {
                if (current_x_auto !== x_auto || current_y_auto !== y_auto) {
                    fig_needs_update = true;
                }
            } else {
                const tol = 1e-7;
                if (update_x) {
                    if (current_x_auto !== false || !current_x_range) {
                        fig_needs_update = true;
                    } else {
                        const diff_x0 = Math.abs(current_x_range[0] - x_range[0]);
                        const diff_x1 = Math.abs(current_x_range[1] - x_range[1]);
                        if (diff_x0 > tol || diff_x1 > tol) {
                            fig_needs_update = true;
                        }
                    }
                }
                if (update_y) {
                    if (current_y_auto !== false || !current_y_range) {
                        fig_needs_update = true;
                    } else {
                        const diff_y0 = Math.abs(current_y_range[0] - y_range[0]);
                        const diff_y1 = Math.abs(current_y_range[1] - y_range[1]);
                        if (diff_y0 > tol || diff_y1 > tol) {
                            fig_needs_update = true;
                        }
                    }
                }
            }

            if (fig_needs_update) {
                any_change = true;
                const updated_fig = JSON.parse(JSON.stringify(fig));
                if (!updated_fig.layout) updated_fig.layout = {};
                if (!updated_fig.layout.xaxis) updated_fig.layout.xaxis = {};
                if (!updated_fig.layout.yaxis) updated_fig.layout.yaxis = {};
                updated_fig.layout.uirevision = "shared-map-viewport";

                if (is_auto) {
                    updated_fig.layout.xaxis.autorange = x_auto;
                    updated_fig.layout.yaxis.autorange = y_auto;
                } else {
                    if (update_x) {
                        updated_fig.layout.xaxis.range = x_range;
                        updated_fig.layout.xaxis.autorange = false;
                    }
                    if (update_y) {
                        updated_fig.layout.yaxis.range = y_range;
                        updated_fig.layout.yaxis.autorange = false;
                        updated_fig.layout.yaxis.scaleanchor = "x";
                        updated_fig.layout.yaxis.scaleratio = 1;
                    }
                }
                return updated_fig;
            }

            return fig;
        });

        if (!any_change) {
            return [window.dash_clientside.no_update, viewport_data];
        }
        return [new_figures, viewport_data];
    }
    """,
    [
        Output({"type": "graph", "index": dash.dependencies.ALL}, "figure"),
        Output("map-viewport-sync", "data"),
    ],
    [Input({"type": "graph", "index": dash.dependencies.ALL}, "relayoutData")],
    [State({"type": "graph", "index": dash.dependencies.ALL}, "figure")],
    prevent_initial_call=True
)

# ----------------------------------------------------------------------
# 8. Start dashboard server
# ----------------------------------------------------------------------
if __name__ == '__main__':
    print("Starting Dash Satellite Dashboard server on port 8050...")
    app.run(debug=False, host='127.0.0.1', port=8050)
