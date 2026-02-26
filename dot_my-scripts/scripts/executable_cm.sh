#!/usr/bin/env bash
set -euo pipefail

pick_managed() {
  chezmoi managed --path-style absolute \
    | while IFS= read -r abs; do
        rel="${abs#$HOME/}"
        printf '%s\t%s\n' "$rel" "$abs"
      done \
    | fzf \
        --prompt="chezmoi> " \
        --height=40% \
        --reverse \
        --delimiter=$'\t' \
        --with-nth=1 \
    | cut -f2
}

normalize_target() {
  local x="${1:-}"
  if [[ -z "$x" ]]; then
    return 0
  fi

  x="${x/#\~/$HOME}"

  if [[ "$x" == /* ]]; then
    printf '%s\n' "$x"
  elif [[ "$x" == .* ]]; then
    printf '%s\n' "$HOME/$x"
  else
    printf '%s\n' "$x"
  fi
}

cmd="${1:-pick}"
shift || true

case "$cmd" in
  pick|p)
    target="$(pick_managed)"
    [[ -n "${target:-}" ]] && printf '%s\n' "$target"
    ;;

  edit|e)
    if [[ $# -eq 0 ]]; then
      target="$(pick_managed)"
      [[ -n "${target:-}" ]] || exit 1
      chezmoi edit --apply "$target"
    else
      for arg in "$@"; do
        chezmoi edit --apply "$(normalize_target "$arg")"
      done
    fi
    ;;

  watch|w)
    if [[ $# -eq 0 ]]; then
      target="$(pick_managed)"
      [[ -n "${target:-}" ]] || exit 1
      chezmoi edit --watch "$target"
    else
      for arg in "$@"; do
        chezmoi edit --watch "$(normalize_target "$arg")"
      done
    fi
    ;;

  diff|d)
    if [[ $# -eq 0 ]]; then
      target="$(pick_managed)"
      [[ -n "${target:-}" ]] || exit 1
      chezmoi diff "$target"
    else
      for arg in "$@"; do
        chezmoi diff "$(normalize_target "$arg")"
      done
    fi
    ;;

  source|s)
    if [[ $# -eq 0 ]]; then
      target="$(pick_managed)"
      [[ -n "${target:-}" ]] || exit 1
      chezmoi source-path "$target"
    else
      for arg in "$@"; do
        chezmoi source-path "$(normalize_target "$arg")"
      done
    fi
    ;;

  apply|a)
    if [[ $# -eq 0 ]]; then
      target="$(pick_managed)"
      [[ -n "${target:-}" ]] || exit 1
      chezmoi apply "$target"
    else
      for arg in "$@"; do
        chezmoi apply "$(normalize_target "$arg")"
      done
    fi
    ;;

  list|ls)
    chezmoi managed
    ;;

  cd)
    chezmoi cd
    ;;

  *)
    cat <<'EOF'
cm pick            # fuzzy-pick a managed target
cm e [target]      # edit --apply target, or fuzzy-pick one
cm w [target]      # edit --watch target, or fuzzy-pick one
cm d [target]      # diff target, or fuzzy-pick one
cm s [target]      # show source path, or fuzzy-pick one
cm a [target]      # apply target, or fuzzy-pick one
cm ls              # list managed targets
cm cd              # cd to chezmoi source dir
EOF
    ;;
esac
