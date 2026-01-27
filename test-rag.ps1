<#
.SYNOPSIS
Test RAG endpoint with proper JSON encoding and UTF8 handling
.DESCRIPTION
Reliable PowerShell script to test BTP RAG server with Invoke-WebRequest
#>

# Configuration
$RAG_SERVER = "http://localhost:8080"
$AUTH_TOKEN = "dev-token-123"
$ENDPOINT = "/rag/api/chat/completions"
$TIMEOUT = 60

# Question to test
$QUESTION = "Quels sont les concepts clés?"

Write-Host "🚀 BTP RAG Server Tester" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green
Write-Host ""
Write-Host "Configuration:"
Write-Host "  Server: $RAG_SERVER"
Write-Host "  Endpoint: $ENDPOINT"
Write-Host "  Question: $QUESTION"
Write-Host ""

# Build request body
$body = @{
    model = "rag-hybrid"
    messages = @(@{ 
        role = "user"
        content = $QUESTION 
    })
    stream = $false
}

# Convert to JSON (without pretty printing to avoid encoding issues)
$json = $body | ConvertTo-Json -Depth 5 -Compress

Write-Host "📤 Sending request..."
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
        -TimeoutSec $TIMEOUT
    
    Write-Host "✅ Response received (Status: $($response.StatusCode))" -ForegroundColor Green
    Write-Host ""
    
    $responseContent = $response.Content | ConvertFrom-Json
    
    Write-Host "📋 Response:" -ForegroundColor Cyan
    Write-Host ""
    
    if ($responseContent.choices) {
        $message = $responseContent.choices[0].message.content
        Write-Host "Message:" -ForegroundColor Yellow
        Write-Host $message
        Write-Host ""
    }
    
    if ($responseContent.sources) {
        Write-Host "Sources:" -ForegroundColor Yellow
        foreach ($source in $responseContent.sources) {
            Write-Host "  - $source"
        }
        Write-Host ""
    }
    
    Write-Host "Full Response:" -ForegroundColor DarkGray
    Write-Host ($responseContent | ConvertTo-Json -Depth 10)
    Write-Host ""
    Write-Host "✨ Test completed successfully!" -ForegroundColor Green
}
catch {
    Write-Host "❌ Error occurred:" -ForegroundColor Red
    Write-Host $_.Exception.Message
    Write-Host ""
    
    if ($_.Exception.Response) {
        $errorStream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorStream)
        $errorContent = $reader.ReadToEnd()
        Write-Host "Server response:"
        Write-Host $errorContent
    }
    
    exit 1
}
