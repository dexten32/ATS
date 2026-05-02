param (
    [string]$TestName = "Load Test"
)

$LogFile = "load_test_results.log"

Write-Host "Running k6 load test..." -ForegroundColor Cyan

# Run k6, show output live in terminal, and capture it for processing
$Output = k6 run load_test.js 2>&1 | Tee-Object -Variable AllOutput

# Find the start of the summary (usually starts with Thresholds or the footer blocks)
$SummaryIndex = $AllOutput | Where-Object { $_ -match "THRESHOLDS|TOTAL RESULTS|checks_total" } | Select-Object -First 1 | ForEach-Object { [array]::IndexOf($AllOutput, $_) }

if ($SummaryIndex -ge 0) {
    # Extract from summary start to end
    $SummaryOutput = $AllOutput[$SummaryIndex..($AllOutput.Length - 1)]
    
    # Write only the Summary to log (No headers as requested)
    $SummaryOutput | Out-File -FilePath $LogFile -Append -Encoding UTF8
    
    Write-Host "`nLoad test completed. Summary saved to $LogFile" -ForegroundColor Green
}
else {
    Write-Warning "Could not find summary metrics in k6 output."
    $AllOutput | Out-File -FilePath $LogFile -Append -Encoding UTF8
}
