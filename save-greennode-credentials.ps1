param(
    [string]$ClientId = "7a522d58-4987-4562-a7f5-63084e40cedf"
)

$ErrorActionPreference = "Stop"

Write-Host "Saving GreenNode IAM credentials for client_id: $($ClientId.Substring(0, 8))..."
$secureSecret = Read-Host "Paste GREENNODE_CLIENT_SECRET" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureSecret)

try {
    $secret = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    if ([string]::IsNullOrWhiteSpace($secret)) {
        throw "Client secret is empty."
    }

    $credentials = [ordered]@{
        client_id     = $ClientId
        client_secret = $secret.Trim()
    }

    $credentials |
        ConvertTo-Json |
        Set-Content -LiteralPath ".greennode.json" -Encoding UTF8

    foreach ($ignoreFile in @(".gitignore", ".dockerignore")) {
        if (Test-Path -LiteralPath $ignoreFile) {
            $content = Get-Content -LiteralPath $ignoreFile -Raw
            if ($content -notmatch "(?m)^\.greennode\.json$") {
                Add-Content -LiteralPath $ignoreFile -Value ".greennode.json"
            }
        }
        else {
            Set-Content -LiteralPath $ignoreFile -Value ".greennode.json" -Encoding UTF8
        }
    }

    $saved = Get-Content -LiteralPath ".greennode.json" -Raw | ConvertFrom-Json
    if (-not $saved.client_id -or -not $saved.client_secret) {
        throw "Credential file was written but required fields are missing."
    }

    Write-Host "OK: .greennode.json saved. Secret was not printed."
}
finally {
    if ($bstr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}
