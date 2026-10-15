"""
PitchPulse 360 - Elite European Football Intelligence Platform
Features:
- Dynamic Light / Dark Mode Toggle with complete color token synchronization
- Zero emojis, ultra-refined executive typography & SVG accents
- Continuous 2D Gaussian KDE pitch heatmaps (Opta/Sofascore standard)
- Transparent vector pitch markings (no clipping or boxy artifacts)
- Calibrated attribute radar charts with full margin protection
- 10,780+ Top 5 European league fixtures & 14,500+ superstar actions
"""

import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import gaussian_kde
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="PitchPulse 360 | European Football Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar Theme Switcher
st.sidebar.markdown("### THEME SELECTOR")
theme_mode = st.sidebar.radio("Display Theme:", ["Dark Theme", "Light Theme"], horizontal=True)
is_dark = (theme_mode == "Dark Theme")

# Theme Palette Tokens
if is_dark:
    bg_main = "#070d19"
    text_main = "#f1f5f9"
    sidebar_bg = "#0c1424"
    sidebar_border = "#1e293b"
    sidebar_text = "#e2e8f0"
    hero_bg = "linear-gradient(135deg, #0f172a 0%, #111e38 50%, #0c1424 100%)"
    hero_border = "#1e293b"
    card_bg = "linear-gradient(145deg, #0e172a 0%, #09101d 100%)"
    card_border = "#1e293b"
    metric_val_col = "#00f2fe"
    metric_title_col = "#94a3b8"
    tabs_bg = "#0c1424"
    tabs_border = "#1e293b"
    tab_active_bg = "#1e293b"
    tab_active_col = "#00f2fe"
    paper_bg = "#0c1424"
    plot_bg = "#070d19"
    pitch_canvas = "#08101f"
    chart_text = "#f8fafc"
    grid_color = "#1e293b"
    pitch_line_color = "rgba(255, 255, 255, 0.85)"
else:
    bg_main = "#f8fafc"
    text_main = "#0f172a"
    sidebar_bg = "#ffffff"
    sidebar_border = "#e2e8f0"
    sidebar_text = "#1e293b"
    hero_bg = "linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%)"
    hero_border = "#cbd5e1"
    card_bg = "#ffffff"
    card_border = "#e2e8f0"
    metric_val_col = "#0284c7"
    metric_title_col = "#64748b"
    tabs_bg = "#e2e8f0"
    tabs_border = "#cbd5e1"
    tab_active_bg = "#ffffff"
    tab_active_col = "#0284c7"
    paper_bg = "#ffffff"
    plot_bg = "#f8fafc"
    pitch_canvas = "#0a3a24" # Deep emerald grass for daylight clarity
    chart_text = "#0f172a"
    grid_color = "#e2e8f0"
    pitch_line_color = "rgba(255, 255, 255, 0.95)"

# Dynamic CSS Injection
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
    
    html, body, [class*="css"], .stApp {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: {bg_main} !important;
        color: {text_main} !important;
    }}
    .main {{ background-color: {bg_main}; color: {text_main}; }}
    
    header[data-testid="stHeader"] {{
        background-color: {bg_main} !important;
    }}
    
    section[data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
        border-right: 1px solid {sidebar_border} !important;
    }}
    
    section[data-testid="stSidebar"] .stMarkdown, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div {{
        color: {sidebar_text};
    }}
    
    .hero-container {{
        background: {hero_bg};
        border: 1px solid {hero_border};
        border-radius: 12px;
        padding: 22px 28px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.15);
    }}
    
    .metric-card {{
        background: {card_bg};
        border-radius: 10px;
        padding: 16px 14px;
        border: 1px solid {card_border};
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }}
    .metric-title {{
        color: {metric_title_col};
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }}
    .metric-val {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.85rem;
        font-weight: 800;
        color: {metric_val_col};
        margin-top: 4px;
        letter-spacing: -0.02em;
    }}
    .metric-sub {{
        font-size: 0.75rem;
        color: #10b981;
        margin-top: 3px;
        font-weight: 500;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: {tabs_bg};
        padding: 6px;
        border-radius: 10px;
        border: 1px solid {tabs_border};
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 42px;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        border-radius: 6px;
        color: {metric_title_col};
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {tab_active_bg} !important;
        color: {tab_active_col} !important;
        border-bottom: 2px solid {tab_active_col} !important;
    }}
