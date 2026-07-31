---
title: "Welcome to the Moshpit"
slug: moshpit-guide
excerpt: "A new First Pair Press field guide to persistent remote agent development with Ghostty, tmux, mosh, SSH, Tailscale, and OSC 52."
tags:
  - agent development
  - terminals
  - mosh
  - tmux
  - Ghostty
---

# Welcome to the Moshpit

![Moshpit: A Guide to Agent Development with Mosh, Tmux and Ghostty](assets/moshpit-headboard.png)

The laptop sleeps. Wi-Fi changes. A long SSH session disappears halfway through a build. Even when the processes survive, a smaller irritation remains: the useful fragment selected on a remote Linux host refuses to arrive in the Mac clipboard.

**Moshpit: A Guide to Agent Development with Mosh, Tmux and Ghostty**, by Alexy Khrabrov, is a short field guide to solving the entire stack rather than one symptom at a time.

The first fix is mosh. It turns a brittle remote terminal into a roaming session that tolerates sleep and network changes. The second is tmux. It gives the work a durable home on the remote machine, so agents, tests, logs, and editors remain alive when the visible client goes away. Ghostty completes the local edge with a fast terminal and explicit OSC 52 clipboard support.

Then comes the surprisingly subtle part: copy and paste.

Pasting from Mac to Linux is ordinary terminal input—Command–V, through Ghostty and mosh, into the active tmux pane. Copying in the other direction needs a return route. For small selections, tmux emits OSC 52 with the literal `c;` target mosh accepts. For reliable multi-line selections, tmux pipes bytes through `ssh mac pbcopy`. Tailscale gives the remote host a private route back to the laptop; SSH multiplexing keeps the connection warm for many tiny clipboard writes.

The guide explains both paths, including the gotchas that made them hard to discover:

- why mosh 1.4 or newer is required for OSC 52;
- why tmux must force the `c;` clipboard target;
- why a wildcard terminal capability avoids the TERM-name rabbit hole;
- why capability changes require a fresh attachment;
- why an SSH agent reuses credentials while `ControlMaster` reuses the actual connection;
- and why OSC 52 remains a convenient fallback even when SSH becomes the reliable primary.

It also records the muscle memory of the finished environment: Command–Left/Right between Ghostty tabs, Shift–Left/Right between tmux windows, `C-b ,` to rename a window, mouse-wheel scrollback, and two selection styles—copy and jump, or copy and stay.

The source is intentionally inspectable. The [`alexy/moshpit` repository](https://github.com/alexy/moshpit) contains separate tmux configurations for macOS and Linux, a Debian `.zprofile` that converges remote logins on a reusable agent, an SSH configuration that keeps the return transport warm, the original troubleshooting notes, the semantic book manuscript, and the reproducible First Pair Press build.

The result is a small system whose layers have clear jobs: Ghostty owns the human edge; tmux owns process continuity; mosh owns roaming interaction; SSH owns authenticated reliable transfer; and Tailscale owns private reachability.

That separation is the real lesson. Remote agent development becomes calmer when the terminal is no longer one fragile pipe, but a set of cooperating layers that each fail—and recover—on their own terms.

