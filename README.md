# dotfiles

Personal dotfiles managed by [chezmoi](https://www.chezmoi.io/). Multi-platform: NixOS/WSL, macOS, plain Linux, Windows.

## Structure

```
.
├── dot_zshenv.tmpl             # Environment + PATH — sourced by every zsh
├── dot_zprofile.tmpl           # Login shells; re-prepends Homebrew after path_helper
├── dot_zshrc                   # Thin conf.d loader
├── dot_zsh/conf.d/             # Modular zsh config (interactive shells only)
│   ├── 00-env.zsh.tmpl         # Interactive-only env (WSL GPG_TTY)
│   ├── 10-aliases.zsh.tmpl     # All aliases (general, eza, editor, NixOS, Homebrew, WSL)
│   ├── 20-functions.zsh.tmpl   # Shell functions
│   ├── 30-keybinds.zsh         # Keybindings + zsh options
│   ├── 40-completions.zsh      # compinit + zstyle
│   └── 90-prompt.zsh.tmpl      # catppuccin → zoxide → starship → atuin (must be last)
├── dot_alacritty.toml.tmpl
├── dot_config/
│   ├── git/
│   │   ├── config.tmpl             # Git base config (includeIf blocks)
│   │   ├── config-personal-github  # Personal GitHub identity
│   │   ├── config-work.tmpl        # Work identity (only deployed when local chezmoi data is present)
│   │   └── ignore                  # Global excludesfile — OS/editor cruft only
│   ├── starship.toml
│   ├── helix/
│   ├── lazygit/
│   ├── zellij/
│   ├── atuin/
│   ├── eza/
│   ├── fastfetch/
│   └── zed/                    # Thin wrappers over .chezmoitemplates/zed/
├── dot_agents/skills/          # Agent skills (pdf)
├── dot_my-scripts/scripts/     # Standalone scripts (cm, generate-readme, …)
├── dot_homebrew/Brewfile       # macOS package manifest
├── dot_docker/config.json.tmpl # macOS/colima docker config
├── AppData/Roaming/Zed/        # Windows Zed — same templates as dot_config/zed
├── .chezmoitemplates/
│   ├── platform.json           # Shared platform detection (see below)
│   └── zed/                    # Zed config fragments shared by all platforms
├── .chezmoiexternal.toml.tmpl  # External repos (neovim config on non-NixOS)
└── .chezmoiignore              # Platform-conditional ignores
```

## Platform detection

Platform booleans are defined once in `.chezmoitemplates/platform.json` and derived from
`.chezmoi.os`, `.chezmoi.hostname`, and `.chezmoi.kernel.osrelease` (contains `microsoft` on WSL).

Any template that needs to branch pulls them in with a single line:

```
{{- $p := includeTemplate "platform.json" . | fromJson -}}

{{ if $p.isWSL }}...{{ end }}
```

Available: `isDarwin`, `isLinux`, `isWindows`, `isWSL`, `isNixOS`.

Deliberately *not* `[data]` in `.chezmoi.toml.tmpl`: that file is only evaluated by
`chezmoi init`, which would overwrite the untracked machine-local config holding the
work identity.

## Work machine setup

On a work machine, create `~/.config/chezmoi/chezmoi.toml` **before** running `chezmoi apply` (or `chezmoi init --apply`). This file is never tracked — it is chezmoi's own local config and stays private on the machine.

### WSL HTTPS Git Operations

If you are using HTTPS Git operations in WSL, you will need Git installed on the Windows host. This is because the configuration uses the Windows Git Credential Manager for secure credential storage. Ensure Git for Windows is installed and properly configured on your Windows host to enable seamless authentication in WSL.

```toml
[data]
  gpg_enabled         = true             # optional — gopass/GPG is set up on this machine; drives WSL tty refresh
  work_git_username   = "yourworkname"
  work_git_email      = "you@company.com"
  work_vcs_host       = "git.company.com"
  work_ado_org        = "mycompany"      # optional — only add if you use Azure DevOps
  work_signing_method = "gpg"            # optional — "gpg" or "ssh", toggles which format signs work commits
  work_gpg_signing_key = "ABCD1234..."   # required when work_signing_method = "gpg"
  work_ssh_signing_key = "~/.ssh/id_ed25519.pub"  # required when work_signing_method = "ssh"
  zed_copilot_uri     = "https://your.enterprise.domain"  # Zed Copilot enterprise URI
```

**Effect of each key:**

| Key | Required | Effect |
|---|---|---|
| `gpg_enabled` | no | On WSL, exports `GPG_TTY` and refreshes the gpg-agent tty on shell start and after `update`/`upgrade`/`rollback` (needed whenever gpg-agent may prompt: gopass unlocks, and gpg-based commit signing). Omit/false if this machine doesn't use gopass or GPG at all |
| `work_git_username` | yes | Name used in commits on work repos |
| `work_git_email` | yes | Email used in commits on work repos |
| `work_vcs_host` | yes | Work VCS hostname — activates SSH + HTTPS `includeIf` blocks |
| `work_ado_org` | no | Azure DevOps org name — activates SSH + HTTPS `includeIf` blocks for `dev.azure.com` |
| `work_signing_method` | no | `"gpg"` or `"ssh"` — enables `commit.gpgsign`/`tag.gpgsign` on work repos with the chosen format. Omit to disable signing entirely |
| `work_gpg_signing_key` | when method is `gpg` | GPG key id used as `user.signingkey` |
| `work_ssh_signing_key` | when method is `ssh` | Path to an SSH public key used as `user.signingkey`, with `gpg.format = ssh` and `gpg.ssh.allowedSignersFile = ~/.ssh/allowed_signers` |
| `zed_copilot_uri` | no | Zed Copilot enterprise URI — activates custom Copilot endpoint |

Note: switching `work_signing_method` to `ssh` requires `~/.ssh/allowed_signers` to exist (containing `<email> <public key>` lines) for local `git log --show-signature` verification to work — GitHub's own "Verified" badge doesn't need this file.

When these keys are present, chezmoi will:
- Add `[includeIf]` blocks to `~/.config/git/config` that load `~/.config/git/config-work` for any repo whose remote matches `work_vcs_host` (and `dev.azure.com/<work_ado_org>` if set)
- Deploy `~/.config/git/config-work` with the work `[user]` block
- Include custom Zed Copilot configuration if `zed_copilot_uri` is defined

`~/.config/git/config-personal-github` is always deployed and matches GitHub remotes over both SSH and HTTPS.

Note there is **no** global `[user]` fallback: every identity comes from an `includeIf` block keyed on the remote URL. A repo whose remote matches nothing — or that has no remote yet — resolves no `user.email`, and git will refuse to commit until one is set. That is deliberate (it fails loudly instead of silently committing under the wrong identity), but it does mean `git init` in a scratch directory needs `git config user.email` before the first commit.

On machines **without** this local config, none of the above is deployed — no action required.

## Zed Copilot Configuration

To configure a custom Copilot endpoint for Zed in a work environment, define the `zed_copilot_uri` variable in your `~/.config/chezmoi/chezmoi.toml` file. This will conditionally include the work-specific Zed configuration.

### Windows Setup

On Windows, the `chezmoi.toml` file should be created at:
- `%USERPROFILE%\.config\chezmoi\chezmoi.toml`

For example:
```toml
[data]
  zed_copilot_uri = "https://your.enterprise.domain"
```

### macOS/Linux Setup

On macOS and Linux, the `chezmoi.toml` file should be created at:
- `~/.config/chezmoi/chezmoi.toml`

For example:
```toml
[data]
  zed_copilot_uri = "https://your.enterprise.domain"
```

## Neovim config

- **NixOS/WSL**: baked into the Nix store by the flake — chezmoi does nothing
- **macOS / plain Linux**: `.chezmoiexternal.toml.tmpl` clones `github:jeomhps/neovim` to `~/.config/neovim-config`; `NVIM_APPNAME=neovim-config/nvim` is set in `dot_zshenv.tmpl`

The clone uses `refreshPeriod = "0s"` — it is cloned once and never auto-pulled. Manage the repo manually.