</style>
""", unsafe_allow_html=True)

# Helper function to generate clean pitch boundary lines over heatmaps
def get_clean_pitch_shapes(line_color):
    sub_color = "rgba(255, 255, 255, 0.6)"
    return [
        # Outer pitch boundary
        dict(type="rect", x0=0, y0=0, x1=120, y1=80, line=dict(color=line_color, width=2), fillcolor="rgba(0,0,0,0)", layer="above"),
        # Halfway line
        dict(type="line", x0=60, y0=0, x1=60, y1=80, line=dict(color=line_color, width=2), layer="above"),
        # Center circle
        dict(type="circle", x0=50, y0=30, x1=70, y1=50, line=dict(color=line_color, width=2), fillcolor="rgba(0,0,0,0)", layer="above"),
        dict(type="circle", x0=59.4, y0=39.4, x1=60.6, y1=40.6, line=dict(color="white", width=2), fillcolor="white", layer="above"),
        # Penalty box left
        dict(type="rect", x0=0, y0=18, x1=18, y1=62, line=dict(color=line_color, width=1.5), fillcolor="rgba(0,0,0,0)", layer="above"),
        # Penalty box right
        dict(type="rect", x0=102, y0=18, x1=120, y1=62, line=dict(color=line_color, width=1.5), fillcolor="rgba(0,0,0,0)", layer="above"),
        # 6-Yard box left
        dict(type="rect", x0=0, y0=30, x1=6, y1=50, line=dict(color=sub_color, width=1), fillcolor="rgba(0,0,0,0)", layer="above"),
        # 6-Yard box right
        dict(type="rect", x0=114, y0=30, x1=120, y1=50, line=dict(color=sub_color, width=1), fillcolor="rgba(0,0,0,0)", layer="above"),
        # Goal net left
        dict(type="rect", x0=-2.5, y0=36, x1=0, y1=44, line=dict(color="#00f2fe", width=2.5), fillcolor="rgba(0,0,0,0)", layer="above"),
        # Goal net right
        dict(type="rect", x0=120, y0=36, x1=122.5, y1=44, line=dict(color="#00f2fe", width=2.5), fillcolor="rgba(0,0,0,0)", layer="above")
    ]

# Load Data from Lakehouse
@st.cache_data(ttl=60)
def load_all_data():
    from deltalake import DeltaTable
    
    silver_path = "data/lakehouse/silver_leagues"
    gold_path = "data/lakehouse/gold_standings"
    
    df_silver = DeltaTable(silver_path).to_pandas() if os.path.exists(silver_path) else pd.DataFrame()
    df_gold = DeltaTable(gold_path).to_pandas() if os.path.exists(gold_path) else pd.DataFrame()

    p_stats_path = "data/lakehouse/player_season_stats.parquet"
    p_spatial_path = "data/lakehouse/player_spatial_telemetry.parquet"

    df_players = pd.read_parquet(p_stats_path) if os.path.exists(p_stats_path) else pd.DataFrame()
    df_spatial = pd.read_parquet(p_spatial_path) if os.path.exists(p_spatial_path) else pd.DataFrame()

    return df_silver, df_gold, df_players, df_spatial

df_silver, df_gold, df_players, df_spatial = load_all_data()

if df_silver.empty or df_gold.empty:
    st.error("Data pipeline tables not found. Please run python run_pipeline.py.")
    st.stop()

# Initialize DuckDB Processor
from spark.duckdb_processor import DuckDBProcessor
proc = DuckDBProcessor()
proc.register_dataframe("silver_matches", df_silver)
proc.register_dataframe("gold_standings", df_gold)
if not df_spatial.empty:
    proc.register_dataframe("player_actions", df_spatial)

# Hero Header (Executive SVG Accent)
st.markdown(f"""
<div class="hero-container">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{metric_val_col}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="m4.93 4.93 4.24 4.24"></path>
                    <path d="m14.83 9.17 4.24-4.24"></path>
                    <path d="m14.83 14.83 4.24 4.24"></path>
                    <path d="m9.17 14.83-4.24 4.24"></path>
                    <circle cx="12" cy="12" r="4"></circle>
                </svg>
                <h1 style="margin: 0; font-size: 2rem; font-weight: 800; letter-spacing: -0.02em; color: {text_main};">
                    PITCHPULSE 360
                </h1>
            </div>
            <p style="margin: 6px 0 0 34px; color: {metric_title_col}; font-size: 0.95rem;">
                European Football Intelligence & Tactical Heatmap Engine | <b>10,780+ Top 5 League Fixtures</b>
            </p>
        </div>
        <div style="text-align: right;">
            <span style="background: rgba(16, 185, 129, 0.12); border: 1px solid #10b981; color: #10b981; padding: 6px 14px; border-radius: 6px; font-weight: 700; font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase;">
                ONLINE FEED
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar Controls
st.sidebar.markdown("### COMPETITION NAVIGATOR")
LEAGUE_OPTIONS = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]
SEASON_OPTIONS = ["2023/2024", "2022/2023", "2021/2022", "2020/2021", "2019/2020", "2018/2019"]

