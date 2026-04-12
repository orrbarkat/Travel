# CLAUDE.md

This is a living document. Update it whenever Claude makes a mistake so it doesn't repeat next time.

## Project Overview

Travel - a travel planning application.
License: MIT (orrbarkat)

## Development Workflow

1. Make changes
2. Typecheck: `npm run typecheck`
3. Run tests: `npm test -- --grep "test name"` (single) or `npm test` (all)
4. Lint: `npm run lint -- --fix`
5. Before committing: ensure all checks pass

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
