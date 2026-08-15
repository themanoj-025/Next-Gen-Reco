"""Movie stats and trivia."""

import streamlit as st


def render_movie_stats_section(movie_id: int, info: dict):
    """Show interesting stats and trivia for a movie on the detail page."""
    rec = st.session_state.recommender

    if not hasattr(rec, "get_movie_stats"):
        return

    stats = rec.get_movie_stats(movie_id)
    if not stats or len(stats) <= 3:
        return

    st.markdown(
        '<div class="section-title"><span class="icon">📊</span> Movie Stats &amp; Trivia</div>',
        unsafe_allow_html=True,
    )

    stat_items = []

    # Budget / Revenue / ROI
    budget = stats.get("budget")
    revenue = stats.get("revenue")
    roi = stats.get("roi")

    if budget and revenue:
        b_str = (
            f"${budget / 1_000_000:.0f}M"
            if budget >= 1_000_000
            else f"${budget / 1_000:.0f}K"
        )
        r_str = (
            f"${revenue / 1_000_000:.0f}M"
            if revenue >= 1_000_000
            else f"${revenue / 1_000:.0f}K"
        )
        if roi:
            roi_label = (
                "💰 Blockbuster"
                if roi >= 5
                else "📈 Profitable"
                if roi >= 2
                else "📉 Modest"
                if roi >= 1
                else "💸 Flop"
            )
            stat_items.append(
                (
                    f"{roi_label}",
                    f"Budget: {b_str} → Revenue: {r_str}",
                    f"{roi:.1f}x ROI",
                    "#22c55e" if roi >= 2 else "#fbbf24" if roi >= 1 else "#ef4444",
                )
            )
    elif budget:
        b_str = (
            f"${budget / 1_000_000:.0f}M"
            if budget >= 1_000_000
            else f"${budget / 1_000:.0f}K"
        )
        stat_items.append(("💰 Budget", "Production budget", b_str, "#60a5fa"))
    elif revenue:
        r_str = (
            f"${revenue / 1_000_000:.0f}M"
            if revenue >= 1_000_000
            else f"${revenue / 1_000:.0f}K"
        )
        stat_items.append(("💵 Revenue", "Box office revenue", r_str, "#34d399"))

    # Runtime
    runtime = stats.get("runtime")
    runtime_diff = stats.get("runtime_diff")
    if runtime:
        h = runtime // 60
        m = runtime % 60
        rt_str = f"{h}h {m}m" if h > 0 else f"{m}m"
        if runtime_diff:
            diff_str = f"{runtime_diff:+d} min"
            if runtime_diff > 0:
                diff_str += " (longer than average)"
            elif runtime_diff < 0:
                diff_str += " (shorter than average)"
            stat_items.append(("⏱️ Runtime", diff_str, rt_str, "#a78bfa"))
        else:
            stat_items.append(("⏱️ Runtime", "", rt_str, "#a78bfa"))

    # Popularity percentile
    pop_pct = stats.get("popularity_percentile")
    if pop_pct is not None:
        rank_label = (
            "🏆 Top Tier"
            if pop_pct >= 90
            else "⭐ Popular"
            if pop_pct >= 70
            else "📊 Average"
            if pop_pct >= 40
            else "🔍 Niche"
        )
        stat_items.append(
            (
                f"{rank_label}",
                f"More popular than {pop_pct:.0f}% of movies",
                f"{pop_pct:.0f}%ile",
                "#f97316",
            )
        )

    # Vote average
    vote_avg = stats.get("vote_average")
    if vote_avg:
        tmdb_color = (
            "#01b4e4" if vote_avg >= 7 else "#fbbf24" if vote_avg >= 5 else "#ef4444"
        )
        stat_items.append(
            ("🌐 TMDB Rating", "Community score", f"{vote_avg:.1f}/10", tmdb_color)
        )

    # Genre count
    gc = stats.get("genre_count")
    gc_vs = stats.get("genre_count_vs_avg")
    if gc and gc_vs is not None:
        vs_str = f"{gc_vs:+.1f} vs avg" if gc_vs != 0 else "Exactly average"
        stat_items.append(("🎭 Genre Diversity", vs_str, f"{gc} genres", "#38bdf8"))

    # Director info
    director = stats.get("director")
    dir_count = stats.get("director_movie_count")
    if director and dir_count:
        stat_items.append(
            (
                "🎬 Director",
                f"{dir_count} movies in our database",
                director[:30],
                "#f472b6",
            )
        )

    # Show as a grid of cards
    if stat_items:
        stat_cols = st.columns(min(3, len(stat_items)))
        for i, (label, sublabel, value, color) in enumerate(stat_items):
            with stat_cols[i % 3]:
                st.markdown(
                    f"""
                <div style="background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:12px;padding:0.8rem 1rem;text-align:center;height:100%;">
                    <div style="font-size:1.3rem;font-weight:700;color:{color};">{value}</div>
                    <div style="font-weight:500;color:var(--text-secondary);font-size:0.85rem;margin-top:0.1rem;">{label}</div>
                    <div style="color:var(--text-muted);font-size:0.75rem;margin-top:0.15rem;">{sublabel}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )


# ── Main app ──────────────────────────────────────────────────────────────────
