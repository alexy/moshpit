This is a set of configuration files for Mac and Linux to run a remote tmux session under mosh and copy-paste between them.

The Mac, under tmux, needs a way to copy to the system clipboard.  

The remote Linux, running under tmux via mosh, needs to pass back a copy.

The Linux config for tmux does that.

Prerequisites:

* tmux >= 3.2
* mosh >= 1.4

We use Ghostty as a terminal supporting OSC 52.  iTerm2 allegedly does too, while the default Mac Terminal does not.
See MOSHPIT.md for the detailed explanation of the remote config.
The Mac config is supposed to copy selections of all kinds.
