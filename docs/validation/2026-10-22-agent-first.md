# Agent-first documentation review

The owner requested an agent-first presentation for reshoot, with a short path
from a social post to the first demo and clear guidance for new and experienced
users. This revision changes documentation and package descriptions. Product
behavior, skill instructions, accepted demo media and version numbers are unchanged.

## Entry points

- The [README](../../README.md) leads with the outcome, the existing accepted
  demo and a copyable prompt. That first prompt requires no preinstalled skill.
- The [agent quickstart](../../guide/agent-quickstart.md) covers the first prompt,
  expected outputs, revisions, refresh and review prompts, and installation.
  It includes a short introduction for readers new to coding agents and an
  explicit setup/creation workflow for the receiving agent.
- The [skill catalog](../../skills/README.md) explains the three primary skills,
  the seven supporting skills, invocation conventions and installation routes.
- Guide navigation, the own-app walkthrough, installation, reference,
  contributor guidance and roadmap now lead to the agent workflow. The complete
  CLI tutorial and manual recording guides remain available.
- Package and plugin descriptions use the same positioning. Local X/LinkedIn
  drafts were prepared with a short description, headline and destinations
  suited to different readers. At the owner's subsequent request, those drafts
  are retained in ignored `docs/sharing.md` rather than distributed with the repo.

## Review criteria

The first action is to open a local coding-agent session in the app repository
and paste one prompt. A task and local URL are optional additions. Setup choices
and storyboard details are supplied to the agent through the linked guide.
Installed-skill users can invoke create, refresh or review directly.

The copy describes skills as reusable workflows and the CLI as the recording
and editing tools. It distinguishes the three-skill project installers from
the ten-skill Claude Code plugin. It preserves synthetic data, isolated capture,
result checks, retained attempts and the owner's review decisions. The copy
makes no claim about installation time, novice success or a measured speedup.

Official sources checked for setup and invocation:

- [OpenAI skills documentation](https://developers.openai.com/codex/skills)
  and [quickstart](https://developers.openai.com/codex/quickstart).
- [Claude Code skills](https://code.claude.com/docs/en/skills),
  [plugin installation](https://code.claude.com/docs/en/discover-plugins)
  and [quickstart](https://code.claude.com/docs/en/quickstart).

## Verification

The local audit covers maintained Markdown, relative links, heading anchors,
example syntax, metadata and prompt consistency. Counts and results are retained
in ignored `takes/agent-first-docs/verification.json`, along with a pre-edit
snapshot and two installed skill bundles.

- Both project-local installers succeed. All 12 copied files match the canonical
  primary skill source; each route installs exactly the three documented skills.
- All ten plugin skill folders exist. Package TOML and plugin/marketplace JSON
  parse, and both package and plugin remain version `0.2.0`.
- The README and quickstart contain the same first-demo prompt. Its repository
  URL maps to the new guide in the local working tree.
- Eight TOML examples parse, 45 Bash examples pass syntax checking, and three
  Python examples parse. First-person prose remains in the README's origin only.
- `pytest tests/test_distribution.py`: **1 passed**.
- `claude plugin validate .`: passed with the existing warning that root
  `CLAUDE.md` is not loaded as plugin project context. The workflows are in skills.
- The X draft is 256 literal characters, including its repository URL.
- `git diff --check` passes. Product source, tests and accepted media are unchanged.

No fresh end-to-end session has exercised the new first-demo prompt. Existing
maintainer harness trials establish the underlying creation, refresh and review
workflows; independent new-user testing remains deferred. The new GitHub guide
URL becomes available after the owner commits and pushes these local changes.
No commit, push, publication or new recording approval accompanied this revision.
