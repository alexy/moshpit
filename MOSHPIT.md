# MOSHPIT

**Clipboard copy/paste that actually works over `tmux` + `mosh`.**

This guide gets terminal selections on a remote Linux box to land in your local
Mac clipboard, across a `mosh` connection, inside `tmux`. It assumes a Mac
running **Ghostty** as the local terminal, connecting over **mosh** to a Linux
host running **tmux**. The same recipe works for other local terminals that
support OSC 52 (iTerm2, Kitty, WezTerm, Alacritty) — only the Mac-side setting
name changes.

Everything here was learned the hard way. The three things that trip people up
are called out explicitly: mosh's `c;`-only quirk, the `kill-server` ritual, and
the `TERM`-matching rabbit hole. If you only remember one line, remember the
`terminal-overrides` line in the config below.

One caveat up front: OSC 52 over mosh gets copy/paste *working* but is never
fully *reliable* — mosh drops large and multi-line selections. If you need it
rock-solid (any size, every time), skip to **Making it solid** below, which
routes copies over SSH to `pbcopy` instead of over mosh.

---

## TL;DR — the working config

**On the Mac**, in `~/.config/ghostty/config`:

```
clipboard-write = allow
```

**On the remote Linux host**, in `~/.tmux.conf`:

```
set -g mouse on
setw -g mode-keys vi
bind -T copy-mode-vi MouseDragEnd1Pane send-keys -X copy-selection-and-cancel

# Clipboard over mosh. Two non-obvious things:
#   1. mosh only accepts OSC 52 whose target is `c;`; tmux's default Ms emits a
#      non-`c` target, so mosh silently drops it. `c%p1%.0s` forces a literal `c`.
#   2. `*` matches any TERM, so this one file is portable across every host.
set -g set-clipboard on
set -as terminal-features ',*:clipboard'
set -as terminal-overrides ',*:Ms=\E]52;c%p1%.0s;%p2%s\7'
```

Then, **critically**, restart the tmux server so the settings actually bind:

```
tmux kill-server
```

Reconnect over mosh, reattach, and a mouse selection should replace your Mac
clipboard. If it doesn't, work through the verification ladder below.

**Requirement:** `mosh` **1.4.0 or newer** on *both* ends. Older mosh strips
OSC 52 entirely and none of this works. Check with `mosh --version` locally and
`mosh-server --version` on the remote.

---

## How it works

There is no shared clipboard across an SSH/mosh hop. The copied text has to
travel back over the terminal byte stream, and the mechanism for that is the
**OSC 52** escape sequence: a program emits `ESC ] 52 ; c ; <base64> BEL`, and a
terminal that understands it decodes the base64 and writes it to the system
clipboard.

Over this stack the sequence passes through three layers, and every layer has to
cooperate:

1. **tmux** generates the OSC 52 when you copy in copy-mode (this needs
   `set-clipboard on` plus a usable `Ms` capability string).
2. **mosh** carries it. mosh doesn't forward raw bytes — it recognizes OSC 52 as
   a clipboard event and propagates it to the client as a side-channel action.
3. **Ghostty** receives it and writes your Mac clipboard (this needs
   `clipboard-write = allow`).

Break any one link and the copy silently does nothing. Most of the debugging
below is about figuring out *which* link is broken.

---

## Step 1 — the Mac (Ghostty)

Ghostty defaults to prompting on (or denying) programmatic clipboard writes. Set
it to allow them:

```
clipboard-write = allow
```

Reload Ghostty (`⌘,` reload, or restart). Other terminals: iTerm2 has
"Applications in terminal may access clipboard" in Preferences → General →
Selection; Kitty uses `clipboard_control write-clipboard write-primary`.

## Step 2 — the remote tmux

Three concerns, all in `~/.tmux.conf`:

**Enable mouse and copy behavior.** `set -g mouse on` turns on selection and
scrollback. `setw -g mode-keys vi` picks the vi copy-mode key table. The
`MouseDragEnd1Pane` binding makes drag-release copy the selection. Use
`copy-selection-and-cancel` to clear the highlight on release, or
`copy-selection` to keep it highlighted — either one still copies.

