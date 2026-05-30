# Weather module status

The `weather/` directory is a standalone experimental CLI scraper. It is not
called by MoeChat's main web chat path.

## Current runtime shape

- Main web startup: `main_web.py`
- Main chat request path: `/api/stream_chat` -> `api/chat_api.py` ->
  `core.chat_core`
- Legacy HeWeather branch: `core/external_server.py`
- Standalone scraper CLI: `weather/main.py`

`web/src/router/router.py` intentionally does not mount `core.external_server`,
and `core.chat_core` does not call the scraper in `weather/`.

## Standalone CLI usage

```bash
cd weather
python main.py 今天天气
```

Supported commands are:

- `今天天气`
- `天气`
- `明天`
- `后天`
- `未来一周`

The scraper depends on browser automation packages such as Playwright and
`playwright-stealth`; those dependencies are not part of the main MoeChat
runtime dependencies.

## Requirements for a future chat integration

A future weather integration PR should:

1. choose one weather backend (`core.external_server` HeWeather/QWeather API or
   the `weather/` scraper);
2. add explicit config and dependency declarations for that backend;
3. call the backend from the real `/api/stream_chat` path;
4. surface backend errors in the chat UI instead of silently falling back;
5. add an end-to-end check where a user-visible chat response changes after a
   weather query.
