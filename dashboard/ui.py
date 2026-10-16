"""Shared presentation layer. Native Streamlit remains the theme authority."""
from html import escape
import streamlit as st


def apply_theme():
    st.markdown('''<style>
    .stApp {
        --pp-accent: color-mix(in srgb, #11936b 85%, currentColor);
        --pp-border: color-mix(in srgb, currentColor 12%, transparent);
        --pp-muted: color-mix(in srgb, currentColor 70%, transparent);
        --pp-surface: color-mix(in srgb, currentColor 2.5%, transparent);
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .stMainBlockContainer {
        max-width: 1600px; padding: 2.8rem 2.2rem 4rem;
    }
    [data-testid="stHeader"] { background: transparent; height: 2.6rem; }
    [data-testid="stAppDeployButton"] { display: none; }
    [data-testid="stToolbar"] { opacity: .7; }
    h1, h2, h3, h4 { letter-spacing: -.035em; }
    h3 { font-size: 1.35rem !important; font-weight: 700 !important; }
    h4 { font-size: 1.05rem !important; }
    [data-testid="stSidebar"] { border-right: 1px solid var(--pp-border); }
    [data-testid="stSidebarUserContent"] { padding-top: 1.25rem; }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: .8rem; }
    [data-testid="stSidebar"] [data-testid="stPageLink"] a {
        padding: .8rem .9rem; border-radius: 10px; font-size: .9rem;
    }
    [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
        background: rgba(17,147,107,.09);
    }
    [data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] {
        color: var(--pp-accent); background: rgba(17,147,107,.1);
    }
    .st-key-nav-current [data-testid="stPageLink"] a {
        color: var(--pp-accent) !important; background: rgba(17,147,107,.1) !important;
    }
    .st-key-nav-current [data-testid="stPageLink"] a p,
    .st-key-nav-current [data-testid="stPageLink"] a span { color: inherit; }
    [data-testid="stPageLink"] a:focus-visible { outline: 2px solid #11936b; outline-offset: 2px; }
    .pp-brand { display: flex; align-items: center; gap: 11px; margin: 0 0 24px; }
    .pp-monogram {
        display: grid; place-items: center; width: 39px; height: 43px;
        border-radius: 12px 12px 17px 17px; background: #114b39;
        color: #d6f4ad; font-size: 20px; font-weight: 800;
    }
    .pp-brand-name { font-weight: 750; letter-spacing: -.04em; font-size: 1.2rem; line-height: 1.1; }
    .pp-brand-name span { color: var(--pp-accent); }
    .pp-brand-sub { margin-top: 4px; font-size: .64rem; letter-spacing: .13em; text-transform: uppercase; color: var(--pp-muted); }
    .pp-sidebar-label { font-size: .65rem; font-weight: 750; letter-spacing: .13em; color: var(--pp-muted); margin: 22px 0 2px; text-transform: uppercase; }
    .pp-sidebar-note { border-top: 1px solid var(--pp-border); padding-top: 17px; margin-top: 15px; font-size: .8rem; line-height: 1.7; color: var(--pp-muted); }
    .pp-sidebar-note strong { color: inherit; font-weight: 650; }
    .pp-topbar { display: flex; justify-content: space-between; align-items: center; gap: 16px; padding: 1px 0 20px; }
    .pp-topbar-label { font-weight: 650; font-size: .85rem; }
    .pp-topbar-meta { font-size: .72rem; color: var(--pp-muted); }
    .pp-topbar-meta::before { content: ''; display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #b39a52; margin-right: 7px; vertical-align: middle; }
    .pp-hero {
        position: relative; overflow: hidden; isolation: isolate;
        border-radius: 20px; min-height: 274px;
        padding: 30px 34px; margin-bottom: 4px;
        color: #f3f7f4; background-color: #0a251c;
        background-image: linear-gradient(90deg, rgba(4,24,17,.35), rgba(4,24,17,.04)), url('/app/static/stadium.png');
        background-size: cover; background-position: center 74%;
    }
    .pp-eyebrow { color: #d4efbe; font-size: .63rem; letter-spacing: .17em; font-weight: 700; margin-bottom: 14px; }
    .pp-hero h1 { color: #fff !important; font-size: clamp(2rem, 3.2vw, 3.5rem) !important; font-weight: 730; line-height: 1.1; margin: 0; padding: 0; max-width: 76%; }
    .pp-hero-season { font-size: 1.45rem; font-weight: 450; color: #e2ebe4; margin-top: 7px; letter-spacing: -.02em; }
    .pp-hero-description { color: #d1ddd4; font-size: .85rem; line-height: 1.6; max-width: 420px; margin: 15px 0 19px; }
    .pp-hero-foot { display: inline-flex; align-items: center; gap: 10px; font-size: .68rem; color: #e1ece4; letter-spacing: .03em; }
    .pp-hero-foot span + span { border-left: 1px solid #5a7367; padding-left: 10px; }
    .pp-section-eyebrow { margin: 10px 0 1px; font-size: .64rem; letter-spacing: .14em; font-weight: 700; color: var(--pp-muted); text-transform: uppercase; }
    .metric-card {
        border: 1px solid var(--pp-border); border-radius: 14px;
        background: var(--pp-surface); color: inherit;
        padding: 19px 20px 17px; min-height: 135px;
        transition: border-color .18s ease, transform .18s ease;
    }
    .metric-card:hover { border-color: #11936b; transform: translateY(-2px); }
    .metric-title { font-size: .65rem; text-transform: uppercase; font-weight: 650; letter-spacing: .09em; color: var(--pp-muted); }
    .metric-val { font-family: inherit; font-variant-numeric: tabular-nums; font-size: 2rem; font-weight: 730; line-height: 1.2; letter-spacing: -.055em; margin-top: 9px; overflow-wrap: anywhere; }
    .metric-card--club .metric-val { font-size: 1.5rem; line-height: 1.6; }
    .metric-card--club { border-top: 3px solid #c5a653; padding-top: 17px; }
    .metric-sub { font-size: .72rem; color: var(--pp-muted); margin-top: 8px; line-height: 1.45; }
    .st-key-overview-metrics [data-testid="stHorizontalBlock"] { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 14px; }
    .st-key-overview-metrics [data-testid="stColumn"] { width: 100% !important; min-width: 0 !important; min-height: 135px; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 23px; border-bottom: 1px solid var(--pp-border); padding: 7px 0 0; background: transparent;
    }
    .stTabs [data-baseweb="tab"] { padding: 8px 1px 17px; height: auto; font-weight: 600; font-size: .85rem; color: var(--pp-muted); white-space: nowrap; }
    .stTabs [aria-selected="true"] { color: var(--pp-accent) !important; }
    .stTabs [data-baseweb="tab-highlight"] { background-color: var(--pp-accent); height: 3px; border-radius: 4px; }
    .stTabs [role="tabpanel"] { padding-top: 17px; }
    [data-baseweb="select"] > div { border-radius: 10px; border-color: var(--pp-border); font-size: .86rem; }
    [data-baseweb="select"] > div:focus-within { border-color: #11936b; }
    [data-testid="stPlotlyChart"] { border: 1px solid var(--pp-border); border-radius: 14px; overflow: hidden; padding: 8px; }
    [data-testid="stDataFrame"] { border-radius: 12px; }
    [data-testid="stMetric"] { border: 1px solid var(--pp-border); border-radius: 14px; padding: 17px 20px; background: var(--pp-surface); }
    [data-testid="stButton"] button, [data-testid="stLinkButton"] a { border-radius: 9px; border-color: var(--pp-border); font-size: .8rem; }
    .pp-legend { display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 10px; font-size: .69rem; color: var(--pp-muted); }
    .pp-legend span::before { content: ''; display: inline-block; width: 7px; height: 7px; margin-right: 5px; border-radius: 2px; background: var(--swatch); }
    .pp-footer { border-top: 1px solid var(--pp-border); margin-top: 35px; padding-top: 18px; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 9px; color: var(--pp-muted); font-size: .7rem; }
    @media (max-width: 1200px) {
        .stMainBlockContainer { padding-left: 1.5rem; padding-right: 1.5rem; }
        .st-key-standings-grid [data-testid="stHorizontalBlock"] { flex-direction: column; }
        .st-key-standings-grid [data-testid="stColumn"] { width: 100% !important; flex: 1 1 auto !important; }
        .st-key-overview-metrics [data-testid="stHorizontalBlock"] { grid-template-columns: repeat(2,minmax(0,1fr)); }
    }
    @media (max-width: 640px) {
        .stMainBlockContainer { padding: 2.8rem 1rem 2rem; }
        .pp-hero { padding: 24px; min-height: 270px; border-radius: 14px; }
        .pp-hero h1 { max-width: 100%; font-size: 2rem !important; }
        .pp-hero-description { max-width: 75%; }
        .pp-topbar-meta { font-size: .63rem; }
        .metric-card { padding: 15px; min-height: 126px; }
        .metric-val { font-size: 1.7rem; }
        .stTabs [data-baseweb="tab-list"] { gap: 19px; }
    }
    @media (prefers-reduced-motion: reduce) { .metric-card { transition: none; } .metric-card:hover { transform: none; } }
    </style>''', unsafe_allow_html=True)