**Turn on the clipboard.** `set -g set-clipboard on` is what makes tmux emit
OSC 52 both when it copies in copy-mode and when a program inside tmux sets the
clipboard.

**Supply a working `Ms`.** This is the line that matters, and the `c%p1%.0s`
detail is the whole ballgame — see the next section.

---

## The three gotchas

### Gotcha 1 — mosh only accepts a `c;` target (the load-bearing fix)

This is the one that costs people hours. **mosh accepts an OSC 52 sequence only
if its clipboard target is `c` (`ESC]52;c;...`).** tmux's built-in `Ms`
capability emits whatever it passes as the first parameter, which is *not* `c`,
so mosh silently drops every copy-mode selection while a hand-written
`printf '\033]52;c;...'` (with an explicit `c`) sails right through. That
asymmetry — "my manual test works but tmux copies don't" — is the fingerprint.

The fix forces a literal `c` into the sequence:

```
set -as terminal-overrides ',*:Ms=\E]52;c%p1%.0s;%p2%s\7'
```

`c%p1%.0s` prints the literal `c`, then formats tmux's first parameter to zero
width so it emits nothing — the target is always exactly `c`. `%p2%s` is the
base64 payload; `\7` is the BEL terminator. This single change is what makes the
whole thing work over mosh.

### Gotcha 2 — a config reload is not enough; you must re-attach

`terminal-overrides` and `terminal-features` bind to a client **only when it
attaches**. Running `tmux source-file ~/.tmux.conf` updates the option in memory
but does **not** push the new capability to your already-attached client, so the
copy path keeps using the old (broken) state and you conclude the fix didn't
work.

The reliable ritual after *any* clipboard-related tmux edit:

```
tmux kill-server        # or: detach fully, then reattach
```

then reconnect over mosh and reattach. A large share of "it worked, then it
didn't, then it did" confusion traces to a stale attach, not to your config.

### Gotcha 3 — don't pin to a `TERM` name; use `*`

Which `TERM` string tmux matches these lines against is genuinely fiddly and
differs per host — the `$TERM` you see *inside* tmux (`default-terminal`), the
outer `#{client_termname}`, and what the override actually keys on don't always
agree. One box reports `xterm-256color` inside tmux, another `tmux-256color`,
another `screen-256color` as the client name. Chasing the "correct" literal name
per machine is a losing game.

Sidestep it entirely by matching **any** terminal with a `*` glob:

```
set -as terminal-features ',*:clipboard'
set -as terminal-overrides ',*:Ms=\E]52;c%p1%.0s;%p2%s\7'
```

The `*` matches every `TERM`, so one identical `.tmux.conf` works on every host
and the next box can't trip on a term string that doesn't line up. There is no
downside to the wildcard.

---

## Verifying — the isolation ladder

When it's not working, don't guess — walk these in order. Each step tests exactly
one link, so the first failure tells you where the break is.

**1. mosh + Ghostty (outside tmux).** In a plain mosh shell, no tmux:

```
printf '\033]52;c;%s\a' "$(printf hello | base64)"
```

`hello` should appear in your Mac clipboard. If not, the problem is mosh
(version < 1.4.0 on one end) or Ghostty (`clipboard-write` not `allow`) — fix
that before touching tmux.

**2. tmux's forwarding (inside tmux).** Run the *same* command inside a tmux
pane. If a fresh unique string reaches the clipboard, tmux is forwarding OSC 52
correctly and `set-clipboard on` is active.

**3. tmux copy-mode generation.** Now select with the mouse (or `prefix [`, then
`v`/motion/`y`). If steps 1–2 work but this doesn't, you're missing the `c;`
target fix (Gotcha 1) or you haven't re-attached since adding it (Gotcha 2).

Useful confirmations along the way:

- `mosh --version` (local) and `mosh-server --version` (remote) — both ≥ 1.4.0.
- `tmux -V` — 3.2+ for the `:clipboard` feature; the `Ms` override works on any.
- `tmux show-options -g set-clipboard` — confirms the *running* value is `on`.
- After a copy, `tmux show-buffer` — if the buffer has your text but the
  clipboard doesn't update, the copy fired and the break is downstream (mosh
  target or a stale attach), not your binding.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Nothing copies, even outside tmux | mosh too old, or Ghostty blocking writes | `mosh`/`mosh-server` ≥ 1.4.0 on both ends; `clipboard-write = allow` |
