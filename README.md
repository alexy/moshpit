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

## Book edition

The illustrated First Pair Press guide lives in `book/`, with the announcement
source and portable `.textpack` in `blog/`. Rebuild the PDF, EPUB, HTML, cover,
headboard, diagrams, and staged configuration screenshots with:

```sh
python3 scripts/build_visuals.py
scripts/build_book.sh
```

The canonical First Pair builder configuration is `book/book.build.json`. The
local wrapper exists so the book can still be rendered when the installed Mac
toolchain does not yet match First Pair's strict publishing lock.
