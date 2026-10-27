# Research: API-key access and tier models at install time

Scope: facts a planner needs for roadmap item 4 ("Configurable model tiers for alternative
providers"), widened by the user's request (2026-10-27): user-friendly API access for static-key
providers (OpenRouter, NRP) and token-helper environments (ALCF `inference.alcf.anl.gov`), a
pick-from-list model per tier (Fable/Opus/Sonnet/Haiku), installed into separate profiles, with
the subscription workflow unchanged. No design is proposed. Web sources fetched 2026-10-27;
Claude Code docs describe a 2.1.3xx release (local `claude --version`: 2.1.312).

## 1. Repo state

Roadmap item, verbatim (`.supervisor/roadmap.md:63-69`):

> ### 4. Configurable model tiers for alternative providers
> Let users map the Opus/Fable, Sonnet and Haiku tiers to custom model names when using local or
> third-party providers that implement the Anthropic API via API keys. Owner direction
> (2026-10-21): when an install is configured with an API key, `deploy` asks whether to configure
> the tiers, lists the provider's available models, and lets the user pick one per tier by number
> or by typing a name. `deploy` stays standard-library-only.
> Priority: normal. Effort: M.

It cites no `Decisions:` entries and names three tiers ("Opus/Fable" as one); the user now names
four.

Memory entries that bind. None of their `affects:` paths changed in token or Fable logic since
`verified:` (`git log --since="2026-10-24 23:59:59" -- deploy docs/deploy.md`: 136b621, 11d1906,
42b57ca, docs and Codex critic only).
- `decisions/2026-10-22-install-target-comes-from-flags-only.md`: "the target comes from
  `--tag`/`--target`, never from `$CLAUDE_CONFIG_DIR`, and a profile resolving to `~/.claude` is
  refused."
- `decisions/2026-10-22-installs-never-need-the-source-checkout.md`: "Any run-time need of the
  checkout is a defect unless the user names one (`update --from`)."
- `decisions/2026-10-23-fable-is-default-opus-is-opt-in.md`: "choosing Opus is the user's explicit
  act, either `--fable-is-opus` per session or their own `ANTHROPIC_DEFAULT_FABLE_MODEL` ... agent
  files keep `model: fable`. ... earlier rejections stand: `CLAUDE_CODE_SUBAGENT_MODEL` (overrides
  every subagent) and an install-time rewrite."
- `decisions/2026-10-24-deploy-never-detects-the-plan-or-model.md`: "Deploy never detects the plan
  or model: no prompt, no auto value, no saved Fable choice." Its rationale concerns reading the
  subscription plan; whether "no prompt" also covers a tier picker on provider installs is an
  open question.
- `decisions/2026-10-24-product-text-says-profile-never-sandbox.md`: "A profile is a private
  config dir `~/.config/claude-<tag>` with its own launcher; several coexist via `--tag`."
- `facts/2026-10-24-claude-config-dir-gives-each-dir-its-own.md`: each `CLAUDE_CONFIG_DIR` has its
  own login (macOS Keychain keyed to the literal dir string); "a launcher bakes the absolute
  resolved path".
- Archived `archive/memory/decisions/2026-10-21-provider-flags-write-a-0600-token-file.md`
  (superseded by `docs/deploy.md`): "The secret never appears in the manifest, `settings.json`,
  install output or `status` output ... Neither URL nor token is validated." `docs/deploy.md`
  does not restate the secrecy rule.

## 2. Current `deploy` behaviour

- **Profile.** A profile is `~/.config/claude-<tag>` (default tag `supervisor`) plus a generated
  POSIX sh launcher `<prefix>/bin/claude-<tag>` (`deploy:80-113`, `launcher_text`). The launcher
  exports `CLAUDE_CONFIG_DIR='<abs target>'` (`deploy:103`) and runs `exec claude "$@"`.
- **`--global`.** Installs into `~/.claude` with no launcher, and rejects `--tag`, `--target`,
  `--base-url`, `--token` and `--token-file` (`deploy:202-207`).
- **Seeding.** A profile's first install copies `~/.claude/settings.json` (minus `agent`),
  `CLAUDE.md`, `commands/` and more (`deploy:49-50`, `docs/deploy.md:55`). A global `env` block,
  any `ANTHROPIC_*` value included, is copied into every new profile.
- **`settings.json` writes.** Install sets `agent`, `attribution.*` in profiles, and one
  `permissions.allow` rule (`docs/deploy.md:31,51,166`). It writes no `env`, `model` or
  `apiKeyHelper` today.
- **Token provider (already shipped).** `install --base-url URL` with `--token-file PATH` or
  `--token VALUE` (`deploy:1757-1760`), profile only. The token goes to `<dir>/token`, mode 0600
  (`deploy:970-971`); the manifest records only `base_url` (`deploy:956`). Launcher lines
  `deploy:104-108`:
  ```
  ANTHROPIC_BASE_URL='<url>'; export ANTHROPIC_BASE_URL
  ANTHROPIC_AUTH_TOKEN="$(cat '<dir>/token')"; export ANTHROPIC_AUTH_TOKEN
  ```
  `install` and `update` keep both; `--base-url ''` clears the URL, and deleting the file drops
  the token (`docs/deploy.md:62-68,113`). The flow has no model selection, no
  `ANTHROPIC_API_KEY=""`, no model-list fetch and no validation.
- **HTTP and prompts.** From `urllib`, `deploy` imports only `urllib.parse` (`deploy:24`).
  `urllib.request` is stdlib. `confirm` (`deploy:186-191`) needs a TTY; `--yes` skips it.
- **Fable.** `--fable-is-opus` exports `ANTHROPIC_DEFAULT_FABLE_MODEL='claude-opus-5-5'`
  (`OPUS_MODEL`, `deploy:55-56,109`); otherwise the variable is left alone
  (`docs/deploy.md:137-153`). No non-Claude provider serves that id, so on a provider profile the
  flag would break the Fable agents.
- **Subscription workflow to preserve.** `./deploy install` (no provider flags), then
  `claude-supervisor`, then `/login` once (`docs/deploy.md:21-31`). The launcher exports only
  `CLAUDE_CONFIG_DIR` plus the optional Fable line.

Tiers in the pack:
- Frontmatter: fable (supervisor, planner, writer, scope-critic); opus (researcher, executor,
  critic, writer-worker); sonnet (the three workers, curator); haiku (fixer, git-ops, scout).
- Per-call overrides: `pack/agents/planner.md:57` (`critic` on `model: fable`) and
  `pack/agents/supervisor.md:50` (`writer` on `model: opus`), both listed in
  `pack/skills/agent-authoring/SKILL.md:23-24`.
- Inventory: `docs/architecture.md:20-36,90-92`.
- Lint: `tests/test_pack_lint.py:18` allows `{fable, opus, sonnet, haiku, inherit}`; `:104-105`
  also allows ids starting with `claude-`; `:115` requires frontmatter to match the
  agent-authoring Tiers table. A non-Claude id in frontmatter fails the lint.
- `doctor` warns on `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` and `CLAUDE_CODE_EFFORT_LEVEL`
  (`deploy:1650-1667`).
- `deploy` resolves no alias: Claude Code maps each alias through `ANTHROPIC_DEFAULT_<TIER>_MODEL`
  (section 3).

## 3. Claude Code mechanics (official docs)

Sources: https://code.claude.com/docs/en/env-vars, `/settings-reference`, `/model-config`,
`/sub-agents`, `/authentication`, `/llm-gateway`.

- **Credentials.** `ANTHROPIC_API_KEY` is "sent as `X-Api-Key` header ... used instead of your
  Claude Pro, Max, Team, or Enterprise subscription even if you are logged in."
  `ANTHROPIC_AUTH_TOKEN` is the "Custom value for the `Authorization` header (... prefixed with
  `Bearer `)". `ANTHROPIC_BASE_URL` overrides the endpoint; `ANTHROPIC_CUSTOM_HEADERS` adds
  headers.
