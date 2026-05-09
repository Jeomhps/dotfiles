# ── Completion ────────────────────────────────────────────────────────────────

# Initialize the completion system
autoload -Uz compinit

# Only regenerate the dump file once per day for speed
if [[ -n "$HOME/.zcompdump"(#qN.mh+24) ]]; then
  compinit
else
  compinit -C
fi

# Case-insensitive matching, then partial-word, then substring
zstyle ':completion:*' matcher-list \
  '' \
  'm:{a-zA-Z}={A-Za-z}' \
  'r:|[._-]=* r:|=*' \
  'l:|=* r:|=*'

# Show a menu when there are multiple matches
zstyle ':completion:*' menu select

# Group matches by category with a header
zstyle ':completion:*' group-name ''
zstyle ':completion:*:descriptions' format '%F{yellow}── %d ──%f'
zstyle ':completion:*:warnings' format '%F{red}No matches for: %d%f'

# Colorize file completions like ls
zstyle ':completion:*:default' list-colors ${(s.:.)LS_COLORS}

# Process completion
zstyle ':completion:*:*:*:*:processes' command 'ps -u $USER -o pid,user,comm -w'

# Cache expensive completions (e.g. package managers)
zstyle ':completion:*' use-cache yes
zstyle ':completion:*' cache-path "$HOME/.zcompcache"

# Fuzzy correction for typos
zstyle ':completion:*' completer _complete _match _approximate
zstyle ':completion:*:match:*' original only
zstyle ':completion:*:approximate:*' max-errors 1 numeric
