local lspconfiger = require("lspconfig")

return {
  -- requires tinymist,
  {
    "williamboman/mason.nvim",
    opts = {
      ensure_installed = {
        "tinymist",
      },
    },
  },

  -- add tinymist to lspconfig
  {
    "neovim/nvim-lspconfig",
    dependencies = {
      "mason.nvim",
      "williamboman/mason-lspconfig.nvim",
    },
    ---@class PluginLspOpts
    opts = {
      ---@type lspconfig.options
      servers = {
        tinymist = {
          --- todo: these configuration from lspconfig maybe broken
          single_file_support = true,
          root_dir = function()
            return vim.fn.getcwd()
          end,
          --- See [Tinymist Server Configuration](https://github.com/Myriad-Dreamin/tinymist/blob/main/Configuration.md) for references.
          settings = {
            exportPdf = "onType",
            outputPath = "$dir/$name",
          },
        },
      },
    },
  },

  -- Configure asm-lsp for x86
  lspconfiger.asm_lsp.setup({
    filetypes = { "asm", "nasm" }, -- Recognize assembly file types
    --root_dir = lspconfiger.util.root_pattern(".git", "."), -- Set project root
    single_file_support = true, -- Enable for single files
    settings = {
      architecture = "x86", -- Force asm-lsp to use x86 architecture
    },
  }),

  {
    "folke/tokyonight.nvim",
    lazy = false,
    priority = 1000,
    opts = {},
  },
}
