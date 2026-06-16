param(
    [string]$DefaultBaseUrl = "https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1",
    [string]$DefaultModel = ""
)

$ErrorActionPreference = "Stop"

function Read-ValueOrDefault {
    param(
        [string]$Prompt,
        [string]$Default
    )

    if ([string]::IsNullOrWhiteSpace($Default)) {
        $value = Read-Host $Prompt
    }
    else {
        $value = Read-Host "$Prompt [$Default]"
    }

    if ([string]::IsNullOrWhiteSpace($value)) {
        return $Default
    }
    return $value.Trim()
}

$baseUrl = Read-ValueOrDefault -Prompt "LLM_BASE_URL" -Default $DefaultBaseUrl
$model = Read-ValueOrDefault -Prompt "LLM_MODEL" -Default $DefaultModel

if ([string]::IsNullOrWhiteSpace($baseUrl)) {
    throw "LLM_BASE_URL is required."
}
if ([string]::IsNullOrWhiteSpace($model)) {
    throw "LLM_MODEL is required."
}

$secureKey = Read-Host "Paste LLM_API_KEY" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)

try {
    $apiKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    if ([string]::IsNullOrWhiteSpace($apiKey)) {
        throw "LLM_API_KEY is empty."
    }

    $envPath = ".env"
    $existing = @{}

    if (Test-Path -LiteralPath $envPath) {
        foreach ($line in Get-Content -LiteralPath $envPath) {
            if ($line -match "^\s*([^#][^=]*)=(.*)$") {
                $existing[$matches[1].Trim()] = $matches[2]
            }
        }
    }

    $existing["LLM_BASE_URL"] = $baseUrl
    $existing["LLM_MODEL"] = $model
    $existing["LLM_API_KEY"] = $apiKey.Trim()
    if (-not $existing.ContainsKey("LLM_TEMPERATURE")) {
        $existing["LLM_TEMPERATURE"] = "0.2"
    }
    if (-not $existing.ContainsKey("LLM_TIMEOUT")) {
        $existing["LLM_TIMEOUT"] = "60"
    }

    $orderedKeys = @("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL", "LLM_TEMPERATURE", "LLM_TIMEOUT")
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("# OpenAI-compatible LLM provider config")
    foreach ($key in $orderedKeys) {
        if ($existing.ContainsKey($key)) {
            $lines.Add("$key=$($existing[$key])")
        }
    }

    $lines | Set-Content -LiteralPath $envPath -Encoding UTF8

    if (Test-Path -LiteralPath ".gitignore") {
        $gitignore = Get-Content -LiteralPath ".gitignore" -Raw
        if ($gitignore -notmatch "(?m)^\.env$") {
            Add-Content -LiteralPath ".gitignore" -Value ".env"
        }
    }

    Write-Host "OK: .env saved. LLM_API_KEY was not printed."
}
finally {
    if ($bstr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}
