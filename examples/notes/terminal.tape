# A separate terminal take with VHS: writing and reading a demo text file. Run from the repo root: vhs examples/notes/terminal.tape
# The shell starts clean (env -i), so nothing from your own environment shows: no prompt, history, names or keys.
Output "takes/terminal.mp4"
Set Shell "bash"
Set FontSize 22
Set Width 1280
Set Height 720
Set Padding 28
Set TypingSpeed 55ms
Set Theme "Catppuccin Mocha"
Hide
Type "env -i HOME=/tmp/reshoot-demo PATH=/usr/bin:/bin:/opt/homebrew/bin TERM=xterm-256color LANG=en_US.UTF-8 PS1='~/demo $ ' bash --noprofile --norc" Enter
Type "mkdir -p ~ && cd ~ && rm -f notes.txt && clear" Enter
Sleep 500ms
Show
Sleep 1s
Type "echo 'Pick up the bikes from the shop' >> notes.txt"
Sleep 400ms
Enter
Sleep 600ms
Type "cat notes.txt"
Sleep 400ms
Enter
# A fixed Sleep, never a Wait: when a Wait times out, VHS throws away the whole recording.
# Afterwards, `reshoot last-change takes/terminal.mp4` says where to cut.
Sleep 3s
