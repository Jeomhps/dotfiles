#!/usr/bin/env lua
local PROG = "script_package_version"

local handle, popen_err = io.popen('git log -p -G "PackageVersion" -- "*.csproj"')

if not handle then
  io.stderr:write(PROG .. ": could not run git: " .. (popen_err or "unknown error") .. "\n")
  os.exit(1)
end

local commit = nil
local proj   = nil

for line in handle:lines() do

  -- New commit
  local sha = line:match("^commit (%x+)")
  if sha then
    if commit then io.write("\n") end
    commit = sha
    proj   = nil
    print("commit : " .. commit .. " :")

  -- File header  (+++ b/some/path/Foo.csproj)
  else
    local path = line:match("^%+%+%+ b/(.*%.csproj)$")
    if path then
      -- grab just the filename, strip extension
      proj = path:match("([^/]+)%.csproj$")

    -- Changed line containing <PackageVersion>
    elseif line:match("^%+.*<PackageVersion>") then
      local version = line:match("<PackageVersion>([^<]+)</PackageVersion>")
      if version and version ~= "" then
        if proj then
          print(proj .. " : v" .. version)
        else
          io.stderr:write(PROG .. ": warning: found PackageVersion with no associated project file\n")
        end
      end
    end
  end

end

local ok, reason, code = handle:close()
if not ok then
  io.stderr:write(PROG .. ": git exited with " .. (reason or "unknown reason") .. " " .. (code or "") .. "\n")
  os.exit(1)
end
