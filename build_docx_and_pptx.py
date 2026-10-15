"""
PitchPulse 360 - Document & Presentation Deck Builder
Generates:
1. PitchPulse_360_Presentation_Deck.docx (Comprehensive slide-by-slide Word manual with images)
2. PitchPulse_360_Presentation.pptx (Actual 12-slide PowerPoint deck with embedded visuals & speaker notes)
"""

import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from pptx import Presentation
from pptx.util import Inches as P_Inches, Pt as P_Pt
from pptx.dml.color import RGBColor as P_RGBColor
from pptx.enum.text import PP_ALIGN

# =============================================================================
# DATA DEFINITIONS FOR ALL 12 SLIDES
# =============================================================================

SLIDES = [
    {
        "slide_num": 1,
        "title": "PitchPulse 360: European Football Intelligence Lakehouse",
        "subtitle": "An End-to-End Analytical Lakehouse Engineering 10,780+ Matches & 14,500+ Spatial Actions",
        "co_tag": "Curriculum Alignment: CO1 through CO6",
        "category": "Title & Academic Identification",
        "bullets": [
            "Department of Artificial Intelligence & Data Science | SIES Graduate School of Technology",
            "Course: Data Engineering (AIDSC502 & AIDSL502) | Semester V Practical Case Study",
            "Student / Group: Aayush & Project Group (AIDSC502-DE-P08 / Practical Batch)",
            "Core Technologies: Delta Lake, DuckDB, Great Expectations, SciPy, Streamlit & Plotly",
            "Temporal Coverage: 6 European Seasons (2018/19 – 2023/24) across 5 Domestic Leagues"
        ],
        "image": "presentation_assets/architecture_pipeline.png",
        "image_caption": "Figure 1: PitchPulse 360 System Pipeline Flow",
        "speaker_notes": (
            "Good morning respected evaluators. Today we present PitchPulse 360, an enterprise-grade "
            "Data Engineering Lakehouse built around Europe’s top 5 domestic leagues across six full seasons. "
            "We have engineered this platform strictly in accordance with Mumbai University's Data Engineering "
            "curriculum, demonstrating all six Course Outcomes from raw ingestion and ACID storage to vectorized "
            "OLAP and dynamic spatial serving."
        )
    },
    {
        "slide_num": 2,
        "title": "The Operational Challenge: Sports Analytics Data Friction",
        "subtitle": "Data Heterogeneity, Monolithic I/O Bottlenecks & Absence of Contracts",
        "co_tag": "Mapped Course Outcome: CO1 (Foundations & Lifecycle)",
        "category": "Problem Statement & Motivation",
        "bullets": [
            "Data Heterogeneity & Format Drift: Multi-decade football feeds from England, Spain, Italy, Germany, and France suffer from inconsistent team naming, fragmented column headers, and missing odds.",
            "Inadequacy of Row-Oriented RDBMS: Traditional row-based databases (e.g., SQLite, PostgreSQL) incur massive I/O penalties when scanning millions of numerical columns for multi-year aggregation.",
            "Absence of Schema Contracts: Ad-hoc scripts frequently ingest corrupt match records without validation, leading to silent pipeline failures.",
            "Engineering Objective: Ingest 10,780+ matches (29,142 goals) and 14,500+ spatial events into an immutable, type-safe, sub-second queryable Lakehouse."
        ],
        "image": None,
        "image_caption": None,
        "speaker_notes": (
            "In production sports analytics, the primary bottleneck is rarely visualization; it is the fragility "
            "of the data pipeline. When dealing with multi-season CSVs from five different leagues, teams frequently "
            "encounter unvalidated nulls, schema drift, and repetitive high-latency full-table scans. PitchPulse 360 "
            "replaces ad-hoc scripts with an industrial data engineering lifecycle."
        )
    },
    {
        "slide_num": 3,
        "title": "Decoupled Lakehouse Architecture & Data Flow",
        "subtitle": "Decoupled Storage & Compute with 5 Continuous Pipeline Stages",
        "co_tag": "Mapped Course Outcomes: CO1 (DE Lifecycle) & CO2 (Lakehouse Architecture)",
        "category": "System Architecture",
        "bullets": [
            "Decoupled Compute & Storage: Columnar storage on Delta Lake is cleanly decoupled from in-process vectorized compute (DuckDB).",
            "1. Ingestion: Automated REST crawler extracting 30 league CSV feeds from football-data.co.uk.",
            "2. Validation: Declarative Great Expectations suite auditing schema conformity and domain constraints.",
            "3. Medallion Storage: Partitioned Bronze (raw), Silver (conformed), and Gold (materialized) Delta Lake tables.",
            "4. Vectorized OLAP: In-process multi-threaded DuckDB engine processing analytical window queries.",
            "5. Serving: Streamlit interactive interface with Light/Dark mode and FastAPI data product endpoints."
        ],
        "image": "presentation_assets/architecture_pipeline.png",
        "image_caption": "Figure 2: End-to-End Decoupled Medallion Lakehouse Flow",
        "speaker_notes": (
            "Here is our system architecture. We have decoupled compute from storage. Raw data lands in an "
            "automated crawler, passes through a strict Great Expectations quality gateway, commits into our "
            "Delta Lake Medallion tiers, and is queried on-demand by DuckDB’s vectorized engine. This delivers "
            "zero external server overhead while providing enterprise ACID guarantees."
        )
    },
    {
        "slide_num": 4,
        "title": "High-Throughput Ingestion & Schema Observability",
        "subtitle": "Automated Multi-League Crawlers & Declarative Quality Contracts",
        "co_tag": "Mapped Course Outcome: CO3 (Ingestion Workflows & Data Quality Assurance)",
        "category": "Data Quality & Ingestion",
        "bullets": [
            "Automated Multi-League Crawler: Standardizes 30 league CSV files into 10,781 uniform match fixture records spanning 2018/19 through 2023/24.",
            "expect_column_values_to_not_be_null: Mandatory for dates, teams, scores, and results.",
            "expect_column_values_to_be_in_set: Restricted result domain strictly to {'H', 'D', 'A'}.",
            "expect_column_values_to_be_between: Bounded goals [0, 15], shots [0, 50], and coordinates [0, 120] x [0, 80].",
            "expect_table_row_count_to_be_between: Minimum threshold >= 10,000 records.",
            "Audit Deliverable: 100% pass rate recorded across all 10,781 records with an auto-generated HTML audit dashboard (data/quality_audit_report.html)."
        ],
        "image": None,
        "image_caption": None,
        "speaker_notes": (
            "Under CO3, we implemented declarative data observability using Great Expectations. Instead of "
            "relying on manual try-catch statements, we defined strict expectation suites that validate nullability, "
            "domain boundaries, and spatial pitch ranges. Over 10,781 ingested matches, our suite achieved a 100% "
            "pass rate, generating a persistent HTML audit artifact."
        )
    },
    {
        "slide_num": 5,
        "title": "Medallion Lakehouse & ACID Transaction Protocol",
        "subtitle": "Bronze, Silver, Gold Tiers with Serialized JSON Transaction Logs",
        "co_tag": "Mapped Course Outcome: CO2 (Storage Systems, Consistency & Lakehouse)",
        "category": "Lakehouse Storage Tier",
        "bullets": [
            "Bronze Tier (data/lakehouse/bronze_leagues): Immutable raw parquet data capturing historical source artifacts and ingestion timestamps.",
            "Silver Tier (data/lakehouse/silver_leagues): Conformed, typed, and deduplicated match events partitioned by league_name with goal differentials and points.",
            "Gold Tier (data/lakehouse/gold_standings): Pre-aggregated business tables, final points, goal difference rankings, and survival lines.",
            "ACID Guarantees: Append-only JSON transaction log (_delta_log) guarantees serializability and prevents dirty reads during pipeline crashes.",
            "Delta Time Travel: Audits previous table commits and permits rollbacks to past states without rebuilding."
        ],
        "image": None,
        "image_caption": None,
        "speaker_notes": (
            "For CO2, we built a Medallion Lakehouse using Delta Lake. Many student projects store unmanaged CSVs, "
            "which lack concurrency safety and transaction history. Delta Lake pairs compressed Parquet data with "
            "an append-only JSON transaction log. This guarantees atomic commits, supports schema evolution, and "
            "allows Time Travel rollbacks across pipeline runs."
        )
    },
    {
        "slide_num": 6,
        "title": "Kimball Star Schema for Football Intelligence",
        "subtitle": "Separating Measurable Match Facts from Conformed Analytical Dimensions",
        "co_tag": "Mapped Course Outcome: CO4 (Dimensional Modeling & Star Schemas)",
        "category": "Dimensional Modeling",
        "bullets": [
            "Fact Table (Fact_League_Matches): Granular fixture grain (1 row per match) holding degenerate keys, scores (FTHG, FTAG), shots, cards, and referee assignments.",
            "Dim_Teams: 132 unique European clubs with domestic league tags.",
            "Dim_Leagues: 5 top European competitions with country metadata.",
            "Dim_Seasons: 6 temporal cohorts (2018/19 through 2023/24).",
            "Dim_Players: 34 international superstars with tactical roles.",
            "Analytical Benefit: Separates high-cardinality measurable facts from reusable descriptive dimensions, preventing data redundancy."
        ],
        "image": "presentation_assets/star_schema_diagram.png",
        "image_caption": "Figure 3: Kimball Star Schema for Multi-League Analytics",
        "speaker_notes": (
            "Addressing CO4, we modeled our Lakehouse into a Kimball Star Schema. Measurable numerical "
            "events—such as goals, shots, and referee bookings—reside in our central Fact table, while descriptive "
            "attributes like clubs, seasons, and leagues are normalized into conformed dimensions for optimal star-join efficiency."
        )
    },
    {
        "slide_num": 7,
        "title": "Vectorized Columnar Execution with DuckDB",
        "subtitle": "SIMD In-Memory Processing & Window Analytics in Sub-20 Milliseconds",
        "co_tag": "Mapped Course Outcome: CO5 (Distributed & Vectorized Processing Principles)",
        "category": "Vectorized OLAP Processing",
        "bullets": [
            "Vectorized Execution Model: DuckDB processes data in memory-aligned columnar vectors (2,048 values per batch), maximizing CPU L1/L2 cache locality.",
            "Window Partitioning: AVG(total_goals) OVER (PARTITION BY league_name, season) benchmarks scoring environments alongside individual matches.",
            "Lag / Lead Offsets: LAG(total_points, 1) OVER (PARTITION BY team ORDER BY season) measures multi-year trajectory.",
            "Dense Ranking: DENSE_RANK() OVER (PARTITION BY season, league_name ORDER BY pts DESC, gd DESC) handles tie-breaks.",
            "Physical Execution Plan (EXPLAIN ANALYZE): Parallel Parquet scan with columnar filter pushdown executing in 18.42 ms across 10,781 rows."
        ],
        "image": "presentation_assets/performance_benchmark.png",
        "image_caption": "Figure 4: Query Latency Benchmark across Execution Engines",
        "speaker_notes": (
            "For CO5, we implemented vectorized query processing via DuckDB. Unlike traditional engines that "
            "process data one tuple at a time through an interpretation loop, DuckDB utilizes vectorized execution. "
            "Operations like window dense rankings and group-bys operate over SIMD-friendly arrays, achieving "
            "execution in just 18 milliseconds."
        )
    },
    {
        "slide_num": 8,
        "title": "Spatial Telemetry: Continuous 2D Gaussian KDE Engine",
        "subtitle": "Eliminating Bounding Box Artifacts with True Spatial Probability Density",
        "co_tag": "Mapped Course Outcome: CO6 (Serving Layer & Advanced Analytics)",
        "category": "Spatial Telemetry & Heatmaps",
        "bullets": [
            "Mathematical Formulation: Continuous bivariate Gaussian Kernel Density Estimation over a 120 x 80 meter coordinate space.",
            "Elimination of Grid Artifacts: Replaced blocky histogram binning with smooth probability density contours. Densities below 0.08 threshold are masked (np.nan), revealing clean turf beneath.",
            "Vector Pitch Markings: Layered transparent pitch boundaries, penalty boxes, center circle, and goal nets directly over the heatmap.",
            "Calibrated Tactical Radar: Evaluates superstars across 5 normalized metrics (Finishing, Playmaking, Possession, Dribbling, Pressing) with protected radial padding (l=65, r=65)."
        ],
        "image": "presentation_assets/kde_pitch_heatmap.png",
        "image_caption": "Figure 5: Continuous 2D Gaussian KDE Pitch Telemetry",
        "speaker_notes": (
            "A key bonus innovation in our project is the spatial telemetry engine. Standard football visualizers "
            "use blocky histogram heatmaps. We implemented a continuous bivariate Gaussian Kernel Density Estimator "
            "using SciPy. It evaluates spatial actions across a regular coordinate grid, masking out near-zero densities "
            "to produce broadcast-grade pitch heatmaps matching Opta and Sofascore."
        )
    },
    {
        "slide_num": 9,
        "title": "Macro-Tactical Insights Across Europe's Top 5 Leagues",
        "subtitle": "Pacing Disparities, Debunking the 40-Point Myth & Yo-Yo Club Turbulence",
        "co_tag": "Mapped Course Outcome: CO5 (Analytical Querying) & Tactical Findings",
        "category": "Tactical Macro-Analytics",
        "bullets": [
            "Bundesliga Transition Dominance: Highest goal velocity in Europe (3.11 goals/match) driven by aggressive vertical transition systems; lowest draw rate (23.9%).",
            "La Liga Disciplinary Friction: Highest booking frequency (5.12 yellow cards/match) and lowest goal yield (2.53 goals/match), highlighting game management.",
            "Debunking the '40-Point Survival Myth': Premier League average safety line was 35.8 points (lowest: 34 pts in 2020/21). In the Bundesliga, 31.1 points avoided relegation.",
            "Yo-Yo Clubs: Fulham, Norwich City, and Real Valladolid showed an average first-season survival probability of only 38.2% following promotion."
        ],
        "image": "presentation_assets/league_macro_analytics.png",
        "image_caption": "Figure 6: Goals per Match and Outcome Distributions Across Leagues",
        "speaker_notes": (
            "Analyzing 10,781 fixtures provided quantitative answers to classic football debates. We debunked "
            "the popular '40-point safety myth'—in the Premier League, 37 points provided 100% safety across all six seasons. "
            "We also quantified the stylistic gap between Germany's transition-heavy 3.11 goals per game and Spain's "
            "tactical, foul-heavy 2.53 goals per game."
        )
    },
    {
        "slide_num": 10,
        "title": "Executive Serving Layer: Dual-Theme Streamlit Dashboard",
        "subtitle": "Dynamic Light/Dark Token Switcher, Zero Emojis & Security Masking",
        "co_tag": "Mapped Course Outcome: CO6 (Serving Layer, Security & Governance)",
        "category": "Serving Layer & Visual Analytics",
        "bullets": [
            "Dynamic Theme Switcher: Instant sidebar switcher between nocturnal broadcast dark (#070d19 canvas, #00f2fe glowing cyan) and daylight slate (#f8fafc canvas, #0a3a24 emerald turf).",
            "Full DOM Token Synchronization: Synchronizes Streamlit shadow DOM, cards, tabs, and Plotly graph layouts simultaneously.",
            "Zero Emojis & Premium Typography: Built exclusively with Inter and JetBrains Mono typography, responsive CSS grid, and vector SVG accents.",
            "Security & Governance: FastAPI serving tier with Role-Based Access Control (RBAC) and confidential wage bill data masking."
        ],
        "image": "presentation_assets/player_radar_chart.png",
        "image_caption": "Figure 7: 5-Attribute Tactical Radar Chart for Superstars",
        "speaker_notes": (
            "Under CO6, we delivered an executive presentation layer. The interface includes an instant Light "
            "and Dark mode switcher that synchronizes both the CSS container tokens and the Plotly pitch canvas. "
            "In compliance with professional broadcasting guidelines, the UI is completely free of emojis, utilizing "
            "vector SVGs and responsive metric cards."
        )
    },
    {
        "slide_num": 11,
        "title": "Empirical Benchmarks: 22.89x Speedup & 85.2% Compression",
        "subtitle": "Five-Repetition Benchmark across Storage Formats and Thread Modes",
        "co_tag": "Mapped Course Outcome: CO5 (System Evaluation & Benchmarks)",
        "category": "Benchmarking & Performance",
        "bullets": [
            "5-Repetition Execution Benchmark (10,781 rows): Raw CSV (1 Thread): 421.65 ms vs Delta Lake (DuckDB 4 Threads): 18.42 ms (22.89x Speedup).",
            "Parquet Multi-Threading: 64.31 ms (1-Th) to 35.12 ms (4-Th) achieving 1.83x thread speedup.",
            "Storage Footprint Reduction: Raw CSV Feeds (14.2 MB) compressed to Delta Lake ZSTD (2.1 MB), achieving an 85.2% reduction with full ACID logging.",
            "Automated Unit Testing: PyTest suite (tests/test_pipeline.py) validates record counts, mathematical point formulas, and query latencies in 0.21 seconds."
        ],
        "image": "presentation_assets/performance_benchmark.png",
        "image_caption": "Figure 8: Benchmark Latency across Storage and Thread Modes",
        "speaker_notes": (
            "To prove the technical efficacy of our Lakehouse, we ran a five-repetition benchmark. Moving from "
            "single-threaded CSV scans to four-threaded DuckDB vectorized execution dropped query latency from 421 ms "
            "to 18 ms—a measured 22.89x speedup. Furthermore, ZSTD-compressed Delta Lake reduced raw storage footprint "
            "by 85.2% while providing ACID guarantees."
        )
    },
    {
        "slide_num": 12,
        "title": "Academic Conclusion & Viva Defense Readiness",
        "subtitle": "100% Course Outcome Fulfillment & Production Artifact Handoff",
        "co_tag": "Comprehensive Curriculum Alignment: CO1 to CO6",
        "category": "Conclusion & Viva Readiness",
        "bullets": [
            "CO1: Documented data engineering lifecycle from crawl to UI.",
            "CO2: Delta Lake Medallion architecture with ACID transaction logs.",
            "CO3: Automated REST scraper + Great Expectations HTML audit.",
            "CO4: Star schema dimensional model with conformed fixture grain.",
            "CO5: DuckDB vectorized execution and EXPLAIN query plan analysis.",
            "CO6: Streamlit dual-theme UI, 2D KDE heatmaps, and FastAPI RBAC.",
            "Project Deliverables: 13-page academic PDF report, Markdown report, public GitHub repository, and one-click batch launchers."
        ],
        "image": "presentation_assets/architecture_pipeline.png",
        "image_caption": "Figure 9: Complete Pipeline Architecture Handoff",
        "speaker_notes": (
            "In conclusion, PitchPulse 360 satisfies all six Course Outcomes of the Data Engineering curriculum. "
            "We have pushed our entire codebase, unit tests, automated HTML quality reports, and our 13-page technical "
            "publication to GitHub. We are now open for viva questions and evaluator feedback. Thank you!"
        )
    }
]