selected_league = st.sidebar.selectbox("Select League:", LEAGUE_OPTIONS, index=0)
selected_season = st.sidebar.selectbox("Select Season:", SEASON_OPTIONS, index=0)

cur_matches = df_silver[(df_silver["league_name"] == selected_league) & (df_silver["season"] == selected_season)]
cur_standings = proc.get_standings(selected_league, selected_season)

# Top KPI Strip
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="metric-card"><div class="metric-title">Season Fixtures</div><div class="metric-val">{len(cur_matches):,}</div><div class="metric-sub">{selected_league} ({selected_season})</div></div>""", unsafe_allow_html=True)
with c2:
    tot_goals = cur_matches["total_goals"].sum()
    avg_goals = round(tot_goals / max(len(cur_matches), 1), 2)
    st.markdown(f"""<div class="metric-card"><div class="metric-title">Total Goals</div><div class="metric-val">{tot_goals:,}</div><div class="metric-sub">{avg_goals} Goals / Game</div></div>""", unsafe_allow_html=True)
with c3:
    home_win_pct = round((len(cur_matches[cur_matches["result"] == "H"]) / max(len(cur_matches), 1)) * 100, 1)
    st.markdown(f"""<div class="metric-card"><div class="metric-title">Home Win Rate</div><div class="metric-val">{home_win_pct}%</div><div class="metric-sub">Home Pitch Advantage</div></div>""", unsafe_allow_html=True)
with c4:
    champ = cur_standings.iloc[0]["team"] if not cur_standings.empty else "TBD"
    champ_pts = cur_standings.iloc[0]["points"] if not cur_standings.empty else "-"
    st.markdown(f"""<div class="metric-card"><div class="metric-title">Champions</div><div class="metric-val" style="color:#facc15;">{champ}</div><div class="metric-sub">{champ_pts} Points</div></div>""", unsafe_allow_html=True)

st.write("")

# Main Studio Tabs
tab_standings, tab_players, tab_relegation, tab_h2h, tab_records = st.tabs([
    "STANDINGS & TITLE RACE",
    "PLAYER ANALYTICS & HEATMAPS",
    "RELEGATION DYNAMICS",
    "HEAD-TO-HEAD MATRIX",
    "ALL-TIME RECORDS"
])

# ====================================================================
# TAB 1: STANDINGS & TITLE RACE
# ====================================================================
with tab_standings:
    st.subheader(f"{selected_league} Table ({selected_season})")
    
    col_t1, col_t2 = st.columns([1.3, 1.2])

    with col_t1:
        clean_standings = cur_standings.copy()
        clean_standings["qualification"] = clean_standings["status"].apply(
            lambda x: "Champion" if "Champion" in x else (
                "UEFA Champions League" if "Champions League" in x else (
                    "UEFA Europa League" if "Europa" in x else (
                        "Relegated" if "Relegated" in x else "Mid Table"
                    )
                )
            )
        )

        st.dataframe(
            clean_standings[["position", "team", "played", "won", "drawn", "lost", "goals_for", "goals_against", "goal_diff", "points", "qualification"]],
            column_config={
                "position": st.column_config.NumberColumn("Pos", width="small"),
                "team": st.column_config.TextColumn("Club", width="medium"),
                "played": "P", "won": "W", "drawn": "D", "lost": "L",
                "goals_for": "GF", "goals_against": "GA", "goal_diff": "GD",
                "points": st.column_config.NumberColumn("PTS", width="small"),
                "qualification": "Status"
            },
            hide_index=True,
            use_container_width=True
        )

    with col_t2:
        colors = []
        for s in clean_standings["qualification"]:
            if s == "Champion": colors.append("#facc15") # Gold
            elif s == "UEFA Champions League": colors.append("#00f2fe") # Cyan
            elif s == "UEFA Europa League": colors.append("#f97316") # Orange
            elif s == "Relegated": colors.append("#ef4444") # Red
            else: colors.append("#64748b" if is_dark else "#94a3b8")

        fig_bar = go.Figure(go.Bar(
            x=clean_standings["points"],
            y=clean_standings["team"],
            orientation="h",
            marker=dict(color=colors),
            text=clean_standings["points"],
            textposition="outside",
            textfont=dict(color=chart_text, size=11)
        ))
        fig_bar.update_layout(
            title=dict(text=f"Points Distribution ({selected_league})", font=dict(color=chart_text, size=14)),
            yaxis=dict(autorange="reversed", tickfont=dict(color=chart_text)),
            xaxis=dict(title=dict(text="Points Total", font=dict(color=metric_title_col)), gridcolor=grid_color),
            paper_bgcolor=paper_bg,
            plot_bgcolor=plot_bg,
            font=dict(color=chart_text),
            margin=dict(l=10, r=25, t=40, b=10),
            height=540
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.write("---")
    st.subheader("Goal Matrix: Offensive Firepower vs Defensive Solidity")
    avg_gf = clean_standings["goals_for"].mean()
    avg_ga = clean_standings["goals_against"].mean()

    fig_quad = px.scatter(
        clean_standings,
        x="goals_for",
        y="goals_against",
        text="team",
        size="points",
        color="points",
        color_continuous_scale="Tealgrn",
        title="Attacking Output vs Defensive Vulnerability (Bubble Size = Points Total)",
        labels={"goals_for": "Goals Scored", "goals_against": "Goals Conceded"}
    )
    fig_quad.add_vline(x=avg_gf, line_dash="dash", line_color="#64748b", annotation_text="League Avg GF", annotation_font_color=chart_text)
    fig_quad.add_hline(y=avg_ga, line_dash="dash", line_color="#64748b", annotation_text="League Avg GA", annotation_font_color=chart_text)
    fig_quad.update_traces(textposition='top center', textfont=dict(color=chart_text))
    fig_quad.update_layout(
        paper_bgcolor=paper_bg, plot_bgcolor=plot_bg, font=dict(color=chart_text),
        yaxis=dict(autorange="reversed", gridcolor=grid_color),
        xaxis=dict(gridcolor=grid_color)
    )
    st.plotly_chart(fig_quad, use_container_width=True)

# ====================================================================
# TAB 2: PLAYER ANALYTICS & TACTICAL HEATMAPS
# ====================================================================
with tab_players:
    st.subheader("Superstar Spatial Analytics & Tactical Radar")
    st.caption("Granular tactical pitch data covering top European performers (2023–2024 Season).")

    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        league_filter = st.selectbox("Competition Filter:", ["All Leagues"] + LEAGUE_OPTIONS, index=0)
    
    filtered_players_df = df_players if league_filter == "All Leagues" else df_players[df_players["league"] == league_filter]
    player_names = sorted(filtered_players_df["name"].tolist())

    with col_f2:
        selected_player = st.selectbox("Select Player:", player_names, index=0)

    p_meta = df_players[df_players["name"] == selected_player].iloc[0]
    p_spatial = df_spatial[df_spatial["player_name"] == selected_player]

    # Metrics Strip
    col_p1, col_p2, col_p3, col_p4, col_p5, col_p6 = st.columns(6)
    with col_p1:
        st.markdown(f"""<div class="metric-card"><div class="metric-title">Club & Position</div><div class="metric-val" style="font-size:1.35rem; color:{text_main};">{p_meta['team']}</div><div class="metric-sub">{p_meta['pos']} ({p_meta['league']})</div></div>""", unsafe_allow_html=True)
    with col_p2:
        st.markdown(f"""<div class="metric-card"><div class="metric-title">Goals Scored</div><div class="metric-val" style="color:#10b981;">{p_meta['goals']}</div><div class="metric-sub">{p_meta['shots']} Shots</div></div>""", unsafe_allow_html=True)
    with col_p3:
        st.markdown(f"""<div class="metric-card"><div class="metric-title">Assists</div><div class="metric-val" style="color:{metric_val_col};">{p_meta['assists']}</div><div class="metric-sub">{p_meta['key_passes']} Key Passes</div></div>""", unsafe_allow_html=True)
    with col_p4:
        st.markdown(f"""<div class="metric-card"><div class="metric-title">Expected Goals</div><div class="metric-val">{p_meta['xg']}</div><div class="metric-sub">{p_meta['xa']} xA (Assists)</div></div>""", unsafe_allow_html=True)
    with col_p5:
        overperf = round(p_meta['goals'] - p_meta['xg'], 2)
        diff_color = "#10b981" if overperf >= 0 else "#f43f5e"
        st.markdown(f"""<div class="metric-card"><div class="metric-title">xG Overperformance</div><div class="metric-val" style="color:{diff_color};">{overperf:+}</div><div class="metric-sub">Conversion Edge</div></div>""", unsafe_allow_html=True)
    with col_p6:
        st.markdown(f"""<div class="metric-card"><div class="metric-title">Shot Accuracy</div><div class="metric-val">{p_meta['shot_acc_pct']}%</div><div class="metric-sub">{p_meta['conversion_pct']}% Conv Rate</div></div>""", unsafe_allow_html=True)

    st.write("")

    col_heat, col_radar = st.columns([1.35, 1])

    with col_heat:
        st.markdown(f"#### Pitch Spatial Density: **{selected_player}**")
        
        c_t1, c_t2, c_t3, c_t4, c_t5 = st.columns(5)
        with c_t1: show_heat = st.checkbox("Density Heatmap", value=True)
        with c_t2: show_goals = st.checkbox("Goals", value=True)
        with c_t3: show_assists = st.checkbox("Assists", value=True)
        with c_t4: show_shots = st.checkbox("Shots", value=True)
        with c_t5: show_passes = st.checkbox("Passes & Touches", value=False)

        fig_heat = go.Figure()

        # 1. Continuous Gaussian KDE Heatmap (Evaluated on full 120x80 pitch grid)
        if show_heat and len(p_spatial) >= 8:
            try:
                kde = gaussian_kde(np.vstack([p_spatial["x"], p_spatial["y"]]), bw_method=0.26)
                grid_x, grid_y = np.mgrid[0:120:120j, 0:80:80j]
                z = kde(np.vstack([grid_x.flatten(), grid_y.flatten()])).reshape(grid_x.shape)
                z = z / z.max() # Normalize
                z[z < 0.08] = np.nan # Transparent zero threshold

                fig_heat.add_trace(go.Heatmap(
                    x=np.linspace(0, 120, 120),
                    y=np.linspace(0, 80, 80),
                    z=z.T,
                    colorscale="Inferno" if is_dark else "YlOrRd",
                    opacity=0.82,
                    showscale=False,
                    hoverinfo="skip"
                ))
            except Exception:
                pass

        # 2. Passes / General Touches
        if show_passes:
            passes = p_spatial[p_spatial["is_pass"] == 1]
            if not passes.empty:
                fig_heat.add_trace(go.Scatter(
                    x=passes["x"], y=passes["y"],
                    mode="markers",
                    marker=dict(size=4.5, color="#38bdf8", opacity=0.4),
                    name="Pass / Touch",
                    hoverinfo="skip"
                ))

        # 3. Assists
        if show_assists:
            assists = p_spatial[p_spatial["is_assist"] == 1]
            if not assists.empty:
                fig_heat.add_trace(go.Scatter(
                    x=assists["x"], y=assists["y"],
                    mode="markers",
                    marker=dict(size=10, color="#c084fc", symbol="diamond", line=dict(color="#ffffff", width=1.5)),
                    text=[f"Assist (Min {m}')" for m in assists["minute"]],
                    hoverinfo="text",
                    name="Assist"
                ))

        # 4. Shots (Saved / Off Target)
        if show_shots:
            shots = p_spatial[(p_spatial["is_shot"] == 1) & (p_spatial["is_goal"] == 0)]
            if not shots.empty:
                fig_heat.add_trace(go.Scatter(
                    x=shots["x"], y=shots["y"],
                    mode="markers",
                    marker=dict(size=shots["xg"] * 22 + 7, color="#f59e0b", symbol="circle", line=dict(color="#ffffff", width=1)),
                    text=[f"Shot ({x:.2f} xG) in Min {m}'" for x, m in zip(shots["xg"], shots["minute"])],
                    hoverinfo="text",
                    name="Shot"
                ))

        # 5. Goals (Clean Glowing Rings)
        if show_goals:
            goals = p_spatial[p_spatial["is_goal"] == 1]
            if not goals.empty:
                fig_heat.add_trace(go.Scatter(
                    x=goals["x"], y=goals["y"],
                    mode="markers",
                    marker=dict(size=goals["xg"] * 22 + 10, color="#10b981", symbol="circle", line=dict(color="#ffffff", width=2)),
                    text=[f"GOAL ({x:.2f} xG) in Min {m}'" for x, m in zip(goals["xg"], goals["minute"])],
                    hoverinfo="text",
                    name="Goal"
                ))

        # Transparent Vector Pitch Markings
        fig_heat.update_layout(
            shapes=get_clean_pitch_shapes(pitch_line_color),
            xaxis=dict(range=[-3, 123], showgrid=False, zeroline=False, visible=False),
            yaxis=dict(range=[-3, 83], showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1),
            paper_bgcolor=paper_bg,
            plot_bgcolor=pitch_canvas,
            font=dict(color=chart_text),
            margin=dict(l=8, r=8, t=8, b=8),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11, color=chart_text))
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    with col_radar:
        st.markdown(f"#### Tactical Profile: **{selected_player}**")
        
        g = p_meta["goals"]
        xg = p_meta["xg"]
        a = p_meta["assists"]
        kp = p_meta["key_passes"]
        conv = p_meta["conversion_pct"]
        pacc = p_meta["pass_acc"]

        r_finishing = min(99.0, max(50.0, 50.0 + (g * 1.5) + ((g - xg) * 3.0)))
        r_threat = min(99.0, max(50.0, 48.0 + (xg * 1.6)))
        r_playmaking = min(99.0, max(50.0, 45.0 + (a * 3.5) + (kp * 0.35)))
        r_accuracy = min(99.0, max(50.0, pacc))
        r_conversion = min(99.0, max(50.0, conv * 3.2))

        radar_cats = ["Finishing", "Goal Threat", "Playmaking", "Passing Acc", "Conversion"]
        radar_vals = [r_finishing, r_threat, r_playmaking, r_accuracy, r_conversion]
        radar_cats.append(radar_cats[0])
        radar_vals.append(radar_vals[0])

        fig_rad = go.Figure(go.Scatterpolar(
            r=radar_vals,
            theta=radar_cats,
            fill='toself',
            fillcolor='rgba(0, 242, 254, 0.25)' if is_dark else 'rgba(2, 132, 199, 0.2)',
            line=dict(color=metric_val_col, width=2.2),
            marker=dict(color='#10b981', size=5)
        ))
        fig_rad.update_layout(
            polar=dict(
                bgcolor=paper_bg,
                radialaxis=dict(visible=True, range=[40, 100], showline=False, gridcolor=grid_color, tickfont=dict(color=metric_title_col, size=9)),
                angularaxis=dict(gridcolor=grid_color, linecolor=grid_color, tickfont=dict(color=chart_text, size=10))
            ),
            paper_bgcolor=paper_bg,
            plot_bgcolor=paper_bg,
            font=dict(color=chart_text),
            margin=dict(l=65, r=65, t=45, b=45),
            showlegend=False,
            height=440
        )
        st.plotly_chart(fig_rad, use_container_width=True)

    st.write("---")
    st.subheader("Top European Goalscorers & Playmakers")
    st.dataframe(
        filtered_players_df[["name", "team", "league", "pos", "goals", "assists", "xg", "xa", "xg_diff", "shot_acc_pct", "conversion_pct", "passes"]],
        column_config={
            "name": "Player", "team": "Club", "league": "Competition", "pos": "Role",
            "goals": "Goals", "assists": "Assists", "xg": "xG", "xa": "xA",
            "xg_diff": "xG Diff (+/-)", "shot_acc_pct": "Shot Acc %", "conversion_pct": "Conv %", "passes": "Passes"
        },
        hide_index=True,
        use_container_width=True
    )

# ====================================================================
# TAB 3: RELEGATION DYNAMICS
# ====================================================================
with tab_relegation:
    st.subheader(f"Multi-Year Relegation Dynamics: {selected_league}")
    st.caption("The Survival Line: Points required by the 17th-placed club to avoid the drop over 6 seasons.")

    survival_records = []
    for s in SEASON_OPTIONS:
        s_std = proc.get_standings(selected_league, s)
        if not s_std.empty:
            tot = len(s_std)
            safe = s_std.iloc[tot - 4]
            drop = s_std.iloc[tot - 3]
            survival_records.append({
                "Season": s,
                "Safe Club": safe["team"],
                "Safety Points": safe["points"],
                "Relegated Club": drop["team"],
                "Relegation Points": drop["points"]
            })

    df_surv = pd.DataFrame(survival_records).sort_values("Season")

    col_s1, col_s2 = st.columns([1.3, 1])
    with col_s1:
        fig_surv = go.Figure()
        fig_surv.add_trace(go.Bar(
            x=df_surv["Season"], y=df_surv["Safety Points"],
            name="Survival Threshold", marker_color="#10b981", text=df_surv["Safety Points"], textposition="auto"
        ))
        fig_surv.add_trace(go.Bar(
            x=df_surv["Season"], y=df_surv["Relegation Points"],
            name="Highest Relegated", marker_color="#ef4444", text=df_surv["Relegation Points"], textposition="auto"
        ))
        fig_surv.update_layout(
            barmode="group",
            title=dict(text="Survival Cutoff vs Relegation Line", font=dict(color=chart_text, size=14)),
            paper_bgcolor=paper_bg, plot_bgcolor=plot_bg, font=dict(color=chart_text),
            yaxis=dict(gridcolor=grid_color, title="Points Total"),
            xaxis=dict(gridcolor=grid_color)
        )
        st.plotly_chart(fig_surv, use_container_width=True)

    with col_s2:
        st.markdown(f"**Relegated Clubs Archive ({selected_league}):**")
        rel_archive = proc.get_relegation_history(selected_league)
        st.dataframe(
            rel_archive[["season", "position", "team", "points", "goal_diff"]],
            column_config={"season": "Season", "position": "Pos", "team": "Club", "points": "Pts", "goal_diff": "GD"},
            hide_index=True,
            use_container_width=True
        )

# ====================================================================
# TAB 4: HEAD-TO-HEAD MATRIX
# ====================================================================
with tab_h2h:
    st.subheader("Head-to-Head Clash & Historical Rivalries")
    
    league_clubs = sorted(list(set(df_silver[df_silver["league_name"] == selected_league]["home_team"])))
    
    cp1, cp2 = st.columns(2)
    with cp1:
        club1 = st.selectbox("Club 1:", league_clubs, index=0)
    with cp2:
        default_idx = 1 if len(league_clubs) > 1 else 0
        club2 = st.selectbox("Club 2:", league_clubs, index=default_idx)

    h2h = proc.get_head_to_head(club1, club2)
    m_h2h = h2h["matches"]
    sum_h2h = h2h["summary"]

    if not m_h2h.empty:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Meetings", sum_h2h["total_matches"])
        k2.metric(f"{club1} Wins", f"{sum_h2h['team1_wins']} ({sum_h2h['team1_goals']} Goals)")
        k3.metric("Draws", sum_h2h["draws"])
        k4.metric(f"{club2} Wins", f"{sum_h2h['team2_wins']} ({sum_h2h['team2_goals']} Goals)")

        ch1, ch2 = st.columns([1, 1.3])
        with ch1:
            fig_pie = px.pie(
                names=[f"{club1} Wins", "Draws", f"{club2} Wins"],
                values=[sum_h2h["team1_wins"], sum_h2h["draws"], sum_h2h["team2_wins"]],
                color=[f"{club1} Wins", "Draws", f"{club2} Wins"],
                color_discrete_map={f"{club1} Wins": "#00f2fe", "Draws": "#64748b", f"{club2} Wins": "#f59e0b"},
                hole=0.45,
                title=f"Win Ratio: {club1} vs {club2}"
            )
            fig_pie.update_layout(paper_bgcolor=paper_bg, font=dict(color=chart_text))
            st.plotly_chart(fig_pie, use_container_width=True)

        with ch2:
            st.markdown(f"**Match-by-Match History:**")
            st.dataframe(
                m_h2h[["match_date", "season", "home_team", "home_goals", "away_goals", "away_team", "result"]],
                column_config={"match_date": "Date", "season": "Season", "home_team": "Home", "home_goals": "HG", "away_goals": "AG", "away_team": "Away", "result": "Result"},
                hide_index=True,
                use_container_width=True
            )

    st.write("---")
    st.subheader(f"6-Year Trajectory: {club1}")
    traj = proc.get_team_trajectory(club1)
    if not traj.empty:
        col_tr1, col_tr2 = st.columns(2)
        with col_tr1:
            fig_tp = px.line(traj, x="season", y="points", markers=True, text="points", title=f"{club1} Points Trend", color_discrete_sequence=["#00f2fe" if is_dark else "#0284c7"])
            fig_tp.update_traces(textposition="top center")
            fig_tp.update_layout(paper_bgcolor=paper_bg, plot_bgcolor=plot_bg, font=dict(color=chart_text), yaxis=dict(gridcolor=grid_color))
            st.plotly_chart(fig_tp, use_container_width=True)
        with col_tr2:
            fig_tpos = px.line(traj, x="season", y="position", markers=True, text="position", title=f"{club1} Final League Finish (1st = Top)", color_discrete_sequence=["#10b981"])
            fig_tpos.update_traces(textposition="top center")
            fig_tpos.update_layout(paper_bgcolor=paper_bg, plot_bgcolor=plot_bg, font=dict(color=chart_text), yaxis=dict(autorange="reversed", gridcolor=grid_color))
            st.plotly_chart(fig_tpos, use_container_width=True)

# ====================================================================
# TAB 5: ALL-TIME RECORDS
# ====================================================================
with tab_records:
    st.subheader("All-Time European Records Across 10,780+ Matches")
    
    col_rec1, col_rec2 = st.columns([1.2, 1])
    with col_rec1:
        st.markdown("### Highest Scoring Thrillers (Top 5 Leagues)")
        thrillers = proc.get_top_scoring_matches(limit=10)
        st.dataframe(
            thrillers[["match_date", "league_name", "season", "home_team", "scoreline", "away_team", "total_goals"]],
            column_config={"match_date": "Date", "league_name": "League", "season": "Season", "home_team": "Home", "scoreline": "Score", "away_team": "Away", "total_goals": "Goals"},
            hide_index=True,
            use_container_width=True
        )

    with col_rec2:
        st.markdown("### Home vs Away Win Share Across Europe")
        home_stats = []
        for l in LEAGUE_OPTIONS:
            sub = df_silver[df_silver["league_name"] == l]
            tot = len(sub)
            home_stats.append({
                "League": l,
                "Home Win %": round((len(sub[sub["result"] == "H"]) / max(tot, 1)) * 100, 1),
                "Draw %": round((len(sub[sub["result"] == "D"]) / max(tot, 1)) * 100, 1),
                "Away Win %": round((len(sub[sub["result"] == "A"]) / max(tot, 1)) * 100, 1)
            })
        fig_ha = px.bar(
            pd.DataFrame(home_stats),
            x="League",
            y=["Home Win %", "Draw %", "Away Win %"],
            barmode="stack",
            title="Result Distribution (Top 5 Leagues)",
            color_discrete_map={"Home Win %": "#00f2fe" if is_dark else "#0284c7", "Draw %": "#64748b", "Away Win %": "#f59e0b"}
        )
        fig_ha.update_layout(paper_bgcolor=paper_bg, plot_bgcolor=plot_bg, font=dict(color=chart_text))
        st.plotly_chart(fig_ha, use_container_width=True)

    st.write("---")
    st.subheader("Roll of Honor: Every Champion Across Europe (2018–2024)")
    st.dataframe(proc.get_all_champions(), use_container_width=True)
