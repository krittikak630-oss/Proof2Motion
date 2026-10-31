# Graph Report - proof2motion  (2026-10-31)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 200 nodes · 349 edges · 10 communities (8 shown, 2 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 17 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- conftest.py
- create_app
- main.py
- schemas.py
- package.json
- App.jsx
- config.py
- steps
- cloudways_setup.sh

## God Nodes (most connected - your core abstractions)
1. `create_app()` - 28 edges
2. `Settings` - 16 edges
3. `upload()` - 14 edges
4. `App()` - 11 edges
5. `FakeLLM` - 10 edges
6. `LLM` - 9 edges
7. `parse_analysis()` - 8 edges
8. `verify_quotes()` - 8 edges
9. `LLMError` - 7 edges
10. `UploadError` - 7 edges

## Surprising Connections (you probably didn't know these)
- `extract_text()` --uses--> `Settings`  [INFERRED]
  backend/app/extract.py → backend/app/config.py
- `create_app()` --uses--> `Settings`  [INFERRED]
  backend/app/main.py → backend/app/config.py
- `make_client()` --uses--> `Settings`  [INFERRED]
  backend/tests/conftest.py → backend/app/config.py
- `create_app()` --uses--> `ConfigError`  [INFERRED]
  backend/app/main.py → backend/app/llm.py
- `create_app()` --uses--> `LLMError`  [INFERRED]
  backend/app/main.py → backend/app/llm.py

## Import Cycles
- None detected.

## Communities (10 total, 2 thin omitted)

### Community 0 - "conftest.py"
Cohesion: 0.10
Nodes (18): client(), FakeLLM, make_client(), factory(), payload(), upload(), test_analyze_verifies_quotes_and_downgrades_unproven_claims(), test_handles_markdown_fenced_json() (+10 more)

### Community 1 - "create_app"
Cohesion: 0.08
Nodes (12): safe_name(), create_app(), analyze(), consume(), analyze_stream(), body(), prepare(), throttle() (+4 more)

### Community 2 - "main.py"
Cohesion: 0.11
Nodes (4): Settings, ConfigError, LLM, LLMError

### Community 3 - "schemas.py"
Cohesion: 0.13
Nodes (14): run(), Analysis, Claim, _duration(), _page(), Scene, _status(), Support (+6 more)

### Community 4 - "package.json"
Cohesion: 0.12
Nodes (18): dependencies, react@^19.0.0, react-dom@^19.0.0, devDependencies, vite@^6.0.0, @vitejs/plugin-react@^4.3.4, name, private (+10 more)

### Community 5 - "App.jsx"
Cohesion: 0.18
Nodes (16): fetchSample(), LIMITS, parseBlock(), streamAnalyze(), validateFiles(), App(), addFiles(), analyze() (+8 more)

### Community 6 - "config.py"
Cohesion: 0.21
Nodes (5): _bool(), _int(), load_settings(), extract_text(), UploadError

### Community 7 - "steps"
Cohesion: 0.16
Nodes (14): runs-on, steps, runs-on, steps, jobs, backend, frontend, name (+6 more)

## Knowledge Gaps
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `create_app()` connect `create_app` to `conftest.py`, `main.py`, `schemas.py`, `config.py`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `create_app()` (e.g. with `Settings` and `ConfigError`) actually correct?**
  _`create_app()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `conftest.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10252100840336134 - nodes in this community are weakly interconnected._
- **Why does `Settings` connect `main.py` to `conftest.py`, `create_app`, `config.py`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Settings` (e.g. with `extract_text()` and `LLM`) actually correct?**
  _`Settings` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `create_app` be split into smaller, more focused modules?**
  _Cohesion score 0.07956989247311828 - nodes in this community are weakly interconnected._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11330049261083744 - nodes in this community are weakly interconnected._