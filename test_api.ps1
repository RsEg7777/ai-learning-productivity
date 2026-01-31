$token = "eyJraWQiOiI5Q3JJVmdhMEdrOW9QaDgyQW5lb3lZUFdFVVFTeFhwNkdFeDNUVVRGdmVVPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI1MTIzMGQ5YS1lMDgxLTcwMDgtZmU2Mi1mYmJiMjYwNTFmNjciLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuYXAtc291dGgtMS5hbWF6b25hd3MuY29tXC9hcC1zb3V0aC0xX2NmQTlkejE1aCIsImNsaWVudF9pZCI6IjQ5bjdha3A5bHVibHZwYTA0ZGJ0MnFqb2EyIiwib3JpZ2luX2p0aSI6IjJjMTUwMDI5LWJhYzktNDVhMi05YTgzLTdlYzE3ZDliZjA3NSIsImV2ZW50X2lkIjoiZmE3NmFiY2MtNWQzNS00NDUwLWFjMGUtMWE3NGUwYTNkZDA3IiwidG9rZW5fdXNlIjoiYWNjZXNzIiwic2NvcGUiOiJhd3MuY29nbml0by5zaWduaW4udXNlci5hZG1pbiIsImF1dGhfdGltZSI6MTc2OTg4MTczOCwiZXhwIjoxNzY5ODg1MzM4LCJpYXQiOjE3Njk4ODE3MzgsImp0aSI6IjljZjJmN2Y0LWJjNTgtNGM5My1iNzdiLWJlMjEyNmZlNmUxYiIsInVzZXJuYW1lIjoidGVzdHVzZXIifQ.N_zyGsMurpl3OxfhbZ_eztcZ15GzrEqdUDxYqXBujBRoPavPXm2ay4PIvzWMnjjLNKI2-OICRXk09YtbdArWrDarVdDNjY9bygt0my914jICxG5tnkUd6fsZ7dAr_EtLsz1Ht66XYYIvPM0ERDGPx8CReQRh-KZvQsJXkNb-RFDH5VljE_gmn1vY_Is5u1HpiFEDwbcVNHWgD5MI1ml7-Ciy8PkZQEFjFt9ZBQTFWuHVHC4OccP8hnahgsp8YjEdVmXOZ-mOFNLIRlOqtwdS5i7cyhz0tBen54KFE7KXJ7ubbLj_NietW_ptfkLLJOHfFYn2z4ZdLy4WtyXnuhNM6w"

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

$body = @{
    content = "Python is a high-level programming language. It supports multiple programming paradigms including procedural, object-oriented, and functional programming. Python uses dynamic typing and automatic memory management."
    question_count = 5
} | ConvertTo-Json

Write-Host "Testing Quiz Generation API..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "https://qtyf9c08b4.execute-api.ap-south-1.amazonaws.com/dev/quiz/generate" -Method Post -Headers $headers -Body $body
    Write-Host "Success!" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Response: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
}
