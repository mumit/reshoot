---
name: record-terminal
description: Record a terminal take with VHS, such as a CLI or an AI agent like Claude Code doing a task, with a clean shell that shows nothing private. Use for the terminal part of a demo video.
---

# Record a terminal take

VHS (`brew install vhs`) plays a tape file in its own terminal and writes a video. Nothing outside that terminal can
show. `template.tape` next to this file is a starting point; `../../examples/notes/terminal.tape` is a full example.

## Steps

1. Copy `template.tape` into the project and set `Output`, the size and the commands.
2. Do the setup inside `Hide` ... `Show`: start a clean shell, `cd` to a demo folder, remove what the last take left
   behind, `clear`.
3. Record: `vhs tools/demo/cli.tape`.
4. Find where it finished: `reshoot last-change takes/cli.mp4` prints the time of the last real change. Cut there.
5. Look at the last frame and a few in the middle before going on.

## A clean shell

The shell must not show the person's name, machine, folders, history, prompt theme or any key:

```
Type "env -i HOME=/tmp/demo PATH=/usr/bin:/bin:/opt/homebrew/bin TERM=xterm-256color LANG=en_US.UTF-8 PS1='~/demo $ ' bash --noprofile --norc" Enter
```

Add only the variables the command needs. Never pass an API key on a typed line: it shows in the video.

## AI agent takes

These notes are for Claude Code. Other agents need the same care: their own config, a demo folder, few tools.

- Run Claude from its own config folder, so the banner and settings show nothing of the person's: log in once with
  `CLAUDE_CONFIG_DIR=~/.claude-demo claude`, with the account that should appear.
- Start it in a demo folder under `/tmp`: the banner shows the folder.
- Give it only the tools the take needs: `--mcp-config demo.json --strict-mcp-config --allowedTools ...`.
- Claude's time varies from run to run. Use a long fixed `Sleep` (longer than its slowest run) and cut at
  `reshoot last-change`. Speed the working part up in the cut, with a label like "8x speed".
- Read the agent's answer in the take. It may describe or name things that need checking too.

## Pitfalls

- **Never use `Wait`.** When a `Wait` times out, VHS throws away the whole recording. Use `Sleep` and cut afterwards.
- **Quotes in typed text.** Wrap a `Type` string that has double quotes in backticks: ``Type `say "hi"` ``.
- **Leftovers from the last take** change what the next one shows. Clean up in the hidden setup.
- **Typing time.** The typed part lasts about the number of characters times `TypingSpeed`. Use that to find where
  the typing ends, if the cut needs it.
- **Two things driving the same app.** If the take drives an app (a desktop app, a database), don't touch that app
  from anywhere else while it runs. Some apps stall when two scripts drive them at once.
