# ── Keybindings ───────────────────────────────────────────────────────────────

# Quality of life options
setopt AUTO_CD       # type a dir name to cd into it
setopt CORRECT       # suggest corrections for mistyped commands
setopt GLOB_DOTS     # globs match dotfiles without needing explicit .

# Use emacs-style bindings as base (works well alongside atuin)
bindkey -e

# Navigate words with Ctrl+Arrow
bindkey "^[[1;5C" forward-word   # Ctrl+Right
bindkey "^[[1;5D" backward-word  # Ctrl+Left

# Delete word with Ctrl+Backspace / Ctrl+Del
bindkey "^H" backward-kill-word
bindkey "^[[3;5~" kill-word

# Jump to beginning/end of line
bindkey "^A" beginning-of-line
bindkey "^E" end-of-line

# Accept autosuggestion with Ctrl+Space
bindkey "^ " autosuggest-accept

# Launch lazygit with Ctrl+G
_lazygit() { lazygit; zle reset-prompt }
zle -N _lazygit
bindkey "^G" _lazygit

# History search with Up/Down arrows (prefix-aware)
autoload -U up-line-or-beginning-search
autoload -U down-line-or-beginning-search
zle -N up-line-or-beginning-search
zle -N down-line-or-beginning-search
bindkey "^[[A" up-line-or-beginning-search   # Up arrow
bindkey "^[[B" down-line-or-beginning-search # Down arrow
