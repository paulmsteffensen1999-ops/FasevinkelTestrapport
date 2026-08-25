# Fasevinkel Testrapport

Streamlit-appen genererer en fasevinkel-testrapport med live vektordiagram og PDF-eksport.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://blank-app-template.streamlit.app/)

### Kør lokalt

Prerequisite: install `uv` if you don't already have it.

```
$ curl -LsSf https://astral.sh/uv/install.sh | sh
```

1. Installer dependencies

   ```
   $ uv sync
   ```

2. Start appen

   ```
   $ uv run streamlit run streamlit_app.py
   ```

### Udgiv på `fasevinkel.streamlit.app`

1. Push repositoryet til GitHub.
2. Åbn [share.streamlit.io](https://share.streamlit.io), vælg repositoryets `main`-branch og filen `streamlit_app.py`.
3. Deploy appen.
4. Vælg **Settings** -> **General** -> **App URL**, og angiv `fasevinkel.streamlit.app`, hvis domænet er ledigt.

Streamlit Cloud starter automatisk appen fra `streamlit_app.py` og installerer dependencies fra `pyproject.toml`.
