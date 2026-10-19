# A VHS tape. Record it with: vhs this.tape
Output "takes/cli.mp4"
Set Shell "bash"
Set FontSize 22
Set Width 1280
Set Height 720
Set Padding 28
Set TypingSpeed 55ms
Set Theme "Catppuccin Mocha"

# Setup, not recorded: a clean shell with nothing private in it, in a demo folder, with the last take's files gone.
Hide
Type "env -i HOME=/tmp/demo PATH=/usr/bin:/bin:/opt/homebrew/bin TERM=xterm-256color LANG=en_US.UTF-8 PS1='~/demo $ ' bash --noprofile --norc" Enter
Type "mkdir -p ~ && cd ~ && clear" Enter
Sleep 500ms
Show

Sleep 1s
Type "echo hello"
Sleep 400ms
Enter

# A fixed Sleep, never a Wait: when a Wait times out, VHS throws away the whole recording.
# Make it longer than the slowest run, then cut at `reshoot last-change takes/cli.mp4`.
Sleep 3s
