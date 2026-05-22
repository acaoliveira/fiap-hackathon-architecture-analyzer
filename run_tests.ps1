# FIAP Hackathon — Rodar todos os testes
$services = @("upload-service", "processing-service", "report-service", "api-gateway")
$total_passed = 0
$total_failed = 0

foreach ($svc in $services) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Testando: $svc" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan

    $path = "C:/Users/alana.oliveira/Desktop/hackathon/services/$svc"
    $result = docker run --rm -v "${path}:/app" -w /app python:3.12-slim `
        bash -c "pip install -r requirements.txt httpx -q 2>/dev/null && python -m pytest tests/ -v --tb=short 2>&1"

    $result | Select-String -Pattern "PASSED|FAILED|ERROR|passed|failed|error|===" | ForEach-Object {
        $line = $_.Line
        if ($line -match "PASSED") { Write-Host $line -ForegroundColor Green }
        elseif ($line -match "FAILED|ERROR") { Write-Host $line -ForegroundColor Red }
        else { Write-Host $line -ForegroundColor White }
    }

    $passMatch = ($result | Select-String "(\d+) passed").Matches
    if ($passMatch) { $total_passed += [int]($passMatch[0].Groups[1].Value) }
    $failMatch = ($result | Select-String "(\d+) failed").Matches
    if ($failMatch) { $total_failed += [int]($failMatch[0].Groups[1].Value) }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RESULTADO FINAL" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PASSED: $total_passed" -ForegroundColor Green
if ($total_failed -gt 0) {
    Write-Host "  FAILED: $total_failed" -ForegroundColor Red
} else {
    Write-Host "  FAILED: 0  -- todos os testes passaram!" -ForegroundColor Green
}
Write-Host ""
