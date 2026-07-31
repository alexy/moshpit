# Reuse one SSH agent across login sessions.
SSH_AGENT_ENV="$HOME/.ssh/agent.env"
# Use the same array form for one or several keys:
#   SSH_KEYS=("$HOME/.ssh/loscabos")
#   SSH_KEYS=("$HOME/.ssh/"{loscabos,linux})
SSH_KEYS=("$HOME/.ssh/"{loscabos,linux})

# Prefer an agent forwarded by the SSH client.
if [[ -z "$SSH_AUTH_SOCK" ]]; then
  [[ -r "$SSH_AGENT_ENV" ]] && source "$SSH_AGENT_ENV" >/dev/null

  # ssh-add returns 2 when no usable agent is reachable.
  ssh-add -l >/dev/null 2>&1
  if (( $? == 2 )); then
    ssh-agent -s |
      sed 's/^echo /# echo /' >| "$SSH_AGENT_ENV"

    chmod 600 "$SSH_AGENT_ENV"
    source "$SSH_AGENT_ENV" >/dev/null
  fi
fi

# Load each server-side key only if the agent does not already have it.
for SSH_KEY in "$SSH_KEYS[@]"; do
  if [[ -f "$SSH_KEY" ]]; then
    if [[ -f "$SSH_KEY.pub" ]]; then
      ssh-add -T "$SSH_KEY.pub" >/dev/null 2>&1 ||
        ssh-add "$SSH_KEY"
    else
      ssh-add "$SSH_KEY"
    fi
  fi
done

unset SSH_AGENT_ENV SSH_KEY SSH_KEYS
