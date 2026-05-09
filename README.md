# dotfiles

Personal dotfiles managed by [chezmoi](https://www.chezmoi.io/). Multi-platform: NixOS/WSL, macOS, plain Linux, Windows.

## Structure

```
.
├── dot_zshrc                   # Thin conf.d loader
├── dot_zsh/conf.d/             # Modular zsh config
│   ├── 00-env.zsh.tmpl         # PATH, exports, EDITOR, NVIM_APPNAME
│   ├── 10-aliases.zsh.tmpl     # All aliases (general, eza, editor, NixOS, Homebrew, WSL)
│   ├── 20-functions.zsh.tmpl   # Shell functions
│   ├── 30-keybinds.zsh         # Keybindings + zsh options
│   ├── 40-completions.zsh      # compinit + zstyle
│   └── 90-prompt.zsh.tmpl      # catppuccin → zoxide → starship → atuin (must be last)
├── dot_config/
│   ├── git/
│   │   ├── config.tmpl             # Git user config (includeIf blocks)
│   │   ├── config-personal-github  # Personal GitHub identity
│   │   └── config-work.tmpl        # Work identity (only deployed when local chezmoi data is present)
│   ├── starship.toml
│   ├── alacritty/
│   ├── helix/
│   ├── lazygit/
│   ├── atuin/
│   ├── eza/
│   └── zed/
├── .chezmoiexternal.toml.tmpl  # External repos (neovim config on non-NixOS)
└── .chezmoiignore              # Platform-conditional ignores
```

## Platform detection

Templates use `.chezmoi.os`, `.chezmoi.hostname`, and `.chezmoi.kernel.osrelease` (contains `microsoft` on WSL) for platform branching.

## Work machine setup

On a work machine, create `~/.config/chezmoi/chezmoi.toml` **before** running `chezmoi apply` (or `chezmoi init --apply`). This file is never tracked — it is chezmoi's own local config and stays private on the machine.

### WSL HTTPS Git Operations

If you are using HTTPS Git operations in WSL, you will need Git installed on the Windows host. This is because the configuration uses the Windows Git Credential Manager for secure credential storage. Ensure Git for Windows is installed and properly configured on your Windows host to enable seamless authentication in WSL.

```toml
[data]
  work_git_username = "yourworkname"
  work_git_email    = "you@company.com"
  work_vcs_host     = "git.company.com"
  work_ado_org      = "mycompany"      # optional — only add if you use Azure DevOps
```

**Effect of each key:**

| Key | Required | Effect |
|---|---|---|
| `work_git_username` | yes | Name used in commits on work repos |
| `work_git_email` | yes | Email used in commits on work repos |
| `work_vcs_host` | yes | Work VCS hostname — activates SSH + HTTPS `includeIf` blocks |
| `work_ado_org` | no | Azure DevOps org name — activates SSH + HTTPS `includeIf` blocks for `dev.azure.com` |

When these keys are present, chezmoi will:
- Add `[includeIf]` blocks to `~/.gitconfig` that load `~/.gitconfig-work` for any repo whose remote matches `work_vcs_host` (and `dev.azure.com/<work_ado_org>` if set)
- Deploy `~/.gitconfig-work` with the work `[user]` block

`~/.gitconfig-personal` is always deployed and acts as the default identity for any repo not matched by the `includeIf` blocks (e.g. repos with no remote, or other hosts).

On machines **without** this local config, none of the above is deployed — no action required.

## Neovim config

- **NixOS/WSL**: baked into the Nix store by the flake — chezmoi does nothing
- **macOS / plain Linux**: `.chezmoiexternal.toml.tmpl` clones `github:jeomhps/neovim` to `~/.config/neovim-config`; `NVIM_APPNAME=neovim-config/nvim` is set in `00-env.zsh.tmpl`

The clone uses `refreshPeriod = "0s"` — it is cloned once and never auto-pulled. Manage the repo manually.
