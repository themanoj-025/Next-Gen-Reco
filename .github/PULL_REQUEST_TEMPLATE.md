## Description

Please include a summary of the changes and the related issue. What problem does this PR solve?

Fixes # (issue)

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Model / algorithm improvement
- [ ] Data pipeline / preprocessing changes
- [ ] UI/UX enhancement (Streamlit)
- [ ] Documentation update
- [ ] Refactoring / code cleanup
- [ ] Breaking change (fix or feature that would cause existing functionality to change)

## Areas Affected

- [ ] Recommendation model (`app/model.py`, `app/recommender.py`)
- [ ] Data enrichment (`app/enrichment.py`)
- [ ] Streamlit app (`app/main.py` or `app.py`)
- [ ] Data files (MovieLens)
- [ ] TMDB integration
- [ ] Notebooks / scripts
- [ ] Testing (`tests/`)

## Testing

- [ ] `pytest tests/` — tests pass
- [ ] Streamlit app loads without errors
- [ ] Recommendations are generated correctly
- [ ] Model accuracy is maintained (or improved)

## Checklist

- [ ] My code follows the existing project conventions and style
- [ ] I have updated documentation if needed
- [ ] I have updated `.streamlit/secrets.toml.template` if new secrets are required
- [ ] My changes do not introduce new warnings or errors
- [ ] I have verified the app works with the default MovieLens dataset

## Additional Context

Add any other context about the PR here, such as performance benchmarks or dataset changes.
