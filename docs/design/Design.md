# Design — MovieLens AI: Design System & UX Principles

| Field | Value |
| --- | --- |
| Version | v0.1 |
| Last Updated | 2026-08-06 |
| Owner | Design Lead |
| Status | In Review |

---

## 1. Design Principles

1. **Discovery-first** — search is the hero.
2. **Explainable** — every score shows its breakdown.
3. **Cinematic feel** — dark, film-inspired theme.
4. **Calm density** — charts + lists, minimal prose.
5. **Fast feedback** — instant search results.

## 2. Brand & Visual Identity

- Voice: cinematic, smart, friendly.
- Imagery: poster-style cards (if available), charts.

## 3. Color System

| Token | Hex | Usage | Contrast (AA) |
| --- | --- | --- | --- |
| bg | `#0B0F19` | dark cinematic bg | — |
| surface | `#141A26` | cards | — |
| text | `#F8FAFC` | body | 15:1 |
| accent | `#F59E0B` | ratings (gold) | 4.8:1 |
| accent-blue | `#3B82F6` | links | 5.8:1 |
| success | `#22C55E` | high rating | 5:1 |
| muted | `#94A3B8` | secondary | 7:1 |

## 4. Typography Scale

| Token | Font | Size | Weight | Line-height | Usage |
| --- | --- | --- | --- | --- | --- |
| display | sans | 28px | 700 | 1.2 | page titles |
| heading | sans | 20px | 600 | 1.3 | sections |
| body | sans | 14px | 400 | 1.5 | content |
| rating | mono | 24px | 700 | 1.2 | rating scores |
| caption | sans | 12px | 400 | 1.4 | meta |

## 5. Spacing & Grid

- Base 4px; Streamlit layout.
- Breakpoints: Streamlit responsive.

## 6. Component Library

**Movie result card:**

```
┌──────────────────────────────┐
│ Inception (2010)      ★ 4.6 │
│ Sci-Fi · Thriller           │
│ [Prediction Breakdown]      │
│ [Similar Movies]            │
└──────────────────────────────┘
```

**Prediction breakdown:** horizontal bar chart of feature contributions (genre/tags/year/rating).

Other: search box, genre filter chips, watchlist table, decade slider, lineup list.

## 7. Iconography

Plotly + emoji; no image assets.

## 8. Accessibility

- WCAG 2.1 AA targets; ratings not color-only (star + number).

## 9. Responsive

- Fluid Streamlit layout.

## 10. Motion

- Chart transitions (300ms); reduced-motion honored.

## 11. Dark Mode

Dark cinematic theme (default).

## 12. Related Documents

| Document | Relationship |
| --- | --- |
| [AppFlow.md](AppFlow.md) | Screens |
| [PRD.md](../product/PRD.md) | UX goals |
| [TechSpec.md](../technical/TechSpec.md) | Stack |
| [Schema.md](../technical/Schema.md) | Display data |
| [ImplementationPlan.md](../project/ImplementationPlan.md) | Tasks |
| [Tracker.md](../project/Tracker.md) | Status |
| [Rules.md](../project/Rules.md) | Standards |
| [API.md](../technical/API.md) | Contracts |
| [SecurityAndCompliance.md](../technical/SecurityAndCompliance.md) | Data |
| [Testing.md](../technical/Testing.md) | UI tests |
| [Deployment.md](../technical/Deployment.md) | Deploy |
| [Glossary.md](../reference/Glossary.md) | Vocabulary |
| [RiskRegister.md](../project/RiskRegister.md) | Risks |
