# Using this repo with Cursor

This project includes a **Cursor project rule**, so the cooperative-principle guidelines apply automatically when you work here.

## In this repository

1. Open the folder in Cursor.
2. The rule [`.cursor/rules/cooperative-principle.mdc`](.cursor/rules/cooperative-principle.mdc) is committed with `alwaysApply: true`, so no extra installation is needed.
3. To confirm, open **Settings → Rules** (or the project rules UI). `cooperative-principle` should be listed.

## Use the same guidelines in another project

**Cursor (recommended):** Copy `.cursor/rules/cooperative-principle.mdc` into that project's `.cursor/rules/` directory (create the folders if needed). Merge it with existing rules as you like.

**Other tools:** If a tool only supports a root instruction file, copy [`CLAUDE.md`](CLAUDE.md) into that project instead (or merge its contents into your existing instructions).

## Optional: personal Agent Skills

To use the same content as a reusable skill under `~/.cursor/skills`, copy or symlink [`skills/cooperative-principle/`](skills/cooperative-principle/) into your personal skills directory.

## Claude Code vs Cursor

- **Claude Code:** Install through the plugin marketplace as described in [`README.md`](README.md); the plugin exposes the skill from this repo. For always-on use in one project, use `CLAUDE.md`.
- **Cursor:** Use the committed `.cursor/rules/` file as described above. Cursor does not read `.claude-plugin/` or `CLAUDE.md` by default.

## For contributors

[`skills/cooperative-principle/SKILL.md`](skills/cooperative-principle/SKILL.md) is the source text. When you change the maxims, update **[`CLAUDE.md`](CLAUDE.md)** and **[`.cursor/rules/cooperative-principle.mdc`](.cursor/rules/cooperative-principle.mdc)** to match. Keep the quoted wording of Grice's principle and maxims exactly as in the 1975 source, and update the page references if you quote anything new.