| Manual `printf` works, tmux selections don't | Missing the `c;` target — mosh drops tmux's default OSC 52 | Use the `c%p1%.0s` override, then `kill-server` + reattach |
| Fixed the config but still broken | Reloaded with `source-file`, never re-attached | `tmux kill-server`, reconnect, reattach |
| Works on one host, not another | Override pinned to a `TERM` name that host doesn't use | Switch both lines to the `*` glob |
| Clipboard "stuck" on the last copy | New OSC 52 not propagating (stale mosh channel, or dropped target) | Bounce the mosh session; verify the `c;` fix is applied |
| Large selections don't copy, small ones do | mosh caps a clipboard payload at ~one UDP packet | Keep copies modest; move large blocks via a file or the SSH side |
| Double/triple-click won't copy but drag does | Those clicks aren't bound to a copy command | Add explicit `DoubleClick1Pane` / `TripleClick1Pane` bindings (below) |

Optional explicit bindings for word (double-click) and line (triple-click) copy,
if your tmux defaults don't cover them:

```
bind -T copy-mode-vi DoubleClick1Pane send -X select-word \; send -X copy-selection-and-cancel
bind -T copy-mode-vi TripleClick1Pane send -X select-line \; send -X copy-selection-and-cancel
bind -n DoubleClick1Pane select-pane \; copy-mode -M \; send -X select-word \; send -X copy-selection-and-cancel
bind -n TripleClick1Pane select-pane \; copy-mode -M \; send -X select-line \; send -X copy-selection-and-cancel
```

---

## Making it solid — take the clipboard off mosh

Everything above gets copy/paste *working*, but OSC 52 over mosh is never fully
**reliable**, and no tmux setting changes that — the weakness is in the
transport, not the config. Two mosh limits cause it:

- **Size cap.** mosh carries the clipboard in roughly a single UDP packet, so a
  multi-line or block selection exceeds it and is silently dropped — while a
  single-line triple-click fits and succeeds.
- **Lossy propagation.** mosh syncs the clipboard as a best-effort event over
  UDP, so even small copies can drop or coalesce.

The tell-tale symptoms: multi-line selections fail but single lines work; the
second copy "repeats" the first (the new copy was dropped, so the clipboard
kept its last good value); the same copy lands one time and not the next. If
that's what you're seeing, stop tuning tmux — move the clipboard onto a
reliable channel.

The fix is to pipe the selection over **SSH straight into `pbcopy`** on the Mac,
bypassing mosh entirely. TCP, no size cap, no dropped events, any payload. Since
`copy-command` routes every copy path through one command, it's a one-liner per
remote:

```tmux
set -g copy-command 'ssh mac pbcopy'
```

Replace `mac` with the Mac's hostname (see Tailscale below). Keep it fast by
reusing one persistent SSH connection — in each remote's `~/.ssh/config`:

```
Host mac
    HostName your-mac.your-tailnet.ts.net   # or the 100.x.y.z Tailscale IP
    User youruser
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist 10m
    BatchMode yes
    ConnectTimeout 3
```

Only the first copy opens the connection (~1s); every copy after reuses the
socket and is effectively instant. A 200-line block now copies as reliably as a
single word.

**Prerequisites (one-time):** Remote Login on the Mac (System Settings →
General → Sharing → Remote Login), and each remote's SSH public key in the Mac's
`~/.ssh/authorized_keys`. `BatchMode yes` makes an unreachable Mac fail fast
instead of hanging your copy.

**Keep the OSC 52 lines as a fallback.** Leave `set-clipboard on` plus the
wildcard `terminal-features`/`terminal-overrides` in place — if the Mac is
asleep or off the network, small copies still ride the OSC 52 path. SSH becomes
the reliable primary; OSC 52 is the backstop.

### The reverse-reachability problem, and Tailscale

