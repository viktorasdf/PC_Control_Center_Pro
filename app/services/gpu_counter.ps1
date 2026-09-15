$ErrorActionPreference = "SilentlyContinue"

$samples = (Get-Counter '\GPU Engine(*)\Utilization Percentage').CounterSamples

$values = @(
    $samples |
    Where-Object {
        $_.CookedValue -gt 0
    } |
    ForEach-Object {
        [double]$_.CookedValue
    }
)

if ($values.Count -gt 0) {
    [math]::Round(
        ($values | Measure-Object -Maximum).Maximum,
        0
    )
}
else {
    0
}
