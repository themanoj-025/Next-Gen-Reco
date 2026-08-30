"""CSS injection module — dark/light theme support via CSS custom properties."""

import streamlit as st

from app.ui.styles_themes import dark_vars, light_vars
from app.ui.styles_css import CSS_BLOCK


def inject_css(theme="dark") -> None:
    """Inject all custom CSS into the app.

    Parameters
    ----------
    theme : str
        Either "dark" or "light" — determines which set of CSS custom
        properties are injected at the .stApp level so the entire app
        (nav, sidebar, main content, footer) picks up the theme.
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
    }}

    /* ── Theme class overrides (fallback) ── */
    .theme-dark {{
        {dark_class_vars}
    }}

    .theme-light {{
        {light_class_vars}
    }}
{CSS_BLOCK}
</style>
""",
        unsafe_allow_html=True,
    )
