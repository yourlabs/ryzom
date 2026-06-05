# Vendored assets — autocomplete-light

`autocomplete-light.css` / `autocomplete-light.js` are the standalone yourlabs
autocomplete web component, vendored into this app's static dir so the project no
longer depends on the `autocomplete-light` Python package (which shipped only
these two files plus Selenium test helpers we don't use).

- Source: https://yourlabs.io/oss/autocomplete-light
- Version: 1.1.6.dev7
- Commit: 6a732bef6ca2321f6eb464449acd0c8c73b5be75

They are served at `STATIC_URL + autocomplete_light/autocomplete-light.{css,js}`
via the staticfiles app-dirs finder — `ryzom_django_autocomplete/html.py` loads
them with `Static('autocomplete_light/...')`. To update, re-copy from upstream and
bump the version/commit above.
