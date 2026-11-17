autoload -Uz compinit

# Full check once a day. (#q) needs extendedglob; compinit doesn't rewrite an
# unchanged dump, so touch it to restart the 24h window.
() {
  setopt local_options extended_glob
  if [[ -n $HOME/.zcompdump(#qN.mh+24) ]]; then
    compinit
    touch "$HOME/.zcompdump"
  else
    compinit -C
  fi
}

zstyle ':completion:*' matcher-list \
  '' \
  'm:{a-zA-Z}={A-Za-z}' \
  'r:|[._-]=* r:|=*' \
  'l:|=* r:|=*'

zstyle ':completion:*' menu select

zstyle ':completion:*' group-name ''
zstyle ':completion:*:descriptions' format '%F{yellow}── %d ──%f'
zstyle ':completion:*:warnings' format '%F{red}No matches for: %d%f'

zstyle ':completion:*:default' list-colors ${(s.:.)LS_COLORS}

zstyle ':completion:*:*:*:*:processes' command 'ps -u $USER -o pid,user,comm -w'

zstyle ':completion:*' use-cache yes
zstyle ':completion:*' cache-path "$HOME/.zcompcache"

zstyle ':completion:*' completer _complete _match _approximate
zstyle ':completion:*:match:*' original only
zstyle ':completion:*:approximate:*' max-errors 1 numeric