def sidebar(active='football'):
    st.sidebar.markdown('''<div class="pp-brand"><div class="pp-monogram">P</div><div><div class="pp-brand-name">PitchPulse<span>360</span></div><div class="pp-brand-sub">The football archive</div></div></div>''',unsafe_allow_html=True)
    st.sidebar.markdown('<div class="pp-sidebar-label">Football overview</div>',unsafe_allow_html=True)



def sidebar_footer():
    st.sidebar.markdown('''<div class="pp-sidebar-note"><strong>Five leagues. Six seasons.</strong><br/>Historical results from 2018/19 to 2023/24.<br/>No live match feed.</div>''',unsafe_allow_html=True)
    with st.sidebar.expander('Appearance'):
        st.caption('Open the top-right menu, select Settings, then Theme. Choose Light, Dark or your system setting.')


def topbar(label='Football overview'):
    st.markdown(f'<div class="pp-topbar"><span class="pp-topbar-label">{escape(label)}</span><span class="pp-topbar-meta">Historical archive &nbsp; / &nbsp; 2018-2024</span></div>',unsafe_allow_html=True)


def hero(league,season,fixtures):
    short=season[:4]+' / '+season[-2:]
    st.markdown(f'''<section class="pp-hero"><div class="pp-eyebrow">EUROPEAN FOOTBALL, EXPLORED</div><h1>{escape(league)}</h1><div class="pp-hero-season">{escape(short)} season</div><p class="pp-hero-description">Compare teams, explore results and see how the season played out.</p><div class="pp-hero-foot"><span>{fixtures:,} fixtures in this edition</span><span>5 competitions in the archive</span></div></section>''',unsafe_allow_html=True)


def metric_card(label,value,detail,club=False):
    cls='metric-card metric-card--club' if club else 'metric-card'
    st.markdown(f'<div class="{cls}"><div class="metric-title">{escape(str(label))}</div><div class="metric-val">{escape(str(value))}</div><div class="metric-sub">{escape(str(detail))}</div></div>',unsafe_allow_html=True)


def chart(fig,**kwargs):
    fig.update_layout(font=dict(family='Segoe UI, Arial, sans-serif',size=13),title_font_size=16)
    st.plotly_chart(fig,use_container_width=True,config={'displaylogo':False,'displayModeBar':'hover'},**kwargs)


def footer():
    st.markdown('<div class="pp-footer"><span>PitchPulse360 &nbsp; / &nbsp; European football analytics</span><span>Historical results. Clearly labeled demonstrations.</span></div>',unsafe_allow_html=True)
