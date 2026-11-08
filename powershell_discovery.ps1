# RING 0.4.1: Parse function definitions; do not execute profile code.
$ErrorActionPreference = 'Stop'
$paths = @(
    (Join-Path $HOME 'OneDrive\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1'),
    (Join-Path $HOME 'Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1'),
    (Join-Path $HOME 'OneDrive\Documents\PowerShell\Microsoft.PowerShell_profile.ps1'),
    (Join-Path $HOME 'Documents\PowerShell\Microsoft.PowerShell_profile.ps1')
) | Select-Object -Unique
$items = New-Object System.Collections.Generic.List[object]
foreach ($path in $paths) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
    $tokens = $null
    $errors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$errors)
    $defs = $ast.FindAll({ param($node)
        $node -is [System.Management.Automation.Language.FunctionDefinitionAst]
    }, $true)
    foreach ($def in $defs) {
        $names = @()
        if ($def.Body.ParamBlock) {
            $names = @($def.Body.ParamBlock.Parameters | ForEach-Object { $_.Name.VariablePath.UserPath })
        }
        $items.Add([pscustomobject]@{
            name = $def.Name
            parameters = @($names)
            source = $path
            line = $def.Extent.StartLineNumber
            engine = if ($path -match '\\PowerShell\\') { 'PowerShell 7 profile' } else { 'Windows PowerShell profile' }
        })
    }
}
[pscustomobject]@{ ok = $true; mode = 'AST only - no profile execution'; functions = @($items.ToArray()) } |
    ConvertTo-Json -Depth 6 -Compress