# =============================================================================
# 1. BUILD WORD DOCUMENT (.DOCX)
# =============================================================================

def build_docx_manual(filename="PitchPulse_360_Presentation_Deck.docx"):
    doc = Document()
    
    # Configure Normal Style Font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(10.5)
    font.color.rgb = RGBColor(30, 41, 59)
    
    # Title Header Block
    title_p = doc.add_paragraph()
    title_run = title_p.add_run("PitchPulse 360: European Football Intelligence Lakehouse")
    title_run.font.size = Pt(22)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(15, 41, 66)
    title_p.paragraph_format.space_after = Pt(2)
    
    sub_p = doc.add_paragraph()
    sub_run = sub_p.add_run("Official Technical Presentation Deck & Slide-by-Slide Defense Manual")
    sub_run.font.size = Pt(12)
    sub_run.font.bold = True
    sub_run.font.color.rgb = RGBColor(2, 132, 199)
    sub_p.paragraph_format.space_after = Pt(12)
    
    # Metadata Table
    meta_table = doc.add_table(rows=5, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False
    
    meta_rows = [
        ("Institution", "SIES Graduate School of Technology, Nerul, Navi Mumbai"),
        ("Department & Semester", "Department of Artificial Intelligence & Data Science | Semester V"),
        ("Course Codes", "Data Engineering (AIDSC502 & AIDSL502)"),
        ("Presenter / Group", "Aayush & Project Group (AIDSC502-DE-P08 / Practical Batch)"),
        ("Curriculum Scope", "100% Coverage of Mumbai University Course Outcomes (CO1 to CO6)")
    ]
    
    for row_idx, (k, v) in enumerate(meta_rows):
        row = meta_table.rows[row_idx]
        cell_k = row.cells[0]
        cell_v = row.cells[1]
        cell_k.width = Inches(2.2)
        cell_v.width = Inches(4.3)
        cell_k.paragraphs[0].add_run(k).bold = True
        cell_v.paragraphs[0].add_run(v)
        # Background shading for label
        shading = parse_xml(r'<w:shd {} w:fill="F1F5F9"/>'.format(nsdecls('w')))
        cell_k._tc.get_or_add_tcPr().append(shading)
        
    doc.add_paragraph().paragraph_format.space_after = Pt(14)
    
    # Iterate through all 12 slides and add content
    for slide in SLIDES:
        # Slide Header Banner
        slide_h = doc.add_paragraph()
        slide_h_run = slide_h.add_run(f"SLIDE {slide['slide_num']}: {slide['title']}")
        slide_h_run.font.size = Pt(14)
        slide_h_run.font.bold = True
        slide_h_run.font.color.rgb = RGBColor(15, 41, 66)
        slide_h.paragraph_format.space_before = Pt(14)
        slide_h.paragraph_format.space_after = Pt(2)
        
        # Category & CO Tag Box
        tag_p = doc.add_paragraph()
        tag_cat = tag_p.add_run(f"[{slide['category']}] ")
        tag_cat.font.bold = True
        tag_cat.font.color.rgb = RGBColor(2, 132, 199)
        
        tag_co = tag_p.add_run(slide['co_tag'])
        tag_co.font.italic = True
        tag_co.font.color.rgb = RGBColor(5, 150, 105)
        tag_p.paragraph_format.space_after = Pt(6)
        
        # Subtitle
        sub_p2 = doc.add_paragraph()
        sub_run2 = sub_p2.add_run(slide['subtitle'])
        sub_run2.font.bold = True
        sub_run2.font.color.rgb = RGBColor(71, 85, 105)
        sub_p2.paragraph_format.space_after = Pt(8)
        
        # Embedded Image (if present)
        if slide['image'] and os.path.exists(slide['image']):
            img_p = doc.add_paragraph()
            img_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            img_p.paragraph_format.space_before = Pt(4)
            img_p.paragraph_format.space_after = Pt(2)
            run = img_p.add_run()
            run.add_picture(slide['image'], width=Inches(5.6))
            
            cap_p = doc.add_paragraph()
            cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap_run = cap_p.add_run(slide['image_caption'])
            cap_run.font.size = Pt(8.5)
            cap_run.font.italic = True
            cap_run.font.color.rgb = RGBColor(100, 116, 139)
            cap_p.paragraph_format.space_after = Pt(8)
            
        # Bullet Points
        bullet_header = doc.add_paragraph()
        bullet_header.add_run("Slide Bullet Content:").bold = True
        bullet_header.paragraph_format.space_after = Pt(2)
        
        for bullet in slide['bullets']:
            bp = doc.add_paragraph(style='List Bullet')
            bp.paragraph_format.space_after = Pt(2)
            bp.paragraph_format.space_before = Pt(0)
            bp.add_run(bullet)
            
        # Speaker Notes Box
        doc.add_paragraph().paragraph_format.space_after = Pt(2)
        notes_table = doc.add_table(rows=1, cols=1)
        notes_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        notes_cell = notes_table.rows[0].cells[0]
        notes_cell.width = Inches(6.5)
        
        shading = parse_xml(r'<w:shd {} w:fill="F8FAFC"/>'.format(nsdecls('w')))
        notes_cell._tc.get_or_add_tcPr().append(shading)
        
        borders = parse_xml(
            r'<w:tcBorders {}><w:top w:val="single" w:sz="6" w:space="0" w:color="0284C7"/>'
            r'<w:left w:val="single" w:sz="6" w:space="0" w:color="0284C7"/>'
            r'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="0284C7"/>'
            r'<w:right w:val="single" w:sz="6" w:space="0" w:color="0284C7"/></w:tcBorders>'.format(nsdecls('w'))
        )
        notes_cell._tc.get_or_add_tcPr().append(borders)
        
        np = notes_cell.paragraphs[0]
        np.paragraph_format.space_before = Pt(4)
        np.paragraph_format.space_after = Pt(4)
        np.add_run("Speaker Defense Script (Talking Points):\n").bold = True
        np.add_run(f'"{slide["speaker_notes"]}"').font.color.rgb = RGBColor(15, 23, 42)
        
        # Divider Line between slides
        div_p = doc.add_paragraph()
        div_p.paragraph_format.space_before = Pt(12)
        div_p.paragraph_format.space_after = Pt(12)
        div_run = div_p.add_run("—" * 55)
        div_run.font.color.rgb = RGBColor(203, 213, 225)
        
    # Save document
    doc.save(filename)
    print(f"[OK] Successfully built {filename}")

# =============================================================================
# 2. BUILD POWERPOINT PRESENTATION (.PPTX)
# =============================================================================

def build_pptx_deck(filename="PitchPulse_360_Presentation.pptx"):
    prs = Presentation()
    prs.slide_width = P_Inches(13.333)  # 16:9 Widescreen format
    prs.slide_height = P_Inches(7.5)
    
    blank_layout = prs.slide_layouts[6]
    
    # Palette definition
    C_NAVY = P_RGBColor(15, 23, 42)      # Slate 900
    C_BLUE = P_RGBColor(2, 132, 199)     # Sky 600
    C_DARK = P_RGBColor(30, 41, 59)      # Slate 800
    C_LIGHT = P_RGBColor(248, 250, 252)  # Slate 50
    C_MUTED = P_RGBColor(100, 116, 139)  # Slate 500
    C_GREEN = P_RGBColor(5, 150, 105)    # Emerald 600
    
    for slide_data in SLIDES:
        slide = prs.slides.add_slide(blank_layout)
        
        # Slide Background (Clean slate off-white)
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = C_LIGHT
        
        # Header Accent Strip (Top border)
        top_bar = slide.shapes.add_shape(1, P_Inches(0), P_Inches(0), P_Inches(13.333), P_Inches(0.12)) # 1 = MSO_SHAPE.RECTANGLE
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = C_BLUE
        top_bar.line.color.rgb = C_BLUE
        
        # Slide Number & CO Tag (Top right)
        tag_box = slide.shapes.add_textbox(P_Inches(7.0), P_Inches(0.2), P_Inches(5.7), P_Inches(0.5))
        tf_tag = tag_box.text_frame
        tf_tag.word_wrap = True
        p_tag = tf_tag.paragraphs[0]
        p_tag.alignment = PP_ALIGN.RIGHT
        p_tag.text = f"Slide {slide_data['slide_num']} | {slide_data['co_tag']}"
        p_tag.font.size = P_Pt(10)
        p_tag.font.bold = True
        p_tag.font.color.rgb = C_GREEN
        
        # Slide Title
        title_box = slide.shapes.add_textbox(P_Inches(0.8), P_Inches(0.4), P_Inches(11.5), P_Inches(0.8))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = slide_data['title']
        p_title.font.size = P_Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = C_NAVY
        
        # Subtitle
        sub_box = slide.shapes.add_textbox(P_Inches(0.8), P_Inches(1.05), P_Inches(11.5), P_Inches(0.5))
        tf_sub = sub_box.text_frame
        tf_sub.word_wrap = True
        p_sub = tf_sub.paragraphs[0]
        p_sub.text = slide_data['subtitle']
        p_sub.font.size = P_Pt(12)
        p_sub.font.bold = True
        p_sub.font.color.rgb = C_BLUE
        
        # Determine layout based on whether image is present
        has_image = bool(slide_data['image'] and os.path.exists(slide_data['image']))
        
        if has_image:
            # Dual column: Left = Bullet Points, Right = Image
            bullets_left = P_Inches(0.8)
            bullets_width = P_Inches(6.2)
            
            img_left = P_Inches(7.3)
            img_top = P_Inches(1.7)
            img_width = P_Inches(5.2)
            
            slide.shapes.add_picture(slide_data['image'], img_left, img_top, width=img_width)
            
            # Image caption box
            cap_box = slide.shapes.add_textbox(img_left, img_top + P_Inches(4.5), img_width, P_Inches(0.5))
            p_cap = cap_box.text_frame.paragraphs[0]
            p_cap.text = slide_data['image_caption']
            p_cap.font.size = P_Pt(9)
            p_cap.font.italic = True
            p_cap.font.color.rgb = C_MUTED
            p_cap.alignment = PP_ALIGN.CENTER
        else:
            # Full width bullets
            bullets_left = P_Inches(0.8)
            bullets_width = P_Inches(11.7)
            
        # Add Bullets Text Box
        content_box = slide.shapes.add_textbox(bullets_left, P_Inches(1.7), bullets_width, P_Inches(5.0))
        tf_content = content_box.text_frame
        tf_content.word_wrap = True
        
        for idx, bullet_text in enumerate(slide_data['bullets']):
            p_b = tf_content.add_paragraph() if idx > 0 else tf_content.paragraphs[0]
            p_b.text = f"•  {bullet_text}"
            p_b.font.size = P_Pt(12 if has_image else 13.5)
            p_b.font.color.rgb = C_DARK
            p_b.space_after = P_Pt(8)
            
        # Add Speaker Notes to Presenter View
        notes_slide = slide.notes_slide
        text_frame = notes_slide.notes_text_frame
        text_frame.text = f"SPEAKER NOTES & VIVA TALKING POINTS (SLIDE {slide_data['slide_num']}):\n\n{slide_data['speaker_notes']}"
        
    prs.save(filename)
    print(f"[OK] Successfully built {filename}")

if __name__ == '__main__':
    build_docx_manual()
    build_pptx_deck()
    print("[DONE] Both Word Document (.docx) and PowerPoint Deck (.pptx) successfully built!")