The catch with `ssh mac pbcopy` is that the *remote* now has to reach *back* to
your Mac — and a Mac behind home NAT (or an EC2 host that can't see your laptop)
has no stable address to connect to. [Tailscale](https://tailscale.com) solves
exactly this: it puts the Mac and every host on one private mesh, giving the Mac
a stable `100.x` address and a MagicDNS name reachable from anywhere on the
tailnet.

**On EC2 (hosts in a VPC), this works well and needs no inbound changes:**

- **Outbound-only.** Tailscale connects *out* to its coordination server and
  does NAT traversal, so you **don't open any inbound security-group ports**.
  Default all-outbound egress is enough. It prefers a direct path over UDP
  41641 and falls back to a DERP relay over 443 if UDP is blocked — and since a
  clipboard payload is tiny, the relay path is imperceptible.
- **Private subnets are fine** as long as the instance has a route to the
  internet for the control plane (a NAT gateway suffices). Only fully
  egress-blocked subnets can't bring it up.
- **Headless install** with a pre-authorized key (no browser login):

  ```bash
  curl -fsSL https://tailscale.com/install.sh | sh
  sudo tailscale up --authkey tskey-auth-xxxxx   # generate in the admin console
  ```

- **MagicDNS** lets the Mac answer to just `mac`, so `copy-command 'ssh mac
  pbcopy'` works verbatim.
- **Tailscale SSH** can replace key management for the remote → Mac hop: run
  `tailscale up --ssh` on the Mac and it accepts SSH from your tailnet by
  identity, no `authorized_keys` bookkeeping.

Two things to weigh: confirm your org allows a third-party mesh VPN on company
AWS accounts, and if you want the tailnet tight, put the EC2 hosts on a tag and
write an ACL that only lets them reach the Mac's SSH port instead of allow-all.

**No-Tailscale alternative:** a reverse SSH tunnel. Since you already connect
Mac → remote, carry a port back with `RemoteForward` and run a small `pbcopy`
listener on the Mac (the `lemonade` tool is built for this). More moving parts,
and note mosh can't carry the forward — you'd need a parallel plain-SSH
connection for it. Tailscale is the cleaner path.

### Once it's reliable, `no-clear` is optional

The reason to keep a selection alive with `copy-pipe-no-clear` was to *retry* a
flaky copy. With SSH transport that motivation is gone, so clear-vs-no-clear
becomes a pure preference: `-and-cancel` auto-exits copy-mode (no lingering
selection to forget, but the view jumps to the prompt), while `-no-clear` holds
your scrollback position (but you tap `q`/Escape to leave). Pick on that basis
alone — the clipboard is solid either way.

---

## Known limits

- **Payload size (OSC 52 path only).** mosh carries the clipboard in roughly a
  single UDP packet, so a large or multi-line selection can silently exceed that
  and get dropped. This is the whole reason for the SSH `copy-command` approach
  above — the SSH path has no such cap. If you're still on the OSC 52 path, keep
  copies modest or move big blocks via a file.
- **One direction.** This covers remote → local (copy on the remote, paste on
  the Mac). Pasting *into* the remote is just your terminal's normal paste
  (⌘V), which works independently of any of this.
- **`:clipboard` vs `Ms`.** The `:clipboard` terminal-feature lets programs
  *inside* tmux (e.g. a vim yank configured for OSC 52) push to your clipboard.
  The `Ms` override is what drives tmux's *own* copy-mode copies. Keep both.

---

## The whole `~/.tmux.conf`, annotated

```tmux
# --- window nav -----------------------------------------------------------
bind -n S-Left  previous-window
bind -n S-Right next-window

# --- panes ----------------------------------------------------------------
set -g pane-border-status top
set -g pane-border-format "#{pane_title}"

# --- mouse + copy-mode ----------------------------------------------------
set -g mouse on
setw -g mode-keys vi
bind -T copy-mode-vi MouseDragEnd1Pane send-keys -X copy-selection-and-cancel

# --- clipboard over mosh --------------------------------------------------
# mosh only accepts OSC 52 with a `c;` target, so force `c` via c%p1%.0s.
# `*` matches any TERM so this file is portable across every host.
# After editing: `tmux kill-server` and reattach (source-file alone won't bind).
set -g set-clipboard on
set -as terminal-features ',*:clipboard'
set -as terminal-overrides ',*:Ms=\E]52;c%p1%.0s;%p2%s\7'
```

That's it — one Ghostty line, one tmux block, and the discipline to
`kill-server` + reattach after you change it.
