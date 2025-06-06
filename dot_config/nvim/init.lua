-- bootstrap lazy.nvim, LazyVim and your plugins
require("config.lazy")

require("lspconfig").clangd.setup({})
require("lspconfig").pyright.setup({})

require("lspconfig")["tinymist"].setup({
  settings = {
    formatterMode = "typstyle",
    semanticTokens = "disable",
  },
})
