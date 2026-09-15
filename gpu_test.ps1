Get-Counter '\GPU Engine(*)\Utilization Percentage' |
    Select-Object -ExpandProperty CounterSamples |
    Where-Object { $_.CookedValue -gt 0 } |
    ForEach-Object {
        Write-Output "$($_.InstanceName)|$([math]::Round($_.CookedValue, 2))"
    }
