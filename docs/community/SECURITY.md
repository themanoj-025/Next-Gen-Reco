# Security Policy for Next-Gen-Reco

## Reporting a Vulnerability

If you discover a security vulnerability in Next-Gen-Reco, please report it privately.

**How to report:**
- Open a private security advisory on GitHub (if this repository is public).
- Email **manojjana.0025@gmail.com** directly. This contact is also listed in our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
- If neither channel works, open a standard issue with the label `security` without including exploit details.

**Expectations:**
- We will acknowledge receipt within 5 business days.
- We will respond with an assessment within 10 business days.

## Security Posture

**⚠️ Important:** Next-Gen-Reco is an educational/data-science application. It is **not designed for production deployment** without significant security hardening.

## Security Measures

### Implemented
- **None.** This project has no authentication, no authorization, and no input sanitization.

### Not Implemented (Critical Gaps)
- **No authentication:** The Streamlit app is open to all visitors.
- **No input sanitization:** User-provided search queries are used directly.
- **No rate limiting:** The app can be called unlimited times.
- **No HTTPS:** All communication is plain HTTP.
- **No user isolation:** All users share the same experience and data.

## Data Privacy

- The MovieLens dataset (`movies.csv`, `links.csv`, `tags.csv`) is static and contains no personally identifiable information.
- The optional TMDB API key (if configured) is used solely to fetch movie poster images.
- No user data is collected, stored, or transmitted to external services (except optional TMDB poster fetches).
- Streamlit secrets (`.streamlit/secrets.toml`) contain the TMDB API key — ensure this file is gitignored.

## TMDB API Key Security

The TMDB API key is optional and used only for fetching movie poster images:

- Store the key in `.streamlit/secrets.toml` (which is gitignored by default).
- Never commit the actual key to version control.
- The `.streamlit/secrets.toml.template` file contains a placeholder — replace it with your actual key.
- If deployed on Streamlit Cloud, use the platform's secret management UI, not the file.

## Dependency Security

This project uses scikit-learn, pandas, numpy, and scipy — well-maintained libraries with active security monitoring:

```bash
pip-audit -r requirements.txt
```

## Recommended Hardening

If this application is deployed publicly:

1. Add authentication to the Streamlit app using Streamlit's built-in secrets or an auth proxy.
2. Implement rate limiting at the reverse proxy level.
3. Deploy behind a TLS-terminating reverse proxy (nginx, Caddy).
4. Restrict the TMDB API key to minimal required permissions.
