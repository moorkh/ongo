# Contributing to ongo

## Setup

ongo is a Claude Code skill plugin. The skill itself lives in
`plugins/ongo/skills/ongo/` (`SKILL.md` plus the stdlib Python helpers in
`bin/`). No build step or dependency install is required to work on it; a
Python 3 interpreter is enough to run the checks below.

```bash
git clone https://github.com/zomglings/ongo.git
cd ongo
```

## Checks

Before opening a PR, run all checks:

```bash
python3 -m py_compile plugins/ongo/skills/ongo/bin/ongo-site
python3 -m py_compile plugins/ongo/skills/ongo/bin/ongo-serve
python3 -m py_compile plugins/ongo/skills/ongo/bin/ongo-poll
python3 -m py_compile plugins/ongo/skills/ongo/bin/ongo-delete
```

If you change `SKILL.md`, re-read it start to finish for internal
consistency (the loop invariants, the pubkind guard pattern, and the
static-site sections must not contradict each other).

## Version bumps

Every PR must bump the `version:` field in
`plugins/ongo/skills/ongo/SKILL.md` (the YAML frontmatter at the top,
alongside `name: ongo`) **unless the PR ONLY touches documentation** —
top-level `*.md` files, the `docs/` directory, or `.github/`. If your
change touches the skill instructions, the `bin/` helpers, or any
configuration, bump the version.

`SKILL.md`'s `version:` frontmatter field is the **single source of truth**
for the skill version. A CI check (`.github/workflows/version-bump-check.yml`)
enforces this on every pull request to `main`.

## Pull requests

- Branch from `main`.
- Keep PRs focused — one logical change per PR.
- Make sure all checks pass before requesting review.
