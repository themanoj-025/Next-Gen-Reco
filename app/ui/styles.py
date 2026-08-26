"""CSS injection module — dark/light theme support via CSS custom properties."""

import streamlit as st


def inject_css(theme="dark") -> None:
    """Inject all custom CSS into the app.

    Parameters
    ----------
    theme : str
        Either "dark" or "light" — determines which set of CSS custom
        properties are injected at the .stApp level so the entire app
        (nav, sidebar, main content, footer) picks up the theme.
    """
    # ── CSS custom property values for each theme ──
    dark_vars = """
        --bg-app: linear-gradient(135deg, #0f0c29 0%, #1a1a3e 50%, #24243e 100%);
        --bg-card: linear-gradient(145deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
        --bg-card-hover: rgba(255,255,255,0.08);
        --bg-card-ghost: linear-gradient(145deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02));
        --bg-sidebar: rgba(255,255,255,0.03);
        --text-primary: #ffffff;
        --text-secondary: rgba(255,255,255,0.6);
        --text-muted: rgba(255,255,255,0.35);
        --text-muted-2: rgba(255,255,255,0.25);
        --text-muted-3: rgba(255,255,255,0.15);
        --border-color: rgba(255,255,255,0.08);
        --border-subtle: rgba(255,255,255,0.06);
        --border-hover: rgba(247,151,30,0.3);
        --accent: #f5c518;
        --accent-gradient: linear-gradient(135deg, #f7971e, #ffd200);
        --star-color: #fbbf24;
        --star-empty: rgba(255,255,255,0.15);
        --footer-text: rgba(255,255,255,0.25);
        --card-shadow: rgba(0,0,0,0.2);
        --scrollbar-bg: rgba(255,255,255,0.05);
        --scrollbar-thumb: rgba(255,255,255,0.15);
        --hero-overlay: linear-gradient(transparent, rgba(0,0,0,0.8));
        --btn-primary-bg: var(--accent-gradient);
        --btn-primary-text: #1a1a2e;
        --btn-secondary-bg: rgba(255,255,255,0.04);
        --btn-secondary-text: rgba(255,255,255,0.7);
        --tab-bg: rgba(255,255,255,0.04);
        --tab-text: rgba(255,255,255,0.5);
        --hover-glow: rgba(247,151,30,0.08);
        --genre-chip-bg: rgba(255,255,255,0.08);
        --genre-chip-text: rgba(255,255,255,0.7);
        --about-bg: rgba(255,255,255,0.03);
        --about-text: rgba(255,255,255,0.65);
        --sidebar-hr: rgba(255,255,255,0.1);
    """

    light_vars = """
        --bg-app: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 50%, #e2e8f0 100%);
        --bg-card: linear-gradient(145deg, rgba(255,255,255,0.95), rgba(255,255,255,0.85));
        --bg-card-hover: #ffffff;
        --bg-card-ghost: linear-gradient(145deg, rgba(255,255,255,0.95), rgba(255,255,255,0.85));
        --bg-sidebar: rgba(0,0,0,0.02);
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --text-muted: #94a3b8;
        --text-muted-2: rgba(0,0,0,0.25);
        --text-muted-3: rgba(0,0,0,0.12);
        --border-color: rgba(0,0,0,0.08);
        --border-subtle: rgba(0,0,0,0.05);
        --border-hover: rgba(247,151,30,0.35);
        --accent: #f5c518;
        --accent-gradient: linear-gradient(135deg, #f7971e, #ffd200);
        --star-color: #eab308;
        --star-empty: rgba(0,0,0,0.1);
        --footer-text: rgba(0,0,0,0.25);
        --card-shadow: rgba(0,0,0,0.08);
        --scrollbar-bg: rgba(0,0,0,0.03);
        --scrollbar-thumb: rgba(0,0,0,0.1);
        --hero-overlay: linear-gradient(transparent, rgba(0,0,0,0.5));
        --btn-primary-bg: var(--accent-gradient);
        --btn-primary-text: #1a1a2e;
        --btn-secondary-bg: rgba(0,0,0,0.04);
        --btn-secondary-text: #475569;
        --tab-bg: rgba(0,0,0,0.04);
        --tab-text: rgba(0,0,0,0.5);
        --hover-glow: rgba(247,151,30,0.1);
        --genre-chip-bg: rgba(0,0,0,0.06);
        --genre-chip-text: rgba(0,0,0,0.6);
        --about-bg: rgba(0,0,0,0.02);
        --about-text: rgba(0,0,0,0.5);
        --sidebar-hr: rgba(0,0,0,0.08);
    """

    active_vars = dark_vars if theme == "dark" else light_vars

    # Also keep class-based vars for the wrapper div as fallback
    dark_class_vars = dark_vars
    light_class_vars = light_vars

    st.markdown(
        f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    * {{ font-family: 'Inter', -apple-system, sans-serif; }}

    /* ═══════════════════════════════════════════════════════════════
       THEME VARIABLES — injected at .stApp level so nav/sidebar/footer
       all receive the active theme
       ═══════════════════════════════════════════════════════════════ */

    .stApp {{
        {active_vars}
        transition: background 0.35s ease;
    }}

    /* Class-based variables for wrapper div redundancy */
    .theme-dark {{
        {dark_class_vars}
    }}

    .theme-light {{
        {light_class_vars}
    }}

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: var(--scrollbar-bg); }}
    ::-webkit-scrollbar-thumb {{ background: var(--scrollbar-thumb); border-radius: 999px; }}

    /* ── Header / Nav Bar ── */
    .imdb-nav {{
        background: var(--bg-card);
        border-bottom: 1px solid var(--border-color);
        backdrop-filter: blur(12px);
        padding: 0.5rem 1.5rem;
        display: flex;
        align-items: center;
        gap: 1.5rem;
        margin: -0.5rem -0.5rem 0 -0.5rem;
        transition: background 0.35s ease, border-color 0.35s ease;
    }}

    .imdb-nav-logo {{ font-size: 1.2rem; font-weight: 800; color: var(--accent); white-space: nowrap; }}
    .imdb-nav-logo span {{ font-weight: 300; color: var(--text-muted); font-size: 0.85rem; transition: color 0.35s ease; }}

    .imdb-nav-links {{ display: flex; gap: 0.8rem; flex-wrap: wrap; }}

    .imdb-nav-link {{
        color: var(--text-muted);
        font-size: 0.78rem;
        font-weight: 500;
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
        cursor: default;
        transition: color 0.2s;
    }}

    .imdb-nav-link.active {{ color: var(--accent); }}
    .imdb-nav-link:not(.active):hover {{ color: var(--text-secondary); }}

    .imdb-nav-right {{ margin-left: auto; }}
    .imdb-nav-user {{ color: var(--text-muted); font-size: 0.78rem; font-weight: 400; transition: color 0.35s ease; }}

    .app-header {{ text-align: center; padding: 2rem 0 1rem 0; }}

    .app-header h1 {{
        font-size: 3rem;
        font-weight: 800;
        background: var(--accent-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -1px;
        margin: 0;
    }}

    .app-header p {{ color: var(--text-secondary); font-size: 1.05rem; font-weight: 300; margin-top: 0.3rem; transition: color 0.35s ease; }}

    /* ── Movie Card ── */
    .movie-card {{
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 1.8rem 2rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease, background 0.35s ease, border-color 0.35s ease;
    }}

    .movie-card:hover {{
        border-color: var(--border-hover);
        box-shadow: 0 8px 32px rgba(247,151,30,0.08);
    }}

    .movie-title {{ font-size: 2rem; font-weight: 700; color: var(--text-primary); margin: 0 0 0.3rem 0; line-height: 1.2; transition: color 0.35s ease; }}
    .movie-year {{ color: var(--text-muted); font-size: 1.1rem; font-weight: 300; transition: color 0.35s ease; }}

    /* ── Genre Chips ── */
    .genre-chip {{
        display: inline-block;
        padding: 0.25rem 0.85rem;
        margin: 0.2rem 0.3rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        letter-spacing: 0.3px;
        border: 1px solid;
    }}

    .genre-chip.action    {{ background: rgba(239,68,68,0.15); border-color: rgba(239,68,68,0.4); color: #fca5a5; }}
    .genre-chip.adventure {{ background: rgba(251,146,60,0.15); border-color: rgba(251,146,60,0.4); color: #fdba74; }}
    .genre-chip.comedy    {{ background: rgba(250,204,21,0.15); border-color: rgba(250,204,21,0.4); color: #fde68a; }}
    .genre-chip.drama     {{ background: rgba(96,165,250,0.15); border-color: rgba(96,165,250,0.4); color: #93c5fd; }}
    .genre-chip.horror    {{ background: rgba(167,139,250,0.15); border-color: rgba(167,139,250,0.4); color: #c4b5fd; }}
    .genre-chip.scifi     {{ background: rgba(34,211,238,0.15); border-color: rgba(34,211,238,0.4); color: #67e8f9; }}
    .genre-chip.romance   {{ background: rgba(244,114,182,0.15); border-color: rgba(244,114,182,0.4); color: #f9a8d4; }}
    .genre-chip.thriller  {{ background: rgba(148,163,184,0.15); border-color: rgba(148,163,184,0.4); color: #cbd5e1; }}
    .genre-chip.documentary {{ background: rgba(52,211,153,0.15); border-color: rgba(52,211,153,0.4); color: #6ee7b7; }}
    .genre-chip.default   {{ background: var(--genre-chip-bg); border-color: var(--border-color); color: var(--genre-chip-text); transition: color 0.35s ease, background 0.35s ease, border-color 0.35s ease; }}

    /* ── Similar Movie Cards (legacy) ── */
    .sim-card {{
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 1.2rem 1.2rem 1rem;
        cursor: pointer;
        transition: all 0.3s ease, background 0.35s ease, border-color 0.35s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
    }}

    .sim-card:hover {{
        border-color: var(--border-hover);
        transform: translateY(-3px);
        box-shadow: 0 12px 40px rgba(247,151,30,0.12);
    }}

    .sim-card-title {{ font-size: 0.95rem; font-weight: 600; color: var(--text-primary); margin: 0 0 0.2rem 0; line-height: 1.3; transition: color 0.35s ease; }}
    .sim-card-year {{ color: var(--text-muted); font-size: 0.8rem; font-weight: 300; transition: color 0.35s ease; }}
    .sim-card-rating {{ font-size: 1.3rem; font-weight: 700; margin-top: auto; padding-top: 0.5rem; }}
    .sim-card-sim {{ color: var(--text-muted-2); font-size: 0.75rem; font-weight: 400; transition: color 0.35s ease; }}
    .sim-card-genres {{ margin: 0.3rem 0 0.5rem 0; }}

    /* ── Poster ── */
    .movie-poster {{
        border-radius: 12px;
        width: 100%;
        aspect-ratio: 2/3;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 3rem;
        font-weight: 700;
        text-shadow: 0 2px 10px rgba(0,0,0,0.5);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }}

    .movie-poster:hover {{ transform: scale(1.03); box-shadow: 0 8px 30px var(--card-shadow); }}

    .tmdb-poster {{ border-radius: 12px; width: 100%; aspect-ratio: 2/3; overflow: hidden; transition: all 0.3s ease; }}
    .tmdb-poster:hover {{ transform: scale(1.03); box-shadow: 0 8px 30px var(--card-shadow); }}
    .tmdb-poster img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}

    .movie-poster .poster-title {{
        position: absolute;
        bottom: 0; left: 0; right: 0;
        padding: 1rem 0.8rem 0.6rem;
        background: var(--hero-overlay);
        font-size: 0.85rem; font-weight: 600; color: white;
        text-align: center;
        text-shadow: 0 1px 4px rgba(0,0,0,0.6);
    }}

    .poster-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 1rem; }}

    /* ── Section headers ── */
    .section-title {{ font-size: 1.4rem; font-weight: 700; color: var(--text-primary); margin: 2rem 0 1rem 0; display: flex; align-items: center; gap: 0.5rem; transition: color 0.35s ease; }}
    .section-title .icon {{ font-size: 1.4rem; }}
    .section-subtitle {{ color: var(--text-muted); font-size: 0.9rem; font-weight: 300; margin-top: -0.5rem; margin-bottom: 1.5rem; transition: color 0.35s ease; }}

    .custom-divider {{ height: 1px; background: linear-gradient(90deg, transparent, rgba(247,151,30,0.3), transparent); margin: 1.5rem 0; }}

    /* ── Metrics ── */
    .metric-box {{ background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 1rem 1.2rem; text-align: center; transition: background 0.35s ease, border-color 0.35s ease; }}
    .metric-value {{ font-size: 1.8rem; font-weight: 700; color: var(--text-primary); transition: color 0.35s ease; }}
    .metric-label {{ font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0.2rem; transition: color 0.35s ease; }}

    .info-badge {{ display: inline-block; background: var(--hover-glow); border: 1px solid rgba(247,151,30,0.25); border-radius: 8px; padding: 0.3rem 0.8rem; font-size: 0.75rem; color: var(--star-color); font-weight: 500; transition: color 0.35s ease, background 0.35s ease, border-color 0.35s ease; }}

    /* ── Stars ── */
    .star-rating {{ font-size: 1.8rem; letter-spacing: 4px; cursor: default; }}
    .star-rating .star {{ cursor: pointer; transition: all 0.15s ease; }}
    .star-rating .star:hover {{ transform: scale(1.2); }}
    .star-filled {{ color: var(--star-color); transition: color 0.35s ease; }}
    .star-empty {{ color: var(--star-empty); transition: color 0.35s ease; }}

    .stat-card {{ background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 14px; padding: 1.2rem; text-align: center; transition: color 0.35s ease, background 0.35s ease, border-color 0.35s ease; }}
    .stat-card .value {{ font-size: 2.2rem; font-weight: 800; color: var(--text-primary); transition: color 0.35s ease; }}
    .stat-card .label {{ font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0.1rem; transition: color 0.35s ease; }}

    /* ── Footer ── */
    .app-footer {{ text-align: center; padding: 2rem 0 1rem 0; color: var(--footer-text); font-size: 0.8rem; transition: color 0.35s ease; }}
    .app-footer-brand {{ font-size: 1rem; font-weight: 700; color: var(--accent); margin-bottom: 0.5rem; }}
    .app-footer-links {{ display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; margin-bottom: 0.5rem; }}
    .app-footer-links a {{ color: var(--text-muted); text-decoration: none; font-size: 0.8rem; transition: color 0.2s; }}
    .app-footer-links a:hover {{ color: var(--accent); }}
    .app-footer-copy {{ color: var(--footer-text); line-height: 1.6; transition: color 0.35s ease; }}

    /* ── Streamlit overrides ── */
    .stApp > header {{ display: none !important; }}
    .stApp > div:first-child {{ padding-top: 0 !important; }}
    .main > div:first-child {{ padding-top: 0 !important; }}

    div.stButton > button {{
        background: var(--btn-primary-bg) !important;
        color: var(--btn-primary-text) !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.5rem 1.5rem !important;
        transition: all 0.3s ease !important;
    }}

    div.stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(247,151,30,0.3) !important;
    }}

    .stTabs [data-baseweb="tab-list"] {{ gap: 0.5rem; background: var(--tab-bg); border-radius: 12px; padding: 0.3rem; transition: background 0.35s ease; }}
    .stTabs [data-baseweb="tab"] {{ border-radius: 8px; padding: 0.5rem 1rem; color: var(--tab-text); font-weight: 500; font-size: 0.9rem; transition: color 0.35s ease; }}
    .stTabs [aria-selected="true"] {{ background: var(--accent-gradient) !important; color: #1a1a2e !important; }}
    .js-plotly-plot .plotly .main-svg {{ background: transparent !important; }}

    .mood-pill {{ display: inline-block; padding: 0.4rem 1rem; margin: 0.2rem; border-radius: 24px; font-size: 0.85rem; font-weight: 500; cursor: pointer; transition: all 0.2s ease; border: 1px solid var(--border-color); background: var(--bg-card); color: var(--text-muted); }}
    .mood-pill.active {{ background: var(--accent-gradient); color: #1a1a2e; border-color: transparent; font-weight: 600; }}

    .action-toast {{ position: fixed; bottom: 2rem; right: 2rem; background: rgba(34,197,94,0.9); color: white; padding: 0.8rem 1.5rem; border-radius: 12px; font-weight: 600; font-size: 0.9rem; z-index: 9999; backdrop-filter: blur(10px); animation: slideIn 0.3s ease, fadeOut 0.3s ease 2.5s forwards; }}

    @keyframes slideIn {{ from {{ transform: translateY(20px); opacity: 0; }} to {{ transform: translateY(0); opacity: 1; }} }}
    @keyframes fadeOut {{ to {{ opacity: 0; transform: translateY(-10px); }} }}

    .empty-state {{ text-align: center; padding: 3rem 1rem; color: var(--text-muted); transition: color 0.35s ease; }}
    .empty-state .icon {{ font-size: 3rem; margin-bottom: 0.5rem; }}
    .empty-state .text {{ font-size: 1rem; font-weight: 300; }}

    /* ═══════════════════════════════════════════════════════════════
       DASHBOARD — REDESIGNED (semantic HTML + smooth transitions)
       ═══════════════════════════════════════════════════════════════ */

    /* ── Header ── */
    .dash-header {{ margin: 0 0 1.5rem 0; animation: fadeSlideUp 0.5s ease forwards; }}
    .dash-title {{ font-size: 1.5rem; font-weight: 700; color: var(--text-primary); margin: 0; letter-spacing: -0.01em; transition: color 0.35s ease; }}
    .dash-subtitle {{ font-size: 0.82rem; color: var(--text-muted); margin: 0.2rem 0 0 0; transition: color 0.35s ease; }}

    /* ── Stat Cards ── */
    .dash-stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 0.9rem; margin: 0 0 2rem 0; }}
    .dash-stat {{
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 18px;
        padding: 1.3rem 1rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        position: relative;
        overflow: hidden;
        transition: transform 0.35s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.35s ease, border-color 0.35s ease;
    }}
    .dash-stat:hover {{ transform: translateY(-4px) scale(1.02); border-color: var(--border-hover); box-shadow: 0 16px 48px rgba(247,151,30,0.1); }}
    .dash-stat-icon {{ font-size: 1.6rem; margin-bottom: 0.4rem; }}
    .dash-stat-value {{ font-size: 2.2rem; font-weight: 800; line-height: 1.1; color: var(--text-primary); transition: color 0.35s ease; }}
    .dash-stat-value small {{ font-size: 0.9rem; font-weight: 400; color: var(--text-muted); transition: color 0.35s ease; }}
    .dash-stat-label {{ font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; font-weight: 500; margin-top: 0.15rem; transition: color 0.35s ease; }}
    .dash-stat--gold .dash-stat-value {{ background: linear-gradient(135deg, #f7971e, #ffd200); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
    .dash-stat--green .dash-stat-value {{ background: linear-gradient(135deg, #34d399, #22c55e); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
    .dash-stat--blue .dash-stat-value {{ background: linear-gradient(135deg, #60a5fa, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
    .dash-stat--purple .dash-stat-value {{ background: linear-gradient(135deg, #a78bfa, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}

    /* ── Summary line ── */
    .dash-summary {{ color: var(--text-muted); font-size: 0.8rem; margin-bottom: 1rem; transition: color 0.35s ease; }}
    .dash-summary strong {{ transition: color 0.35s ease; }}

    /* ── Rating Distribution ── */
    .dash-dist {{ display: flex; gap: 0.35rem; margin-bottom: 1.5rem; align-items: flex-end; }}
    .dash-dist-bar {{ display: flex; flex-direction: column; align-items: center; flex: 1; margin: 0; }}
    .dash-dist-count {{ font-size: 0.65rem; color: var(--text-muted-2); margin-bottom: 0.2rem; font-style: normal; transition: color 0.35s ease; }}
    .dash-dist-track {{ width: 100%; height: 60px; background: var(--tab-bg); border-radius: 8px; overflow: hidden; display: flex; align-items: flex-end; transition: background 0.35s ease; }}
    .dash-dist-fill {{ width: 100%; border-radius: 8px; transition: height 0.8s cubic-bezier(0.34,1.56,0.64,1); }}
    .dash-dist-label {{ font-size: 0.7rem; color: var(--text-muted); margin-top: 0.2rem; font-style: normal; transition: color 0.35s ease; }}

    /* ── Movie Grid & Cards ── */
    .dash-movie-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.9rem; margin: 1rem 0; }}
    .dash-movie-card {{
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 14px;
        padding: 1rem 0.9rem;
        transition: transform 0.35s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.35s ease, border-color 0.35s ease;
        animation: cardFadeIn 0.45s ease forwards;
        opacity: 0;
    }}
    .dash-movie-card:hover {{ border-color: var(--border-hover); transform: translateY(-3px); box-shadow: 0 12px 40px var(--card-shadow); }}
    .dash-movie-card:active {{ transform: translateY(-1px) scale(0.98); }}
    .dash-movie-card-header {{ display: flex; align-items: baseline; gap: 0.4rem; flex-wrap: wrap; }}
    .dash-movie-card-title {{ font-size: 0.88rem; font-weight: 600; color: var(--text-primary); margin: 0; line-height: 1.3; transition: color 0.35s ease; }}
    .dash-movie-card-year {{ font-size: 0.72rem; color: var(--text-muted); font-weight: 400; white-space: nowrap; transition: color 0.35s ease; }}
    .dash-movie-card-genres {{ margin: 0.3rem 0; display: flex; flex-wrap: wrap; gap: 0.15rem; }}
    .dash-movie-card-stars {{ font-size: 0.95rem; letter-spacing: 1px; margin: 0.15rem 0; transition: color 0.35s ease; }}
    .dash-movie-card-rating {{ font-size: 1.4rem; font-weight: 800; display: flex; align-items: baseline; gap: 0.15rem; transition: color 0.35s ease; }}
    .dash-movie-card-rating small {{ font-size: 0.65rem; font-weight: 400; color: var(--text-muted-3); transition: color 0.35s ease; }}
    .dash-movie-card-pred {{ font-size: 0.65rem; color: var(--text-muted-2); margin-top: 0.2rem; transition: color 0.35s ease; }}
    .dash-chip-mini {{ font-size: 0.55rem !important; padding: 0.1rem 0.35rem !important; margin: 0.05rem 0.1rem !important; }}

    /* ── Empty State ── */
    .dash-empty {{ text-align: center; padding: 3rem 1rem; color: var(--text-muted); animation: fadeSlideUp 0.5s ease forwards; transition: color 0.35s ease; }}
    .dash-empty-icon {{ font-size: 3rem; margin-bottom: 0.5rem; }}
    .dash-empty-text {{ font-size: 1rem; font-weight: 400; color: var(--text-secondary); margin: 0; transition: color 0.35s ease; }}
    .dash-empty-hint {{ font-size: 0.85rem; color: var(--text-muted); margin-top: 0.4rem; transition: color 0.35s ease; }}

    /* ── Watchlist Section ── */
    .dash-wl-section {{ margin: 0.5rem 0 1rem 0; }}
    .dash-wl-header {{ display: flex; align-items: center; gap: 0.5rem; padding: 0.6rem 0 0.4rem 0; border-bottom: 1px solid var(--border-subtle); margin-bottom: 0.5rem; transition: border-color 0.35s ease; }}
    .dash-wl-icon {{ font-size: 1.1rem; }}
    .dash-wl-title {{ font-size: 0.95rem; font-weight: 600; color: var(--text-primary); margin: 0; transition: color 0.35s ease; }}
    .dash-wl-count {{ font-size: 0.7rem; font-weight: 400; color: var(--text-muted); background: var(--tab-bg); padding: 0.1rem 0.45rem; border-radius: 999px; margin-left: 0.3rem; transition: color 0.35s ease, background 0.35s ease; }}

    /* ── Settings ── */
    .dash-settings-header {{ margin-bottom: 1rem; }}
    .dash-settings-title {{ font-size: 1.1rem; font-weight: 600; color: var(--text-primary); margin: 0; transition: color 0.35s ease; }}
    .dash-settings-desc {{ font-size: 0.82rem; color: var(--text-muted); margin: 0.2rem 0 0 0; transition: color 0.35s ease; }}
    .dash-export-header {{ margin: 1.5rem 0 0.5rem 0; }}
    .dash-export-title {{ font-size: 1rem; font-weight: 600; color: var(--text-primary); margin: 0; transition: color 0.35s ease; }}
    .dash-divider {{ height: 1px; background: linear-gradient(90deg, transparent, rgba(247,151,30,0.2), rgba(247,151,30,0.4), rgba(247,151,30,0.2), transparent); margin: 2rem 0; border: none; }}

    /* ── Shared section header (used by other pages) ── */
    .dash-section-header {{ display: flex; align-items: center; gap: 0.75rem; margin: 2rem 0 1.25rem 0; padding-bottom: 0.75rem; border-bottom: 1px solid var(--border-subtle); }}
    .dash-section-header .h-icon {{ font-size: 1.4rem; }}
    .dash-section-header .h-title {{ font-size: 1.25rem; font-weight: 700; color: var(--text-primary); letter-spacing: -0.01em; transition: color 0.35s ease; }}
    .dash-section-header .h-subtitle {{ margin-left: auto; font-size: 0.75rem; color: var(--text-muted-2); font-weight: 400; letter-spacing: 0.3px; transition: color 0.35s ease; }}

    /* ── Shared card grid (used by other pages) ── */
    .dash-card-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1rem; margin: 1rem 0; }}
    .dash-card {{
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 16px;
        padding: 1.2rem 1rem;
        cursor: pointer;
        transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.35s ease, border-color 0.35s ease;
        position: relative;
        overflow: hidden;
    }}
    .dash-card:hover {{ border-color: var(--border-hover); transform: translateY(-3px); box-shadow: 0 16px 48px var(--card-shadow); }}
    .dash-card:active {{ transform: translateY(-1px) scale(0.98); }}
    .dash-card .dc-title {{ font-size: 0.9rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.15rem; line-height: 1.3; transition: color 0.35s ease; }}
    .dash-card .dc-meta {{ font-size: 0.75rem; color: var(--text-muted); font-weight: 400; transition: color 0.35s ease; }}
    .dash-card .dc-rating {{ font-size: 1.5rem; font-weight: 800; margin-top: 0.4rem; display: flex; align-items: baseline; gap: 0.2rem; }}
    .dash-card .dc-rating .dc-max {{ font-size: 0.7rem; font-weight: 400; color: var(--text-muted-3); transition: color 0.35s ease; }}
    .dash-card .dc-actions {{ margin-top: 0.6rem; display: flex; gap: 0.4rem; }}
    .dash-card .dc-badge {{ display: inline-block; padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.6rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; background: var(--hover-glow); color: var(--star-color); border: 1px solid rgba(247,151,30,0.15); }}
    .dash-card .dc-stars {{ font-size: 1.1rem; letter-spacing: 1px; margin: 0.15rem 0; }}
    .genre-bar {{ height: 0.5rem; background: var(--star-empty); border-radius: 999px; overflow: hidden; width: 100%; max-width: 120px; transition: background 0.35s ease; }}
    .genre-bar-fill {{ height: 100%; border-radius: 999px; transition: width 1s cubic-bezier(0.34, 1.56, 0.64, 1); }}
    .wl-category-header {{ display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem 0 0.5rem 0; margin-top: 1rem; border-bottom: 1px solid var(--border-subtle); }}
    .wl-category-header .wl-cat-icon {{ font-size: 1.2rem; }}
    .wl-category-header .wl-cat-name {{ font-size: 1rem; font-weight: 600; color: var(--text-primary); transition: color 0.35s ease; }}
    .wl-category-header .wl-cat-count {{ font-size: 0.75rem; font-weight: 400; color: var(--text-muted); background: var(--tab-bg); padding: 0.1rem 0.5rem; border-radius: 999px; transition: color 0.35s ease, background 0.35s ease; }}
    .genre-table-wrap {{ overflow-x: auto; margin-top: 1rem; border-radius: 12px; border: 1px solid var(--border-subtle); }}
    .genre-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
    .genre-table thead th {{ padding: 0.65rem 0.8rem; text-align: left; color: var(--text-muted); font-weight: 500; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; background: var(--tab-bg); border-bottom: 1px solid var(--border-subtle); transition: color 0.35s ease, background 0.35s ease, border-color 0.35s ease; }}
    .genre-table tbody tr {{ transition: background 0.2s ease; }}
    .genre-table tbody tr:hover {{ background: var(--hover-glow); }}
    .genre-table tbody td {{ padding: 0.55rem 0.8rem; border-bottom: 1px solid var(--border-subtle); color: var(--text-secondary); transition: color 0.35s ease, border-color 0.35s ease; }}
    .genre-table tbody tr:last-child td {{ border-bottom: none; }}

    /* ═══════════════════════════════════════════════════════════════
       MOVIE DETAIL MODERN STYLES
       ═══════════════════════════════════════════════════════════════ */

    .detail-hero {{
        background: var(--bg-card-ghost);
        border: 1px solid var(--border-color);
        border-radius: 20px;
        padding: 1.8rem 2rem;
        margin: 0 0 1.5rem 0;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        transition: all 0.3s ease, background 0.35s ease, border-color 0.35s ease;
    }}

    .detail-hero:hover {{ border-color: rgba(247,151,30,0.2); box-shadow: 0 8px 32px rgba(247,151,30,0.06); }}
    .detail-hero .movie-title-main {{ font-size: 2.2rem; font-weight: 800; color: var(--text-primary); margin: 0; line-height: 1.15; letter-spacing: -0.015em; transition: color 0.35s ease; }}
    .detail-hero .movie-title-main .year-badge {{ font-size: 1.2rem; font-weight: 400; color: var(--text-muted); margin-left: 0.5rem; transition: color 0.35s ease; }}

    .rating-badge {{ display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100px; height: 100px; border-radius: 50%; background: var(--bg-card); border: 2px solid var(--border-color); position: relative; transition: all 0.3s ease; }}
    .rating-badge:hover {{ transform: scale(1.05); }}
    .rating-badge .rb-value {{ font-size: 1.8rem; font-weight: 800; line-height: 1; }}
    .rating-badge .rb-label {{ font-size: 0.55rem; font-weight: 500; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0.15rem; transition: color 0.35s ease; }}
    .rating-badge .rb-stars {{ font-size: 0.75rem; letter-spacing: 1px; margin-top: 0.1rem; }}

    .detail-meta-row {{ display: flex; align-items: baseline; gap: 0.5rem; padding: 0.35rem 0; font-size: 0.9rem; color: var(--text-muted); border-bottom: 1px solid var(--border-subtle); transition: color 0.35s ease, border-color 0.35s ease; }}
    .detail-meta-row:last-of-type {{ border-bottom: none; }}
    .detail-meta-row .meta-label {{ font-weight: 500; color: var(--text-muted-2); text-transform: uppercase; font-size: 0.65rem; letter-spacing: 0.5px; min-width: 70px; transition: color 0.35s ease; }}
    .detail-meta-row .meta-value {{ color: var(--text-secondary); font-weight: 400; transition: color 0.35s ease; }}
    .detail-meta-row .meta-value a {{ color: #60a5fa; text-decoration: none; transition: color 0.2s; }}
    .detail-meta-row .meta-value a:hover {{ color: #93c5fd; text-decoration: underline; }}

    .detail-stats {{ display: flex; flex-wrap: wrap; gap: 0.6rem; margin: 0.75rem 0; }}
    .detail-stat-chip {{ display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.3rem 0.7rem; border-radius: 8px; background: var(--tab-bg); border: 1px solid var(--border-subtle); font-size: 0.78rem; color: var(--text-muted); font-weight: 500; transition: all 0.2s ease, background 0.35s ease, border-color 0.35s ease, color 0.35s ease; }}
    .detail-stat-chip:hover {{ background: var(--bg-card-hover); border-color: var(--border-hover); }}
    .detail-stat-chip .chip-icon {{ font-size: 0.85rem; }}
    .detail-tagline {{ font-style: italic; font-size: 1.1rem; color: var(--text-secondary); border-left: 3px solid rgba(247,151,30,0.35); padding: 0.5rem 0 0.5rem 1rem; margin: 0.5rem 0; line-height: 1.5; transition: color 0.35s ease; }}
    .detail-overview {{ color: var(--text-secondary); font-size: 0.9rem; line-height: 1.65; margin: 0.5rem 0; transition: color 0.35s ease; }}

    .detail-kw-grid {{ display: flex; flex-wrap: wrap; gap: 0.3rem; margin: 0.5rem 0; }}
    .detail-kw-chip {{ display: inline-block; padding: 0.15rem 0.65rem; border-radius: 999px; background: var(--tab-bg); color: var(--text-muted); font-size: 0.7rem; font-weight: 400; border: 1px solid var(--border-subtle); transition: all 0.2s ease, background 0.35s ease, border-color 0.35s ease, color 0.35s ease; }}
    .detail-kw-chip:hover {{ background: var(--hover-glow); color: var(--star-color); border-color: rgba(247,151,30,0.15); }}

    .detail-side-widget {{ background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: 16px; padding: 1.2rem 1rem; margin: 1rem 0; backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); transition: background 0.35s ease, border-color 0.35s ease; }}
    .detail-side-widget .w-label {{ font-size: 0.75rem; font-weight: 600; color: var(--text-muted-2); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.6rem; transition: color 0.35s ease; }}

    .detail-mini-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 0.75rem; margin: 0.75rem 0; }}

    .detail-mini-card {{
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 14px;
        padding: 0.9rem 0.9rem 0.75rem;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.35s ease, border-color 0.35s ease;
    }}

    .detail-mini-card:hover {{ border-color: var(--border-hover); transform: translateY(-2px); box-shadow: 0 12px 32px var(--card-shadow); }}
    .detail-mini-card .dmc-title {{ font-size: 0.85rem; font-weight: 600; color: var(--text-primary); line-height: 1.25; transition: color 0.35s ease; }}
    .detail-mini-card .dmc-year {{ font-size: 0.7rem; color: var(--text-muted); font-weight: 400; transition: color 0.35s ease; }}
    .detail-mini-card .dmc-rating {{ font-size: 1.15rem; font-weight: 700; margin-top: 0.3rem; display: flex; align-items: baseline; gap: 0.15rem; }}
    .detail-mini-card .dmc-rating .dmc-max {{ font-size: 0.65rem; font-weight: 400; color: var(--text-muted-3); transition: color 0.35s ease; }}

    .star-widget {{ display: flex; gap: 0.3rem; margin: 0.5rem 0; }}
    .star-widget .sw-btn {{ display: inline-flex; align-items: center; justify-content: center; width: 2.4rem; height: 2.4rem; border-radius: 10px; font-size: 1.3rem; background: var(--tab-bg); border: 1px solid var(--border-subtle); cursor: pointer; transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1); }}
    .star-widget .sw-btn:hover {{ transform: scale(1.15); background: var(--hover-glow); border-color: rgba(247,151,30,0.3); }}
    .star-widget .sw-btn.filled {{ background: var(--hover-glow); border-color: rgba(247,151,30,0.3); color: var(--star-color); }}

    .sim-card-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 1rem; margin: 1rem 0; }}

    .sim-card-new {{
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 16px;
        padding: 1.1rem 1rem;
        cursor: pointer;
        transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.35s ease, border-color 0.35s ease;
        display: flex;
        flex-direction: column;
    }}

    .sim-card-new:hover {{ border-color: var(--border-hover); transform: translateY(-3px); box-shadow: 0 16px 48px var(--card-shadow); }}
    .sim-card-new .sc-title {{ font-size: 0.9rem; font-weight: 600; color: var(--text-primary); line-height: 1.3; margin-bottom: 0.1rem; transition: color 0.35s ease; }}
    .sim-card-new .sc-year {{ font-size: 0.72rem; color: var(--text-muted); font-weight: 400; transition: color 0.35s ease; }}
    .sim-card-new .sc-genres {{ margin: 0.2rem 0 0.35rem 0; }}
    .sim-card-new .sc-rating {{ font-size: 1.3rem; font-weight: 700; margin-top: auto; padding-top: 0.3rem; display: flex; align-items: baseline; gap: 0.2rem; }}
    .sim-card-new .sc-rating .sc-max {{ font-size: 0.65rem; font-weight: 400; color: var(--text-muted-3); transition: color 0.35s ease; }}
    .sim-card-new .sc-sim {{ font-size: 0.7rem; color: var(--text-muted-2); font-weight: 400; margin-top: 0.2rem; transition: color 0.35s ease; }}
    .sim-card-new .sc-badge {{ display: inline-block; padding: 0.1rem 0.4rem; border-radius: 999px; font-size: 0.55rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; background: var(--hover-glow); color: var(--star-color); border: 1px solid rgba(247,151,30,0.12); margin-left: 0.3rem; }}
    .sim-card-new .sc-actions {{ display: flex; gap: 0.4rem; margin-top: 0.5rem; }}

    /* ── Card entrance animation delays ── */
    .dash-card, .dash-stat-glass, .sim-card-new {{ animation: cardFadeIn 0.5s ease forwards; opacity: 0; }}
    .dash-card:nth-child(1), .dash-stat-glass:nth-child(1), .sim-card-new:nth-child(1) {{ animation-delay: 0.05s; }}
    .dash-card:nth-child(2), .dash-stat-glass:nth-child(2), .sim-card-new:nth-child(2) {{ animation-delay: 0.1s; }}
    .dash-card:nth-child(3), .dash-stat-glass:nth-child(3), .sim-card-new:nth-child(3) {{ animation-delay: 0.15s; }}
    .dash-card:nth-child(4), .dash-stat-glass:nth-child(4), .sim-card-new:nth-child(4) {{ animation-delay: 0.2s; }}
    .dash-card:nth-child(5), .dash-stat-glass:nth-child(5), .sim-card-new:nth-child(5) {{ animation-delay: 0.25s; }}
    .dash-card:nth-child(6), .dash-stat-glass:nth-child(6), .sim-card-new:nth-child(6) {{ animation-delay: 0.3s; }}
    .dash-card:nth-child(7), .dash-stat-glass:nth-child(7), .sim-card-new:nth-child(7) {{ animation-delay: 0.35s; }}
    .dash-card:nth-child(8), .dash-stat-glass:nth-child(8), .sim-card-new:nth-child(8) {{ animation-delay: 0.4s; }}
    .dash-card:nth-child(9), .dash-stat-glass:nth-child(9), .sim-card-new:nth-child(9) {{ animation-delay: 0.45s; }}
    .dash-card:nth-child(10), .dash-stat-glass:nth-child(10), .sim-card-new:nth-child(10) {{ animation-delay: 0.5s; }}
    .sim-card-new:nth-child(11) {{ animation-delay: 0.55s; }}
    .sim-card-new:nth-child(12) {{ animation-delay: 0.6s; }}

    @keyframes cardFadeIn {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes fadeSlideUp {{ from {{ opacity: 0; transform: translateY(14px); }} to {{ opacity: 1; transform: translateY(0); }} }}

    /* ── Backward-compat aliases for components.py (dash-stat-glass etc.) ── */
    .dash-stat-glass {{
        position: relative; background: var(--bg-card); border: 1px solid var(--border-color);
        border-radius: 20px; padding: 1.5rem 1.2rem; backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px); overflow: hidden;
        transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.35s ease, border-color 0.35s ease;
    }}
    .dash-stat-glass:hover {{ transform: translateY(-4px) scale(1.02); border-color: var(--border-hover); box-shadow: 0 20px 60px rgba(247,151,30,0.1); }}
    .dash-stat-glass .stat-glow {{
        position: absolute; top: -50%; right: -50%; width: 100%; height: 100%;
        background: radial-gradient(circle, rgba(247,151,30,0.08) 0%, transparent 70%);
        pointer-events: none; animation: pulseGlow 4s ease-in-out infinite;
    }}
    @keyframes pulseGlow {{ 0%, 100% {{ opacity: 0.5; transform: scale(1); }} 50% {{ opacity: 1; transform: scale(1.2); }} }}
    .dash-stat-glass .stat-icon {{ font-size: 1.8rem; margin-bottom: 0.5rem; display: block; }}
    .dash-stat-glass .stat-value {{ font-size: 2.5rem; font-weight: 800; color: var(--text-primary); line-height: 1.1; letter-spacing: -0.02em; transition: color 0.35s ease; }}
    .dash-stat-glass .stat-value .stat-suffix {{ font-size: 1rem; font-weight: 400; color: var(--text-muted); margin-left: 0.2rem; transition: color 0.35s ease; }}
    .dash-stat-glass .stat-label {{ font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; margin-top: 0.15rem; font-weight: 500; transition: color 0.35s ease; }}
    .stat-accent-gold .stat-value {{ background: linear-gradient(135deg, #f7971e, #ffd200); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
    .stat-accent-green .stat-value {{ background: linear-gradient(135deg, #34d399, #22c55e); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
    .stat-accent-blue .stat-value {{ background: linear-gradient(135deg, #60a5fa, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
    .stat-accent-purple .stat-value {{ background: linear-gradient(135deg, #a78bfa, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}

    /* ── Home Page Hero Section ── */
    .hero-section {{ position: relative; background: var(--bg-card-ghost); border: 1px solid var(--border-color); border-radius: 20px; padding: 2rem 2.5rem; margin: 0 0 2rem 0; overflow: hidden; transition: background 0.35s ease, border-color 0.35s ease; }}
    .hero-gradient {{ position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(ellipse at 80% 20%, rgba(247,151,30,0.06) 0%, transparent 60%); pointer-events: none; }}
    .hero-content {{ position: relative; z-index: 1; }}

    .hero-badge {{ display: inline-block; padding: 0.2rem 0.8rem; border-radius: 999px; background: var(--hover-glow); color: var(--star-color); font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem; border: 1px solid rgba(247,151,30,0.15); transition: color 0.35s ease, background 0.35s ease; }}
    .hero-title {{ font-size: 2.5rem; font-weight: 800; color: var(--text-primary); margin: 0; line-height: 1.15; letter-spacing: -0.02em; transition: color 0.35s ease; }}
    .hero-meta {{ display: flex; align-items: center; gap: 1rem; margin: 0.5rem 0; color: var(--text-secondary); font-size: 0.9rem; transition: color 0.35s ease; }}
    .hero-meta .rating {{ color: var(--star-color); font-weight: 600; }}
    .hero-meta .rating span {{ color: var(--text-muted); font-weight: 400; }}
    .hero-overview {{ color: var(--text-secondary); font-size: 0.9rem; line-height: 1.6; margin: 0.5rem 0; max-width: 700px; transition: color 0.35s ease; }}
    .hero-actions {{ display: flex; gap: 0.75rem; margin-top: 1rem; }}
    .hero-btn {{ padding: 0.5rem 1.5rem; border-radius: 10px; font-size: 0.85rem; font-weight: 600; border: none; cursor: pointer; transition: all 0.3s ease; }}
    .hero-btn-primary {{ background: var(--accent-gradient); color: #1a1a2e; }}
    .hero-btn-primary:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(247,151,30,0.3); }}
    .hero-btn-secondary {{ background: var(--btn-secondary-bg); color: var(--btn-secondary-text); border: 1px solid var(--border-color); transition: all 0.3s ease, background 0.35s ease, border-color 0.35s ease, color 0.35s ease; }}
    .hero-btn-secondary:hover {{ background: var(--bg-card-hover); border-color: var(--border-hover); }}

    .section-header {{ display: flex; align-items: center; gap: 0.75rem; margin: 2rem 0 1.25rem 0; }}
    .section-header .accent-line {{ width: 4px; height: 1.5rem; background: var(--accent-gradient); border-radius: 999px; }}
    .section-header h2 {{ font-size: 1.3rem; font-weight: 700; color: var(--text-primary); margin: 0; transition: color 0.35s ease; }}

    .imdb-card {{ background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: 14px; overflow: hidden; transition: all 0.3s ease, background 0.35s ease, border-color 0.35s ease; cursor: pointer; }}
    .imdb-card:hover {{ transform: translateY(-3px); box-shadow: 0 12px 32px var(--card-shadow); border-color: var(--border-hover); }}
    .imdb-card-poster {{ width: 100%; aspect-ratio: 2/3; display: flex; align-items: center; justify-content: center; font-size: 2.5rem; font-weight: 700; color: rgba(255,255,255,0.7); text-shadow: 0 2px 8px rgba(0,0,0,0.3); position: relative; }}
    .imdb-card-body {{ padding: 0.75rem 0.8rem; }}
    .imdb-card-title {{ font-size: 0.85rem; font-weight: 600; color: var(--text-primary); line-height: 1.3; margin-bottom: 0.15rem; transition: color 0.35s ease; }}
    .imdb-card-meta {{ display: flex; align-items: center; gap: 0.5rem; font-size: 0.75rem; }}
    .imdb-card-rating {{ color: var(--star-color); font-weight: 600; }}
    .imdb-card-year {{ color: var(--text-muted); font-weight: 400; }}
    .imdb-card-genres {{ margin-top: 0.25rem; display: flex; gap: 0.2rem; flex-wrap: wrap; }}
    .imdb-card-genre-chip {{ display: inline-block; padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.6rem; font-weight: 500; background: var(--tab-bg); color: var(--text-muted); border: 1px solid var(--border-subtle); transition: color 0.35s ease, background 0.35s ease, border-color 0.35s ease; }}

    .sidebar-stat {{ transition: color 0.35s ease; }}

    .theme-toggle-btn {{ display: inline-flex; align-items: center; justify-content: center; gap: 0.4rem; padding: 0.45rem 1rem; border-radius: 10px; font-size: 0.8rem; font-weight: 500; border: 1px solid var(--border-color); background: var(--bg-card); color: var(--text-secondary); cursor: pointer; transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); width: 100%; }}
    .theme-toggle-btn:hover {{ border-color: var(--accent); background: var(--hover-glow); color: var(--accent); }}

    .main-content {{ transition: color 0.35s ease; }}

    /* ── Sidebar overrides for light theme ── */
    .theme-light [data-testid="stSidebar"] {{ background: rgba(255,255,255,0.5) !important; }}

    .theme-light div.stButton > button[kind="secondary"] {{ background: rgba(0,0,0,0.04) !important; color: #475569 !important; }}

    .theme-light input, .theme-light select, .theme-light textarea {{ background: white !important; color: #0f172a !important; border-color: rgba(0,0,0,0.12) !important; }}
    .theme-light .st-bq, .theme-light .st-br {{ background: white !important; }}
    .theme-light .st-cn {{ color: #475569 !important; }}
    .theme-light .st-eq {{ background: rgba(0,0,0,0.02) !important; }}
    .theme-light .st-cj {{ color: #475569 !important; }}

    .theme-light .stAlert {{ background: white !important; color: #0f172a !important; }}

    .theme-light .streamlit-expanderHeader {{ color: #475569 !important; background: rgba(0,0,0,0.02) !important; }}
    .theme-light .streamlit-expanderContent {{ background: transparent !important; }}

    .theme-light div[data-baseweb="select"] > div {{ background: white !important; border-color: rgba(0,0,0,0.12) !important; }}
    .theme-light div[data-baseweb="select"] span {{ color: #0f172a !important; }}
    .theme-light div[data-baseweb="select"] svg {{ fill: #475569 !important; }}

    .theme-light div[data-baseweb="tag"] {{ background: rgba(0,0,0,0.06) !important; color: #0f172a !important; }}
    .theme-light div[role="listbox"] {{ background: white !important; }}
    .theme-light div[role="option"] {{ color: #0f172a !important; }}
    .theme-light div[role="option"]:hover {{ background: rgba(247,151,30,0.06) !important; }}

    .theme-light [data-testid="stSidebar"] .stButton button {{ background: rgba(0,0,0,0.03) !important; color: #475569 !important; }}
    .theme-light [data-testid="stSidebar"] .stButton button[kind="primary"] {{ background: var(--accent-gradient) !important; color: #1a1a2e !important; }}

</style>
""",
        unsafe_allow_html=True,
    )
