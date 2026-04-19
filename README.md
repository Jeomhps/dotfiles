# dotfiles

## Setup

After cloning, create the local chezmoi config file **before** running `chezmoi apply`.
This file is never committed — it holds machine-specific private values.

**`~/.config/chezmoi/chezmoi.toml`**
```toml
[data]
  gitName  = "Your Name"
  gitEmail = "your@email.com"
```

Then apply:
```sh
chezmoi apply
```

## TODO

- Do not import helix languages unless it is nixos
