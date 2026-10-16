"""
PitchPulse 360 - Elite European Football Intelligence Platform
Historical football results and explicitly labeled player visualization demonstrations.
The shared UI preserves native Streamlit light/dark behavior.
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

from dashboard.ui import apply_theme, sidebar, sidebar_footer, topbar, hero, metric_card, chart, footer
apply_theme()
sidebar()
# Let native Streamlit select chart/table colors for the current appearance.
text_main = "inherit"
metric_title_col = "inherit"
metric_val_col = "#11936b"
chart_text = paper_bg = plot_bg = grid_color = None
pitch_canvas = "#0a3a24"
pitch_line_color = "rgba(255, 255, 255, 0.95)"

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
        dict(type="rect", x0=-2.5, y0=36, x1=0, y1=44, line=dict(color="#11936b", width=2.5), fillcolor="rgba(0,0,0,0)", layer="above"),
        # Goal net right
        dict(type="rect", x0=120, y0=36, x1=122.5, y1=44, line=dict(color="#11936b", width=2.5), fillcolor="rgba(0,0,0,0)", layer="above")
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

# Archive filters are genuine Streamlit controls, shared with the data queries.
st.sidebar.markdown('<div class="pp-sidebar-label">Explore a season</div>',unsafe_allow_html=True)
LEAGUE_OPTIONS = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]
SEASON_OPTIONS = ["2023/2024", "2022/2023", "2021/2022", "2020/2021", "2019/2020", "2018/2019"]
selected_league = st.sidebar.selectbox("Competition", LEAGUE_OPTIONS, index=0)
selected_season = st.sidebar.selectbox("Season", SEASON_OPTIONS, index=0)
sidebar_footer()

cur_matches = df_silver[(df_silver["league_name"] == selected_league) & (df_silver["season"] == selected_season)]
cur_standings = proc.get_standings(selected_league, selected_season)

topbar()
hero(selected_league, selected_season, len(cur_matches))
st.markdown('<div class="pp-section-eyebrow">The season at a glance</div>',unsafe_allow_html=True)
with st.container(key="overview-metrics"):
    c1, c2, c3, c4 = st.columns(4)
    tot_goals = cur_matches["total_goals"].sum()
    avg_goals = round(tot_goals / max(len(cur_matches), 1), 2)
    home_win_pct = round((len(cur_matches[cur_matches["result"] == "H"]) / max(len(cur_matches), 1)) * 100, 1)
    champ = cur_standings.iloc[0]["team"] if not cur_standings.empty else "TBD"
    champ_pts = cur_standings.iloc[0]["points"] if not cur_standings.empty else "-"
    with c1: metric_card("Matches played", f"{len(cur_matches):,}", selected_season)
    with c2: metric_card("Goals scored", f"{tot_goals:,}", f"{avg_goals} per match")
    with c3: metric_card("Home win rate", f"{home_win_pct}%", "Wins on home ground")
    with c4: metric_card("Table leader", champ, f"{champ_pts} calculated points", club=True)

# Main Studio Tabs
tab_standings, tab_players, tab_relegation, tab_h2h, tab_records = st.tabs([
    "Overview",
    "Player studio",
    "Relegation",
    "Head-to-head",
    "Season records"
])

# ====================================================================
# TAB 1: STANDINGS & TITLE RACE
# ====================================================================
with tab_standings:
    st.subheader("League standings")
    st.caption("Calculated from included results. Official points deductions, league-specific tie-breaks and qualification exceptions are not fully modeled.")
    
    with st.container(key="standings-grid"):
        col_t1, col_t2 = st.columns([1.4, 1])

        with col_t1:
            clean_standings = cur_standings.copy()
            clean_standings["qualification"] = clean_standings["status"].apply(
                lambda x: "Champion" if str(x).startswith("Champion ") else (
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
                    "position": st.column_config.NumberColumn("Pos", width=40),
                    "team": st.column_config.TextColumn("Club", width=140),
                    "played": st.column_config.NumberColumn("P", width=40),
                    "won": st.column_config.NumberColumn("W", width=40),
                    "drawn": st.column_config.NumberColumn("D", width=40),
                    "lost": st.column_config.NumberColumn("L", width=40),
                    "goals_for": "GF", "goals_against": "GA", "goal_diff": "GD",
                    "points": st.column_config.NumberColumn("PTS", width=50),
                    "qualification": "Status"
                },
                column_order=["position", "team", "played", "won", "drawn", "lost", "goal_diff", "points"],
                hide_index=True,
                width="stretch",
                height=560
            )

        with col_t2:
            st.markdown('<div class="pp-legend"><span style="--swatch:#c4a249">Leader</span><span style="--swatch:#11936b">European places</span><span style="--swatch:#c66565">Bottom three</span></div>',unsafe_allow_html=True)
            colors = []
            for s in clean_standings["qualification"]:
                if s == "Champion": colors.append("#c4a249") # Gold
                elif s == "UEFA Champions League": colors.append("#11936b") # Cyan
                elif s == "UEFA Europa League": colors.append("#6c9f8d") # Orange
                elif s == "Relegated": colors.append("#c66565") # Red
                else: colors.append("#9baba5")

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
                xaxis=dict(title=dict(text="Points Total", font=dict(color=chart_text)), gridcolor=grid_color),
                paper_bgcolor=paper_bg,
                plot_bgcolor=plot_bg,
                font=dict(color=chart_text),
                margin=dict(l=10, r=25, t=40, b=10),
                height=560
            )
            chart(fig_bar)

    st.write("---")
    st.subheader("Attack meets defence")
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
        title="Goals scored and conceded · bubble size shows points",
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
    chart(fig_quad)

# ====================================================================
# TAB 2: PLAYER ANALYTICS & TACTICAL HEATMAPS
# ====================================================================
with tab_players:
    st.subheader("Player studio")
    st.caption("Demonstration: pitch positions are computer-generated; player summary numbers are manually entered. They are not recorded player movements or a complete season dataset.")

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
                    colorscale="Inferno",
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
                    marker=dict(size=shots["xg"] * 22 + 7, color="#c4a249", symbol="circle", line=dict(color="#ffffff", width=1)),
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
        chart(fig_heat)

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
            fillcolor='rgba(59, 130, 246, 0.2)',
            line=dict(color=metric_val_col, width=2.2),
            marker=dict(color='#10b981', size=5)
        ))
        fig_rad.update_layout(
            polar=dict(
                bgcolor=paper_bg,
                radialaxis=dict(visible=True, range=[40, 100], showline=False, gridcolor=grid_color, tickfont=dict(color=chart_text, size=9)),
                angularaxis=dict(gridcolor=grid_color, linecolor=grid_color, tickfont=dict(color=chart_text, size=10))
            ),
            paper_bgcolor=paper_bg,
            plot_bgcolor=paper_bg,
            font=dict(color=chart_text),
            margin=dict(l=65, r=65, t=45, b=45),
            showlegend=False,
            height=440
        )
        chart(fig_rad)

    st.write("---")
    st.subheader("Player profiles")
    st.dataframe(
        filtered_players_df[["name", "team", "league", "pos", "goals", "assists", "xg", "xa", "xg_diff", "shot_acc_pct", "conversion_pct", "passes"]],
        column_config={
            "name": "Player", "team": "Club", "league": "Competition", "pos": "Role",
            "goals": "Goals", "assists": "Assists", "xg": "xG", "xa": "xA",
            "xg_diff": "xG Diff (+/-)", "shot_acc_pct": "Shot Acc %", "conversion_pct": "Conv %", "passes": "Passes"
        },
        hide_index=True,
        width="stretch"
    )

# ====================================================================
# TAB 3: RELEGATION DYNAMICS
# ====================================================================
with tab_relegation:
    st.subheader(f"The relegation picture · {selected_league}")
    st.caption("Illustrative bottom-three comparison across six seasons. Actual relegation and playoff rules vary by league and season.")

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
        chart(fig_surv)

    with col_s2:
        st.markdown(f"**Relegated Clubs Archive ({selected_league}):**")
        rel_archive = proc.get_relegation_history(selected_league)
        st.dataframe(
            rel_archive[["season", "position", "team", "points", "goal_diff"]],
            column_config={"season": "Season", "position": "Pos", "team": "Club", "points": "Pts", "goal_diff": "GD"},
            hide_index=True,
            width="stretch"
        )

# ====================================================================
# TAB 4: HEAD-TO-HEAD MATRIX
# ====================================================================
with tab_h2h:
    st.subheader("Head-to-head")
    
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
                color_discrete_map={f"{club1} Wins": "#11936b", "Draws": "#64748b", f"{club2} Wins": "#c4a249"},
                hole=0.45,
                title=f"Win Ratio: {club1} vs {club2}"
            )
            fig_pie.update_layout(paper_bgcolor=paper_bg, font=dict(color=chart_text))
            chart(fig_pie)

        with ch2:
            st.markdown(f"**Match-by-Match History:**")
            st.dataframe(
                m_h2h[["match_date", "season", "home_team", "home_goals", "away_goals", "away_team", "result"]],
                column_config={"match_date": "Date", "season": "Season", "home_team": "Home", "home_goals": "HG", "away_goals": "AG", "away_team": "Away", "result": "Result"},
                hide_index=True,
                width="stretch"
            )

    st.write("---")
    st.subheader(f"6-Year Trajectory: {club1}")
    traj = proc.get_team_trajectory(club1)
    if not traj.empty:
        col_tr1, col_tr2 = st.columns(2)
        with col_tr1:
            fig_tp = px.line(traj, x="season", y="points", markers=True, text="points", title=f"{club1} Points Trend", color_discrete_sequence=["#11936b"])
            fig_tp.update_traces(textposition="top center")
            fig_tp.update_layout(paper_bgcolor=paper_bg, plot_bgcolor=plot_bg, font=dict(color=chart_text), yaxis=dict(gridcolor=grid_color))
            chart(fig_tp)
        with col_tr2:
            fig_tpos = px.line(traj, x="season", y="position", markers=True, text="position", title=f"{club1} Final League Finish (1st = Top)", color_discrete_sequence=["#10b981"])
            fig_tpos.update_traces(textposition="top center")
            fig_tpos.update_layout(paper_bgcolor=paper_bg, plot_bgcolor=plot_bg, font=dict(color=chart_text), yaxis=dict(autorange="reversed", gridcolor=grid_color))
            chart(fig_tpos)

# ====================================================================
# TAB 5: ALL-TIME RECORDS
# ====================================================================
with tab_records:
    st.subheader("Records from the archive")
    
    col_rec1, col_rec2 = st.columns([1.2, 1])
    with col_rec1:
        st.markdown("### Highest Scoring Thrillers (Top 5 Leagues)")
        thrillers = proc.get_top_scoring_matches(limit=10)
        st.dataframe(
            thrillers[["match_date", "league_name", "season", "home_team", "scoreline", "away_team", "total_goals"]],
            column_config={"match_date": "Date", "league_name": "League", "season": "Season", "home_team": "Home", "scoreline": "Score", "away_team": "Away", "total_goals": "Goals"},
            hide_index=True,
            width="stretch"
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
            color_discrete_map={"Home Win %": "#11936b", "Draw %": "#64748b", "Away Win %": "#c4a249"}
        )
        fig_ha.update_layout(paper_bgcolor=paper_bg, plot_bgcolor=plot_bg, font=dict(color=chart_text))
        chart(fig_ha)

    st.write("---")
    st.subheader("Roll of Honor: Every Champion Across Europe (2018–2024)")
    st.dataframe(proc.get_all_champions(), width="stretch")

footer()
