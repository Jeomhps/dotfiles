setopt AUTO_CD
setopt CORRECT
setopt GLOB_DOTS

bindkey -e

bindkey "^[[1;5C" forward-word
bindkey "^[[1;5D" backward-word

bindkey "^H" backward-kill-word
bindkey "^[[3;5~" kill-word

bindkey "^A" beginning-of-line
bindkey "^E" end-of-line

bindkey "^ " autosuggest-accept

_lazygit() { lazygit; zle reset-prompt }
zle -N _lazygit
bindkey "^G" _lazygit

autoload -U up-line-or-beginning-search
autoload -U down-line-or-beginning-search
zle -N up-line-or-beginning-search
zle -N down-line-or-beginning-search
bindkey "^[[A" up-line-or-beginning-search
bindkey "^[[B" down-line-or-beginning-search
