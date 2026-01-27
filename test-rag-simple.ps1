# Test RAG Server
$RAG_SERVER = "http://localhost:8080"
$AUTH_TOKEN = "dev-token-123"
$ENDPOINT = "/rag/api/chat/completions"
$QUESTION = "Quels sont les concepts cles?"

Write-Host "BTP RAG Server Test" -ForegroundColor Green
Write-Host "===================" -ForegroundColor Green
Write-Host ""

$body = @{
    model = "rag-hybrid"
    messages = @(@{ role = "user"; content = $QUESTION })
    stream = $false
}

$json = $body | ConvertTo-Json -Depth 5 -Compress

Write-Host "Sending request..."
Write-Host ""

try {
    $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    
    $response = Invoke-WebRequest `
        -Uri "$RAG_SERVER$ENDPOINT" `
        -Headers @{
            "Authorization" = "Bearer $AUTH_TOKEN"
            "Content-Type" = "application/json"
        } `
        -Method Post `
        -Body $bodyBytes `
        -TimeoutSec 60
    
    Write-Host "Success! Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host ""
    
    $responseContent = $response.Content | ConvertFrom-Json
    Write-Host ($responseContent | ConvertTo-Json -Depth 10)
}
catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $stream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $errorContent = $reader.ReadToEnd()
        Write-Host "Response: $errorContent"
    }
}
