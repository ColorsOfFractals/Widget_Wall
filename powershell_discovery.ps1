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
# Deduplicate case-insensitively without executing any discovered function.
$descriptionPath = Join-Path $PSScriptRoot 'powershell_descriptions.json'
$descriptions = @{}

if (Test-Path -LiteralPath $descriptionPath -PathType Leaf) {
    $descriptionData = Get-Content -LiteralPath $descriptionPath -Raw |
        ConvertFrom-Json

    foreach ($property in $descriptionData.PSObject.Properties) {
        $descriptions[$property.Name] = [string]$property.Value
    }
}

$unique = New-Object System.Collections.Generic.List[object]
$index = New-Object 'System.Collections.Generic.Dictionary[string,int]' ([System.StringComparer]::OrdinalIgnoreCase)

foreach ($item in $items) {
    if ($index.ContainsKey($item.name)) {
        $existing = $unique[$index[$item.name]]
        $existing.sources += [pscustomobject]@{
            source = $item.source
            line = $item.line
            engine = $item.engine
        }
        continue
    }

    $index.Add($item.name, $unique.Count)

    $unique.Add([pscustomobject]@{
        name = $item.name
        description = [string]$descriptions[$item.name]
        parameters = @($item.parameters)
        source = $item.source
        line = $item.line
        engine = $item.engine
        sources = @(
            [pscustomobject]@{
                source = $item.source
                line = $item.line
                engine = $item.engine
            }
        )
    })
}

[pscustomobject]@{ ok = $true; mode = 'AST only - no profile execution'; functions = @($unique.ToArray()) } |
    ConvertTo-Json -Depth 6 -Compress