- **Precedence** (authentication), highest first: cloud-provider vars, then
  `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_API_KEY`, `apiKeyHelper`, `CLAUDE_CODE_OAUTH_TOKEN`, profile
  or federation credentials, and last the `/login` OAuth. A base URL with no credential keeps
  using the claude.ai login.
- **Approval prompt.** In interactive mode Claude Code asks once to approve an
  `ANTHROPIC_API_KEY` (toggle in `/config`). `-p` always uses it. No prompt is documented for
  `ANTHROPIC_AUTH_TOKEN`.
- **`apiKeyHelper`** (settings-reference):
  - It runs a shell command and "sends its output as both the `X-Api-Key` and
    `Authorization: Bearer` headers".
  - It re-runs after 5 min (`CLAUDE_CODE_API_KEY_HELPER_TTL_MS`), on 401/403, and on an expired
    JWT; the last two "only when ... `ANTHROPIC_AUTH_TOKEN` isn't set".
  - A failing or empty helper fails requests. The docs recommend a helper over `env` for
    credentials.
  - Consequence: today's launcher exports a static `ANTHROPIC_AUTH_TOKEN`, which outranks any
    helper and never refreshes within a session. A shell `ANTHROPIC_API_KEY` also outranks a
    helper.
- **Tier models.** `ANTHROPIC_DEFAULT_OPUS_MODEL`, `_SONNET_MODEL`, `_HAIKU_MODEL` (also used "for
  background functionality") and **`ANTHROPIC_DEFAULT_FABLE_MODEL`**, the "Model ID that the
  `fable` alias resolves to". Each has `_NAME`, `_DESCRIPTION` and `_SUPPORTED_CAPABILITIES`
  variants. Related:
  - Main model: `--model` > `ANTHROPIC_MODEL` > settings `model` > `ANTHROPIC_DEFAULT_MODEL`.
  - `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1` fills `/model` from the gateway's `/v1/models`;
    `ANTHROPIC_CUSTOM_MODEL_OPTION` adds one picker entry.
  - `availableModels` blocks redirecting an alias to a model outside its list.
- **Subagent resolution** (sub-agents): frontmatter accepts `sonnet`, `opus`, `haiku`, `fable`, a
  full id or `inherit`. Order: per-invocation `model`, then frontmatter, then
  `CLAUDE_CODE_SUBAGENT_MODEL`, then the main model. Aliases resolve through
  `ANTHROPIC_DEFAULT_<TIER>_MODEL`, so the four variables remap every pack agent and both per-call
  overrides with agent files unchanged.
- **Profiles.** `CLAUDE_CONFIG_DIR` holds settings, history, plugins and credentials; each dir has
  "its own settings, session history, and claude.ai login or API key". `settings.json` `env`
  applies "for every session and for the subprocesses Claude Code starts" and overwrites the same
  shell export. A profile can therefore be self-contained: base URL, credential or helper, and
  tier models. Consequence: a seeded or user `env` value beats any launcher export, including
  `--fable-is-opus` (as `docs/deploy.md:153` already says).
- **Wire format** (llm-gateway protocol):
  - A gateway "must expose at least one of" Anthropic Messages (`/v1/messages`, optional
    `/v1/messages/count_tokens`), Bedrock InvokeModel or Vertex rawPredict, and must forward
    `anthropic-beta`/`anthropic-version`.
  - No OpenAI `/v1/chat/completions` support is documented.
  - Anthropic "doesn't support routing Claude Code to non-Claude models through any gateway"; it
    works in practice but is unsupported, and tool-calling quality varies by model.
- **Knobs for non-Anthropic backends** (env-vars): `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS`,
  `DISABLE_PROMPT_CACHING`, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`,
  `CLAUDE_CODE_DISABLE_THINKING`, `CLAUDE_CODE_MAX_CONTEXT_TOKENS`, `API_TIMEOUT_MS`. Claude Code
  assumes a 200k context unless the model name ends in `[1m]` (OpenRouter page).

## 4. Providers

### (a) OpenRouter (https://openrouter.ai/docs/guides/guides/claude-code-integration)
- Native Anthropic route: `ANTHROPIC_BASE_URL=https://openrouter.ai/api` ("no `/v1`"),
  `ANTHROPIC_AUTH_TOKEN=<key>` ("not in ANTHROPIC_API_KEY"), `ANTHROPIC_API_KEY=""` ("Must be
  explicitly empty"). Optional: gateway model discovery and the four `ANTHROPIC_DEFAULT_*`.
- The page advises `/logout` if previously logged in; non-Anthropic models are "not guaranteed".

### (b) NRP (https://nrp.ai/documentation/userdocs/ai/llm-managed/)
- The client-configs page has a Claude Code recipe: "Claude Code talks to NRP through the
  Anthropic-compatible endpoint at `/anthropic`", with
  `ANTHROPIC_BASE_URL=https://ellm.nrp-nautilus.io/anthropic` and `ANTHROPIC_AUTH_TOKEN`. It also
  sets:
  - `ANTHROPIC_MODEL` and `ANTHROPIC_DEFAULT_{OPUS,SONNET,HAIKU,FABLE}_MODEL` to NRP names;
  - `CLAUDE_CODE_SUBAGENT_MODEL`, `CLAUDE_CODE_AUTO_COMPACT_WINDOW`, `ENABLE_TOOL_SEARCH=false`;
  - `CLAUDE_CODE_EFFORT_LEVEL=max`, which `doctor` warns on (section 2);
  - long timeouts, retries, and telemetry off.

  `CLAUDE_CODE_SUBAGENT_MODEL` ranks below frontmatter, so it would touch no pack agent, but the
  Fable decision rejects it.
- Caveats: not all NRP models route cleanly through the Anthropic-compatible endpoint, and Web
  Search does not work.
- Token: static, from https://nrp.ai/llmtoken, for members of an LLM-flagged group, sent as
  `Authorization: Bearer`. The OpenAI base is `https://ellm.nrp-nautilus.io/v1` (Envoy AI
  gateway).
- Published list (`.../llm-managed/models`): `qwen3`, `qwen3-small`, `gpt-oss`, `gemma` (main);
  `gemma-small`, `kimi`, `glm-5`, `deepseek-v4-flash`, `minimax` (evaluating). Contexts run
  131k-1M, with tool calling on all chat models.

### (c) ALCF (https://docs.alcf.anl.gov/services/inference-endpoints/)
- Host `https://inference-api.alcf.anl.gov`. OpenAI-style bases are
  `/resource_server/sophia/vllm/v1` and `/resource_server/{metis,minerva,tara}/api/v1`.
- The Agents page (https://docs.alcf.anl.gov/services/inference-endpoints/agents/, updated
  2026-10-22) has a Claude Code recipe in `~/.claude/settings.json` `env`:
  - `ANTHROPIC_BASE_URL=https://inference-api.alcf.anl.gov/resource_server/minerva/api`, which
    "intentionally omits the trailing `/v1`";
  - `ANTHROPIC_AUTH_TOKEN`;
  - `ANTHROPIC_DEFAULT_{OPUS,SONNET,HAIKU}_MODEL=muse-spark-bf16`.

  Claude Code needs "a Direct API-backed endpoint that supports the Anthropic Messages API ...
  (i.e. Minerva or Tara)"; by implication Sophia (vLLM) and Metis need a shim.
- `alcf-ai agent configure claude` writes that configuration (`-m` default model
  `muse-spark-bf16`, `-c` default cluster `minerva`). "When a token helper (`alcf-tokens` or
  `alcf-ai`) is on your `PATH`, the generated configuration refreshes access tokens
  automatically". Otherwise it "embeds the current access token and warns you to re-run". It
  installs with pip, uv or pipx (https://pypi.org/project/alcf-ai/), so it is not stdlib.
- Auth: `alcf-tokens login inference`, then `alcf-tokens get-token inference`. The older
  `inference_auth_token.py` is deprecated and keeps a separate cache. "Access tokens are valid for
  48 hours"; get-token refreshes automatically; "re-authentication every 30 days".
- `apiKeyHelper: "alcf-tokens get-token inference"` fits the helper contract on paper; untested.
- Community shim `alcf-proxy` (https://alcf-proxy.readthedocs.io/en/latest/): `pip install`, a
  resident `alcf-proxy serve` on `localhost:11445` exposing `/v1/messages`, with token refresh and
  cluster failover.

### (d) Bridges for OpenAI-only backends
- LiteLLM proxy (https://docs.litellm.ai/docs/tutorials/claude_responses_api):
  - Install and run with `pip install 'litellm[proxy]'` and `litellm --config config.yaml`, which
    serves `/v1/messages` on port 4000.
  - Its `model_list[].model_name` must equal the `ANTHROPIC_DEFAULT_*` values.
  - It supports `apiKeyHelper`.
- claude-code-router (https://github.com/musistudio/claude-code-router): installed with
  `npm i -g @musistudio/claude-code-router` (Node 22+); runs a gateway on `127.0.0.1:3456`.
- Each bridge adds a non-stdlib runtime and a resident process outside `deploy`'s control. That
  includes `alcf-proxy`.

## 5. Model listing for a pick-list
- **OpenRouter.** `GET https://openrouter.ai/api/v1/models?supported_parameters=tools`
  (https://openrouter.ai/docs/api/api-reference/models/get-models).
  - Response: `{data[], total_count, links}`. Each entry has `id`, `name`, `context_length`,
    `pricing` and `supported_parameters`. Filters include `category` and `limit` (up to 1000).
  - Today's unauthenticated curl returned 200, with 464 models in all and 373 with `tools`. The
    spec declares bearer auth.
- **NRP.** `GET https://ellm.nrp-nautilus.io/v1/models` with `Authorization: Bearer <token>`
  returns `{data:[{id,created,object,owned_by}]}`, ids only. Context and tool data are on the
  docs page. An unauthenticated curl returned 200.
- **ALCF.** `alcf-ai ls-models <cluster>` lists a cluster's models with capabilities (raw API
  response). `alcf-proxy models` is the alternative.
- **Common shape.** OpenAI-style `{data:[{id}]}`. Claude Code's own gateway discovery reads the
  same shape from `<base>/v1/models`. The HTTPS calls take a bearer header and work with
  `urllib.request`.

## Constraints the plan must respect
- `deploy` stays stdlib-only and runs on Python 3.9 (`/usr/bin/python3`). Validate with
  py_compile, `--help`, and a dry-run install under a fresh `HOME`.
- No provider flags means today's launcher and settings byte for byte, and no new prompts.
  `--global` keeps rejecting provider flags unless the owner decides otherwise.
- Agent files keep `model: fable|opus|sonnet|haiku`. Non-`claude-` ids fail the lint, and the
  Fable decision rejects install-time rewrites and `CLAUDE_CODE_SUBAGENT_MODEL`, so tier mapping
  goes through `ANTHROPIC_DEFAULT_*_MODEL`.
- Targets come from flags only, and launchers bake absolute paths.
- Secrets never appear in the manifest, output or `status`, and the token file is 0600.
- No run-time dependency on the checkout. `update` re-applies recorded options from a fresh
  clone, so a recorded tier choice must survive it.
- Sync `docs/deploy.md` (Token Provider, Fable Or Opus), `docs/architecture.md` (Models And Cost)
  and the provider tests in `tests/test_deploy.py` (`:840`, `:2141`, `:2397`; help flags `:428`).
  Bump `VERSION` per `CLAUDE.md`.

## Open questions for the user
1. Does "deploy never prompts about the model" (2026-10-24) allow an interactive tier picker on
   provider installs, as the 2026-10-21 roadmap direction asks?
2. On a provider profile, should `--fable-is-opus` be refused, ignored, or remapped to the chosen
   Opus-tier model?

## Unverified
- Whether `alcf-tokens get-token inference` prints only the token. What `alcf-ai agent configure
  claude` writes for refresh (`apiKeyHelper` or another mechanism). The `ls-models` output shape.
- Where the API-key approval is stored (assumed `customApiKeyResponses` in `.claude.json`), and
  whether `.claude.json` moves under `CLAUDE_CONFIG_DIR`.
- Whether subagents receive the `settings.json` `env`. They run in-process, so it is likely.
- Tool-use fidelity of any bridge or non-Claude model.
- The authentication, sub-agents and llm-gateway pages, precedence order included, were read
  through WebFetch summaries, not raw text.
