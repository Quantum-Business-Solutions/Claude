# Project: Claude Agent Team

This repository is configured for Claude Code agent teams — multiple Claude Code instances working in parallel on coordinated tasks.

## Agent Teams Setup

Agent teams are **enabled** via `.claude/settings.json`. The lead agent can spawn teammates that work independently and communicate through a shared task list and mailbox system.

## How to Use Agent Teams

Describe your task and team structure in natural language. Examples:

### Code Review Team
```
Create an agent team to review PR #42. Spawn three reviewers:
- One focused on security implications
- One checking performance impact
- One validating test coverage
Have them each review and report findings.
```

### Feature Implementation Team
```
Create an agent team to build a REST API. Spawn teammates:
- One to implement the data models and database layer
- One to build the API routes and controllers
- One to write integration tests
```

### Research Team
```
Create an agent team to research our codebase. Spawn teammates:
- One to document the authentication flow
- One to map out the database schema
- One to catalog all API endpoints
```

## Best Practices

1. **Give specific context** — Teammates don't inherit conversation history; be explicit in spawn prompts
2. **Avoid file conflicts** — Structure work so each teammate owns different files
3. **Size tasks well** — Aim for 5-6 tasks per teammate
4. **Start read-only** — Try code review or research tasks before parallel implementation
5. **Monitor progress** — Check in on teammates and redirect when needed

## Team Controls

- **Shift+Tab**: Toggle delegate mode (restricts lead to coordination only)
- **Shift+Up/Down**: Select and message individual teammates
- **Split panes**: Use tmux or iTerm2 for separate terminal panes per teammate

## Project Structure

```
.
├── CLAUDE.md              # This file — agent instructions
├── README.md              # Project overview
└── .claude/
    └── settings.json      # Agent teams enabled here
```
