# Claude Agent Team

This repository is configured for **Claude Code agent teams** — an experimental feature that enables multiple Claude Code instances to work in parallel on coordinated tasks.

## Quick Start

1. Open this project in Claude Code
2. Agent teams are already enabled via `.claude/settings.json`
3. Ask Claude to create a team:

```
Create an agent team with 3 teammates to [describe your task]
```

## What Are Agent Teams?

Instead of a single Claude agent working sequentially, a **lead agent** can delegate to multiple **teammates** that work in parallel:

| Component     | Role                                                |
|---------------|-----------------------------------------------------|
| **Team Lead** | Your main Claude Code session; spawns and coordinates teammates |
| **Teammates** | Independent Claude Code instances with their own context |
| **Task List** | Shared work items with dependency tracking          |
| **Mailbox**   | Inter-agent messaging for direct communication      |

## Configuration

Agent teams are enabled in `.claude/settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

## Usage Examples

- **Code review**: Spawn reviewers focused on security, performance, and test coverage
- **Feature development**: Split work across data layer, API, and tests
- **Research**: Parallelize codebase documentation and analysis
- **Debugging**: Test competing hypotheses simultaneously

See [CLAUDE.md](CLAUDE.md) for detailed agent instructions and best practices.
