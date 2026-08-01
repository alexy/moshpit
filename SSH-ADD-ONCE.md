# SSH-ADD-ONCE

Loading SSH keys exactly once per machine, shared across every zsh instance —
tmux panes, mosh sessions, Codex subshells, cron.

## The problem

`ssh-add` lived in `.zprofile` on the assumption that `.zprofile` runs once at
login. It doesn't. `.zprofile` runs **once per login shell**, and login shells
are created far more often than you'd think:

- tmux spawns each new window and pane as a login shell
- Codex and similar tools spawn `zsh -l` for subshells
- every fresh mosh/ssh connection is another login shell

Result: a passphrase prompt per pane.

## The principle

Decouple key loading from shell startup entirely.

1. **One long-lived agent** per machine, listening on a **fixed socket path**,
   owned by the init system (launchd / systemd) rather than by any shell.
2. **Shells only point at it.** No `ssh-add` in any rc file, ever.
3. The `SSH_AUTH_SOCK` export belongs in **`.zshenv`**, not `.zprofile` —
   `.zshenv` is the only file every zsh invocation reads, including the
   non-login, non-interactive subshells that tools spawn.

Key material gets added by `AddKeysToAgent yes` on first use, or once by hand
after boot. Either way: one prompt per boot, not one per window.

## macOS

macOS already runs an agent under launchd and hands `SSH_AUTH_SOCK` to every
process. Don't start your own.

Delete the `ssh-add` block from `.zprofile`, then in `~/.ssh/config`:

```
Host *
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_ed25519
```

Then, once — by hand, not from a script:

```zsh
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
```

The passphrase goes into the login Keychain. Every subsequent process inherits
the launchd socket. Nothing else is needed.

## Linux with systemd (suse, Debian)

`~/.config/systemd/user/ssh-agent.service`:

```ini
[Unit]
Description=SSH authentication agent

[Service]
Type=simple
Environment=SSH_AUTH_SOCK=%t/ssh-agent.socket
ExecStart=/usr/bin/ssh-agent -D -a $SSH_AUTH_SOCK

[Install]
WantedBy=default.target
```

Enable it, and enable lingering so it survives logout and starts at boot:

```zsh
systemctl --user enable --now ssh-agent
loginctl enable-linger "$USER"
```

`~/.zshenv`:

```zsh
export SSH_AUTH_SOCK="${XDG_RUNTIME_DIR}/ssh-agent.socket"
```

`~/.ssh/config`:

```
Host *
  AddKeysToAgent yes
  IdentityFile ~/.ssh/id_ed25519
```

`%t` in the unit expands to `$XDG_RUNTIME_DIR`, so the two paths agree.

## No systemd (Termux, proot-distro Debian)

Fixed socket path, plus a guard that starts an agent only when none is
reachable. All of this in `~/.zshenv`:

```zsh
export SSH_AUTH_SOCK="${XDG_RUNTIME_DIR:-${TMPDIR:-/tmp}}/ssh-agent-$UID.sock"

ssh-add -l >/dev/null 2>&1
if [[ $? == 2 ]]; then
  rm -f "$SSH_AUTH_SOCK"
  eval "$(ssh-agent -a "$SSH_AUTH_SOCK")" >/dev/null
fi
```

`ssh-add -l` exit codes matter here:

| code | meaning | action |
|------|---------|--------|
| 0 | agent up, has keys | nothing |
| 1 | agent up, no keys loaded | nothing — `AddKeysToAgent` will fill it |
| 2 | no agent reachable | clear stale socket, start one |

Restarting on `1` as well as `2` is the classic bug: it spawns a fresh agent
every time the current one happens to be empty, and you're back to prompting
per pane.

## Agent forwarding into long-lived tmux

Separate failure mode, same symptom. When you `ssh -A` / mosh into a remote
box, sshd sets `SSH_AUTH_SOCK` to a **per-connection** socket. That socket dies
with the connection, so tmux panes created under an old connection keep
pointing at a dead path after you reattach.

Fix with a stable symlink. On the remote, `~/.ssh/rc`:

```sh
if [ -S "$SSH_AUTH_SOCK" ] && [ ! -L "$SSH_AUTH_SOCK" ]; then
  ln -sf "$SSH_AUTH_SOCK" "$HOME/.ssh/agent.sock"
fi
```

and in the remote `~/.zshenv`:

```zsh
[[ -S "$HOME/.ssh/agent.sock" || -L "$HOME/.ssh/agent.sock" ]] \
  && export SSH_AUTH_SOCK="$HOME/.ssh/agent.sock"
```

`~/.ssh/rc` runs per incoming connection and repoints the symlink at the live
socket; existing panes read the stable path and keep working across reconnects.
`tmux set -g update-environment` does not help here — it only affects newly
created panes, not the ones already running.

## Not recommended

`set -g default-command "${SHELL}"` in `.tmux.conf` makes panes non-login
shells, which suppresses the symptom. It's a band-aid: it breaks
`path_helper`-derived `PATH` on macOS and leaves the Codex subshell case
unfixed. Fix the agent, not the shell type.

## Checklist

- [ ] no `ssh-add` in `.zprofile`, `.zshrc`, or `.zlogin`
- [ ] `SSH_AUTH_SOCK` exported from `.zshenv` only
- [ ] agent owned by launchd (mac) or a systemd user unit (linux)
- [ ] `AddKeysToAgent yes` in `~/.ssh/config`
- [ ] `loginctl enable-linger` on linux boxes
- [ ] `~/.ssh/rc` symlink on any host reached with agent forwarding

Verify from a fresh tmux pane: `echo $SSH_AUTH_SOCK` should be identical in
every pane, and `ssh-add -l` should list keys without prompting.
