
$ErrorActionPreference = "Stop"

$AGENT_VERSION = "0.1.0"

function New-Check {
    param(
        [string]$ControlId,
        [string]$Status,
        [string]$Severity,
        [string]$Message,
        [object]$Evidence
    )

    return @{
        control_id = $ControlId
        status = $Status
        severity = $Severity
        message = $Message
        evidence = @{
            observed_value = $Evidence
            source = "windows_powershell"
        }
    }
}

function Get-FirewallCheck {
    try {
        $profiles = Get-NetFirewallProfile
        $disabled = @($profiles | Where-Object { -not $_.Enabled })

        if ($disabled.Count -eq 0) {
            return New-Check `
                -ControlId "FIREWALL-001" `
                -Status "ok" `
                -Severity "low" `
                -Message "Tous les profils du pare-feu Windows sont actifs." `
                -Evidence "Tous les profils sont activés"
        }

        return New-Check `
            -ControlId "FIREWALL-001" `
            -Status "attention" `
            -Severity "high" `
            -Message "Au moins un profil du pare-feu Windows est désactivé." `
            -Evidence ($disabled.Name -join ", ")
    }
    catch {
        return New-Check `
            -ControlId "FIREWALL-001" `
            -Status "non_verifie" `
            -Severity "high" `
            -Message "Impossible de vérifier le pare-feu Windows." `
            -Evidence $_.Exception.Message
    }
}

function Get-PortsCheck {
    try {
        $ports = @(Get-NetTCPConnection -State Listen -ErrorAction Stop)

        $details = @(
            $ports | ForEach-Object {
                "$($_.LocalAddress):$($_.LocalPort)"
            }
        )

        if ($ports.Count -eq 0) {
            $status = "ok"
            $severity = "low"
            $message = "Aucun port TCP en écoute détecté."
        }
        else {
            $status = "attention"
            $severity = "medium"
            $message = "$($ports.Count) connexion(s) TCP en écoute détectée(s). Une analyse est nécessaire."
        }

        return New-Check `
            -ControlId "NETWORK-PORTS-001" `
            -Status $status `
            -Severity $severity `
            -Message $message `
            -Evidence ($details -join "; ")
    }
    catch {
        return New-Check `
            -ControlId "NETWORK-PORTS-001" `
            -Status "non_verifie" `
            -Severity "medium" `
            -Message "Impossible de récupérer les ports TCP en écoute." `
            -Evidence $_.Exception.Message
    }
}

function Get-UpdatesCheck {
    try {
        $session = New-Object -ComObject Microsoft.Update.Session
        $searcher = $session.CreateUpdateSearcher()
        $result = $searcher.Search("IsInstalled=0 and IsHidden=0")

        $count = $result.Updates.Count

        if ($count -eq 0) {
            $status = "ok"
            $message = "Aucune mise à jour applicable en attente n'a été détectée."
        }
        else {
            $status = "attention"
            $message = "$count mise(s) à jour applicable(s) en attente."
        }

        return New-Check `
            -ControlId "UPDATES-001" `
            -Status $status `
            -Severity "medium" `
            -Message $message `
            -Evidence "$count mise(s) à jour en attente"
    }
    catch {
        return New-Check `
            -ControlId "UPDATES-001" `
            -Status "non_verifie" `
            -Severity "medium" `
            -Message "Impossible de vérifier les mises à jour Windows." `
            -Evidence $_.Exception.Message
    }
}

$hostname = $env:COMPUTERNAME
$os = Get-CimInstance Win32_OperatingSystem

$checks = @(
    (Get-FirewallCheck)
    (Get-PortsCheck)
    (Get-UpdatesCheck)
)

$result = @{
    schema_version = "1.0"

    asset = @{
        asset_id = $hostname
        hostname = $hostname
        platform = "windows"
        os_version = $os.Caption + " " + $os.Version
    }

    agent = @{
        version = $AGENT_VERSION
    }

    collected_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

    checks = @($checks)
}

$result | ConvertTo-Json -Depth 8

