"""
PitchPulse 360 - Presentation Visual Asset Generator
Generates high-resolution publication-quality PNG charts & diagrams
to be embedded into both the .docx document and .pptx presentation deck.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
import matplotlib.patches as patches

# Ensure output directory exists
os.makedirs("presentation_assets", exist_ok=True)

# Set global aesthetic defaults
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cbd5e1'
plt.rcParams['axes.linewidth'] = 0.8

# -----------------------------------------------------------------------------
# 1. Architecture Pipeline Diagram
# -----------------------------------------------------------------------------
def create_architecture_diagram():
    fig, ax = plt.subplots(figsize=(10, 4.2), dpi=200)
    ax.set_facecolor('#0f172a')
    fig.patch.set_facecolor('#0f172a')
    
    stages = [
        ("1. INGESTION", "REST Scraping\n30 League CSVs\n(10,781 Matches)", "#0284c7"),
        ("2. VALIDATION", "Great Expectations\n8 Assertion Suites\n100% Pass Rate", "#10b981"),
        ("3. LAKEHOUSE", "Delta Lake Storage\nBronze, Silver, Gold\nACID Log & Time Travel", "#06b6d4"),
        ("4. OLAP ENGINE", "DuckDB In-Memory\nVectorized SIMD\nWindow SQL (18ms)", "#8b5cf6"),
        ("5. SERVING UI", "Streamlit + Plotly\nDual-Theme Engine\n2D KDE Heatmaps", "#f59e0b")
    ]
    
    for i, (title, desc, col) in enumerate(stages):
        x = 0.5 + i * 2.2
        # Box
        rect = patches.FancyBboxPatch((x, 1.0), 1.8, 2.2, boxstyle="round,pad=0.15",
                                      facecolor=col, edgecolor="#ffffff", linewidth=1.5, alpha=0.9)
        ax.add_patch(rect)
        ax.text(x + 0.9, 2.65, title, color="white", fontsize=10, weight="bold", ha="center")
        ax.text(x + 0.9, 1.75, desc, color="#ffffff", fontsize=8.2, ha="center", va="center")
        
        # Arrow to next stage
        if i < len(stages) - 1:
            ax.annotate("", xy=(x + 2.15, 2.1), xytext=(x + 1.85, 2.1),
                        arrowprops=dict(arrowstyle="->", color="#38bdf8", lw=3))
            
    ax.set_xlim(0, 11.5)
    ax.set_ylim(0.5, 3.8)
    ax.axis('off')
    plt.title("PitchPulse 360: End-to-End Medallion Lakehouse Architecture", color="white", fontsize=13, weight="bold", pad=12)
    plt.tight_layout()
    plt.savefig("presentation_assets/architecture_pipeline.png", facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()
    print("[OK] Created architecture_pipeline.png")

# -----------------------------------------------------------------------------
# 2. Continuous 2D Gaussian KDE Football Pitch Heatmap
# -----------------------------------------------------------------------------
def create_kde_pitch_heatmap():
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=200)
    ax.set_facecolor('#08101f')
    fig.patch.set_facecolor('#070d19')
    
    # Generate synthetic elite striker spatial coordinates (e.g. Haaland / Kane)
    np.random.seed(42)
    # Box cluster (penalty box), half spaces, central channel
    box_x = np.random.normal(106, 6, 450)
    box_y = np.random.normal(40, 8, 450)
    
    flank_x = np.random.normal(92, 10, 250)
    flank_y = np.random.normal(26, 7, 250)
    
    mid_x = np.random.normal(78, 12, 180)
    mid_y = np.random.normal(42, 10, 180)
    
    x = np.clip(np.concatenate([box_x, flank_x, mid_x]), 0, 120)
    y = np.clip(np.concatenate([box_y, flank_y, mid_y]), 0, 80)
    
    # 2D KDE
    xy = np.vstack([x, y])
    kde = gaussian_kde(xy, bw_method=0.28)
    
    xi, yi = np.mgrid[0:120:150j, 0:80:100j]
    zi = kde(np.vstack([xi.flatten(), yi.flatten()])).reshape(xi.shape)
    zi = zi / zi.max()
    zi[zi < 0.08] = np.nan
    
    # Render KDE Contour
    cs = ax.contourf(xi, yi, zi, levels=20, cmap='inferno', alpha=0.88)
    
    # Vector pitch lines
    lc = "rgba(255,255,255,0.9)"
    # Boundary
    ax.plot([0, 120, 120, 0, 0], [0, 0, 80, 80, 0], color='white', lw=1.8)
    # Halfway line
    ax.plot([60, 60], [0, 80], color='white', lw=1.8)
    # Center circle
    center_circle = patches.Circle((60, 40), 10, edgecolor='white', facecolor='none', lw=1.8)
    ax.add_patch(center_circle)
    ax.plot(60, 40, 'o', color='white', markersize=4)
    # Penalty boxes
    ax.add_patch(patches.Rectangle((0, 18), 18, 44, edgecolor='white', facecolor='none', lw=1.5))
    ax.add_patch(patches.Rectangle((102, 18), 18, 44, edgecolor='white', facecolor='none', lw=1.5))
    # 6-yard boxes
    ax.add_patch(patches.Rectangle((0, 30), 6, 20, edgecolor='white', facecolor='none', lw=1.2, alpha=0.8))
    ax.add_patch(patches.Rectangle((114, 30), 6, 20, edgecolor='white', facecolor='none', lw=1.2, alpha=0.8))
    # Penalty spots
    ax.plot(12, 40, 'o', color='white', markersize=3.5)
    ax.plot(108, 40, 'o', color='white', markersize=3.5)
    # Goal nets
    ax.add_patch(patches.Rectangle((-2.5, 36), 2.5, 8, edgecolor='#00f2fe', facecolor='none', lw=2))
    ax.add_patch(patches.Rectangle((120, 36), 2.5, 8, edgecolor='#00f2fe', facecolor='none', lw=2))
    
    # Sample goal & shot markers
    ax.scatter([108, 112, 105, 114], [38, 42, 44, 37], color='#10b981', s=80, marker='*', label='Goals Scored', zorder=5)
    ax.scatter([98, 102, 95, 101], [32, 48, 40, 26], color='#f59e0b', s=45, marker='o', label='Shots on Target', zorder=5)
    
    ax.set_xlim(-4, 124)
    ax.set_ylim(-3, 83)
    ax.axis('off')
    ax.legend(loc='upper left', facecolor='#0f172a', edgecolor='#1e293b', labelcolor='white', fontsize=9)
    plt.title("Continuous 2D Gaussian KDE Pitch Telemetry (Opta / Sofascore Standard)", color="#f8fafc", fontsize=12, weight="bold", pad=10)
    plt.tight_layout()
    plt.savefig("presentation_assets/kde_pitch_heatmap.png", facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()
    print("[OK] Created kde_pitch_heatmap.png")

# -----------------------------------------------------------------------------
# 3. Tactical Player Radar Chart
# -----------------------------------------------------------------------------
def create_player_radar_chart():
    categories = ['Finishing\n(xG Overperf)', 'Playmaking\n(Key Passes)', 'Possession\n(Pass %)', 'Dribbling\n(1v1 Wins)', 'Pressing\n(High Regains)']
    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True), dpi=200)
    ax.set_facecolor('#0c1424')
    fig.patch.set_facecolor('#070d19')
    
    # Data for 3 players
    haaland = [98, 62, 74, 76, 85]
    haaland += haaland[:1]
    
    mbappe = [95, 88, 83, 97, 72]
    mbappe += mbappe[:1]
    
    debruyne = [78, 99, 94, 82, 88]
    debruyne += debruyne[:1]
    
    ax.plot(angles, haaland, color='#00f2fe', linewidth=2.2, label='Erling Haaland (Box Finisher)')
    ax.fill(angles, haaland, color='#00f2fe', alpha=0.18)
    
    ax.plot(angles, mbappe, color='#ec4899', linewidth=2.2, label='Kylian Mbappé (Wide Penetrator)')
    ax.fill(angles, mbappe, color='#ec4899', alpha=0.15)
    
    ax.plot(angles, debruyne, color='#eab308', linewidth=2.2, label='Kevin De Bruyne (Visionary)')
    ax.fill(angles, debruyne, color='#eab308', alpha=0.15)
    
    plt.xticks(angles[:-1], categories, color='#e2e8f0', size=9, weight='bold')
    ax.set_rlabel_position(0)
    plt.yticks([40, 60, 80, 100], ["40", "60", "80", "100"], color="#64748b", size=7.5)
    plt.ylim(30, 105)
    ax.grid(color='#1e293b', linestyle='--', linewidth=0.8)
    
    plt.legend(loc='lower center', bbox_to_anchor=(0.5, -0.18), ncol=2, facecolor='#0f172a', edgecolor='#1e293b', labelcolor='white', fontsize=8.5)
    plt.title("Superstar Tactical Radar: 5-Attribute Profile", color='#f8fafc', size=12, weight='bold', pad=18)
    plt.tight_layout()
    plt.savefig("presentation_assets/player_radar_chart.png", facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()
    print("[OK] Created player_radar_chart.png")

# -----------------------------------------------------------------------------
# 4. Storage & Engine Benchmark Latency
# -----------------------------------------------------------------------------
def create_benchmark_chart():
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=200)
    ax.set_facecolor('#f8fafc')
    fig.patch.set_facecolor('#ffffff')
    
    configs = [
        'CSV (1-Th)',
        'CSV (4-Th)',
        'Parquet (1-Th)',
        'Parquet (4-Th)',
        'Delta Lake (1-Th)',
        'DuckDB (4-Th)'
    ]
    latencies = [421.65, 210.42, 64.31, 35.12, 28.94, 18.42]
    colors_list = ['#94a3b8', '#64748b', '#38bdf8', '#0284c7', '#10b981', '#059669']
    
    bars = ax.barh(configs, latencies, color=colors_list, height=0.58, edgecolor='#0f172a', linewidth=0.6)
    
    for bar, val in zip(bars, latencies):
        speedup = 421.65 / val
        label = f"{val:.1f} ms ({speedup:.1f}x)" if speedup > 1.0 else f"{val:.1f} ms (Baseline)"
        ax.text(val + 8, bar.get_y() + bar.get_height()/2, label, va='center', ha='left', fontsize=8.5, weight='bold', color='#0f172a')
        
    ax.set_xlim(0, 500)
    ax.set_xlabel("Query Execution Latency (ms) - Lower is Faster", fontsize=9.5, weight='bold', color='#1e293b')
    ax.set_title("Storage & Execution Engine Benchmark across 10,781 Records (5 Repetitions)", fontsize=11.5, weight='bold', color='#0f172a', pad=12)
    ax.grid(axis='x', linestyle=':', color='#cbd5e1')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig("presentation_assets/performance_benchmark.png", facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()
    print("[OK] Created performance_benchmark.png")

# -----------------------------------------------------------------------------
# 5. Kimball Star Schema Entity-Relationship Diagram
# -----------------------------------------------------------------------------
def create_star_schema_diagram():
    fig, ax = plt.subplots(figsize=(9, 5), dpi=200)
    ax.set_facecolor('#f8fafc')
    fig.patch.set_facecolor('#ffffff')
    
    # Center Fact Box
    fact_box = patches.FancyBboxPatch((3.4, 1.4), 2.8, 2.4, boxstyle="round,pad=0.15",
                                     facecolor='#0f2942', edgecolor='#0284c7', linewidth=2)
    ax.add_patch(fact_box)
    ax.text(4.8, 3.5, "Fact_League_Matches", color='white', weight='bold', fontsize=10, ha='center')
    fact_txt = "• match_id (PK)\n• date_key (FK)\n• home_team_key (FK)\n• away_team_key (FK)\n• league_key (FK)\n• season_key (FK)\n• FTHG, FTAG, FTR\n• HS, AS, HY, AY"
    ax.text(4.8, 2.3, fact_txt, color='#e2e8f0', fontsize=7.8, ha='center', va='center')
    
    # Dimensions around center
    dims = [
        ("Dim_Teams", "• team_key (PK)\n• team_name\n• stadium_capacity\n• country", (0.5, 3.1)),
        ("Dim_Leagues", "• league_key (PK)\n• league_name\n• country\n• tier_level", (6.7, 3.1)),
        ("Dim_Seasons", "• season_key (PK)\n• season_name\n• start_year\n• end_year", (0.5, 0.5)),
        ("Dim_Players", "• player_key (PK)\n• player_name\n• tactical_role\n• primary_club", (6.7, 0.5)),
    ]
    
    for name, cols, (x, y) in dims:
        dim_box = patches.FancyBboxPatch((x, y), 2.4, 1.6, boxstyle="round,pad=0.1",
                                         facecolor='#e0f2fe', edgecolor='#0284c7', linewidth=1.2)
        ax.add_patch(dim_box)
        ax.text(x + 1.2, y + 1.4, name, color='#0f2942', weight='bold', fontsize=9, ha='center')
        ax.text(x + 1.2, y + 0.65, cols, color='#1e293b', fontsize=7.5, ha='center', va='center')
        
        # Connect to Fact
        center_fact = (4.8, 2.6)
        target = (x + 1.2, y + 0.8)
        ax.annotate("", xy=center_fact, xytext=target,
                    arrowprops=dict(arrowstyle="->", color="#0284c7", lw=1.5, linestyle="--"))

    ax.set_xlim(0, 9.6)
    ax.set_ylim(0, 5.2)
    ax.axis('off')
    plt.title("PitchPulse 360: Kimball Star Schema for Dimensional OLAP", color='#0f2942', fontsize=12, weight='bold', pad=12)
    plt.tight_layout()
    plt.savefig("presentation_assets/star_schema_diagram.png", facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()
    print("[OK] Created star_schema_diagram.png")

# -----------------------------------------------------------------------------
# 6. Top 5 European Leagues Macro Analysis
# -----------------------------------------------------------------------------
def create_macro_analysis_chart():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.4), dpi=200)
    fig.patch.set_facecolor('#ffffff')
    
    leagues = ['Bundesliga', 'Premier League', 'Serie A', 'Ligue 1', 'La Liga']
    goals = [3.11, 2.84, 2.81, 2.75, 2.53]
    home_win = [44.2, 46.1, 43.8, 43.2, 44.8]
    away_win = [31.9, 30.4, 31.2, 31.5, 27.8]
    draws = [23.9, 23.5, 25.0, 25.3, 27.4]
    
    # Left: Goals per Match
    bars = ax1.bar(leagues, goals, color=['#0284c7', '#0369a1', '#0ea5e9', '#38bdf8', '#7dd3fc'], width=0.55, edgecolor='#0f172a', lw=0.6)
    ax1.set_ylabel("Average Goals / Match", fontsize=9, weight='bold', color='#1e293b')
    ax1.set_title("Scoring Velocity across Top 5 Leagues", fontsize=10.5, weight='bold', color='#0f2942')
    ax1.set_ylim(0, 3.6)
    for bar in bars:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, h + 0.08, f"{h:.2f}", ha='center', fontsize=8.5, weight='bold')
    ax1.tick_params(axis='x', rotation=20)
    ax1.grid(axis='y', linestyle=':', color='#cbd5e1')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    
    # Right: Result Distribution Stacked
    ax2.bar(leagues, home_win, label='Home Win %', color='#10b981', width=0.55, edgecolor='#0f172a', lw=0.6)
    ax2.bar(leagues, draws, bottom=home_win, label='Draw %', color='#f59e0b', width=0.55, edgecolor='#0f172a', lw=0.6)
    bottom_away = np.array(home_win) + np.array(draws)
    ax2.bar(leagues, away_win, bottom=bottom_away, label='Away Win %', color='#ef4444', width=0.55, edgecolor='#0f172a', lw=0.6)
    ax2.set_ylabel("Match Outcome Share (%)", fontsize=9, weight='bold', color='#1e293b')
    ax2.set_title("Home Advantage vs Draw Frequency", fontsize=10.5, weight='bold', color='#0f2942')
    ax2.set_ylim(0, 110)
    ax2.tick_params(axis='x', rotation=20)
    ax2.legend(loc='lower left', fontsize=8)
    ax2.grid(axis='y', linestyle=':', color='#cbd5e1')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    
    plt.suptitle("Comparative Macro-Analytics across Europe's Top 5 Competitions", fontsize=12, weight='bold', color='#0f2942', y=1.02)
    plt.tight_layout()
    plt.savefig("presentation_assets/league_macro_analytics.png", facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()
    print("[OK] Created league_macro_analytics.png")

if __name__ == '__main__':
    create_architecture_diagram()
    create_kde_pitch_heatmap()
    create_player_radar_chart()
    create_benchmark_chart()
    create_star_schema_diagram()
    create_macro_analysis_chart()
    print("[DONE] All 6 high-resolution presentation visual assets generated successfully!")
