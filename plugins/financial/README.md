# Financial plugin status

The financial recorder is currently a standalone/opt-in plugin. MoeChat's main
FastAPI chat path does not initialize `financial_plugin_hook()` or inject its
result into `chat_core`, so setting `financial_plugin.enabled: true` alone does
not make financial messages visible in the normal chat UI.

## Current runtime shape

- Standalone API/UI: `plugins/financial/balancer/app.py`
- Plugin hook: `plugins/financial/plugin.py`
- Default plugin config: `plugins/financial/config.yml`
- Main chat runtime: `/api/stream_chat` and `/api/chat` call `core.chat_core`
  directly and do not call the financial hook.

## How to run the standalone recorder

```bash
cd plugins/financial/balancer
python app.py
```

By default the standalone recorder listens on `127.0.0.1:5000`. Override it with:

```bash
MOECHAT_FINANCIAL_HOST=127.0.0.1 MOECHAT_FINANCIAL_PORT=5050 python app.py
```

## Enabling integration later

A future integration PR should:

1. add a main-runtime feature flag;
2. initialize the plugin once during server startup;
3. call `financial_plugin_hook()` from the chat path;
4. convert `llm_context` into user-visible chat feedback;
5. include an end-to-end check where a real chat message records or rejects a
   transaction through the standalone API.
