# CLAUDE.md

This is a living document. Update it whenever Claude makes a mistake so it doesn't repeat next time.

## Project Overview

Flight stopover optimization engine — DuckDB + Python + Streamlit system that finds cheap stopover deals for flights. Inspired by @mluggy's viral X post about using Claude + SQL to find deals like 2-3 days in Madrid on the way to Portugal, saving 40-60% vs direct.

License: MIT (orrbarkat)

## Repository Structure

```
Travel/
├── schema.sql       — DuckDB DDL (source of truth for all table definitions)
├── load_data.py     — Data generation + loading (airports, airlines, routes, prices)
├── engine.py        — Core SQL query functions (all return pandas DataFrames)
├── claude_prompt.py — System prompt generator for Claude-as-travel-agent
├── cli.py           — CLI interface (click + rich)
├── app.py           — Streamlit web dashboard
├── README.md        — User-facing documentation
└── PLAN.md          — Implementation plan with per-PR breakdown
```

## Development Workflow

1. Make changes
2. Test data loading: `python load_data.py`
3. Test queries: `python -c "from engine import find_stopover_deals; print(find_stopover_deals('TLV','LIS','2026-07-01','2026-07-31'))"`
4. Test CLI: `python cli.py stopover TLV LIS`
5. Test dashboard: `streamlit run app.py`
6. Before committing: ensure all checks pass

## Per-PR Agent Instructions

See `PLAN.md` for the full PR breakdown and per-PR agent instructions.

## Key Technical Decisions

- **Database**: DuckDB (embedded, analytical SQL, zero-config)
- **Currency**: Store both `price_usd` and `price_ils` at load time (USD_ILS_RATE = 3.65)
- **Imports**: engine.py is the shared query layer — cli.py, app.py, and claude_prompt.py all import from it
- **Maps**: Plotly Scattergeo (not Folium) for native Streamlit support
- **Connections**: Read-only everywhere except load_data.py to prevent DuckDB write contention
- **Branch**: `claude/flight-optimization-engine-7i3P2`

## Planning & Execution

- Enter plan mode (Shift+Tab x2) for any non-trivial task (3+ steps)
- Iterate on the plan until solid before writing code
- If something goes sideways, stop and re-plan immediately
- Write detailed specs upfront to reduce ambiguity

## Verification

- Never mark a task complete without proving it works
- Run tests and check output before reporting success
- For UI changes: visually verify in the browser
- Ask yourself: "Would a staff engineer approve this?"

## Code Standards

- Write clear, simple code; avoid premature abstractions
- No unnecessary error handling for impossible scenarios
- Don't add features beyond what was asked
- Three similar lines > a premature abstraction
- Only add comments where the logic isn't self-evident
- Prefer editing existing files over creating new ones

## Git Conventions

- Write concise commit messages focused on "why" not "what"
- One logical change per commit
- Never force-push to main

## Subagents

- Use subagents for independent subtasks to keep main context clean
- One task per subagent for focused execution
- For complex problems, parallelize with multiple subagents

## Lessons Learned
