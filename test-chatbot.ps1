# AWS CloudOps Chatbot - Interactive Testing Script
param(
    [string]$TestType = "interactive"
)

Write-Host "🚀 AWS CloudOps Chatbot - Testing Suite" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Yellow

function Test-Endpoint {
    param([string]$Uri, [string]$Method = "GET", [string]$Body = $null, [string]$Description)
    Write-Host "`n🔍 Testing: $Description" -ForegroundColor Cyan
    try {
        if ($Body) {
            $response = Invoke-WebRequest -Uri $Uri -Method $Method -ContentType "application/json" -Body $Body -UseBasicParsing
        } else {
            $response = Invoke-WebRequest -Uri $Uri -Method $Method -UseBasicParsing
        }
        Write-Host "✅ Status: $($response.StatusCode)" -ForegroundColor Green
        $content = $response.Content
        if ($content.Length -gt 200) {
            Write-Host "📄 Response: $($content.Substring(0,200))..." -ForegroundColor White
        } else {
            Write-Host "📄 Response: $content" -ForegroundColor White
        }
        return $response.Content
    } catch {
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function Test-Chat {
    param([string]$Message, [string]$Description)
    Write-Host "`n💬 Testing Chat: $Description" -ForegroundColor Magenta
    $body = "{`"message`": `"$Message`", `"accountMode`": `"our`"}"
    $response = Test-Endpoint -Uri "http://localhost:5000/chat" -Method "POST" -Body $body -Description "Chat: $Message"
    if ($response) {
        $json = $response | ConvertFrom-Json
        Write-Host "🤖 Bot Reply: $($json.botReply)" -ForegroundColor Yellow
        Write-Host "🎯 Intent: $($json.intent)" -ForegroundColor Cyan
    }
}

function Run-InteractiveTest {
    Write-Host "`n🎮 Interactive Testing Mode" -ForegroundColor Green
    Write-Host "Type 'exit' to quit, 'help' for commands" -ForegroundColor White

    while ($true) {
        $input = Read-Host "`nYou"
        if ($input -eq "exit") { break }
        if ($input -eq "help") {
            Write-Host "Commands:" -ForegroundColor Yellow
            Write-Host "  'hello' - Test greeting" -ForegroundColor White
            Write-Host "  'deploy' - Test deployment intent" -ForegroundColor White
            Write-Host "  'help' - Show this help" -ForegroundColor White
            Write-Host "  'exit' - Quit testing" -ForegroundColor White
            continue
        }

        Test-Chat -Message $input -Description "User input: $input"
    }
}

function Run-FullTest {
    Write-Host "`n🧪 Running Full Test Suite..." -ForegroundColor Green

    # Health Check
    Test-Endpoint -Uri "http://localhost:5000/health" -Description "Health Check"

    # Templates
    Test-Endpoint -Uri "http://localhost:5000/api/templates" -Description "Templates API"

    # Session Creation
    $sessionResponse = Test-Endpoint -Uri "http://localhost:5000/api/session" -Method "POST" -Body '{"accountMode": "our"}' -Description "Session Creation"
    if ($sessionResponse) {
        $sessionData = $sessionResponse | ConvertFrom-Json
        $sessionId = $sessionData.sessionId
        Write-Host "📝 Session ID: $sessionId" -ForegroundColor Cyan
    }

    # Conversational Tests
    Test-Chat -Message "hello" -Description "Greeting Test"
    Test-Chat -Message "what can you do" -Description "Capabilities Test"
    Test-Chat -Message "deploy a serverless api" -Description "Deployment Intent Test"
    Test-Chat -Message "list my resources" -Description "Resource Management Test"

    Write-Host "`n✅ Full Test Suite Complete!" -ForegroundColor Green
}

# Main execution
switch ($TestType) {
    "health" {
        Test-Endpoint -Uri "http://localhost:5000/health" -Description "Health Check"
    }
    "chat" {
        Test-Chat -Message "hello" -Description "Basic Chat Test"
    }
    "full" {
        Run-FullTest
    }
    "interactive" {
        Run-InteractiveTest
    }
    default {
        Write-Host "Usage: .\test-chatbot.ps1 -TestType [health|chat|full|interactive]" -ForegroundColor Yellow
        Write-Host "Running interactive mode..." -ForegroundColor Cyan
        Run-InteractiveTest
    }
}