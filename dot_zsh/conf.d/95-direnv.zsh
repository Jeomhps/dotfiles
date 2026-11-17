# direnv — charge l'env (ex: flake nix) à l'entrée d'un dossier avec .envrc
if command -v direnv >/dev/null; then
  eval "$(direnv hook zsh)"
fi
