New-Item -ItemType Directory -Force -Path examples/assets | Out-Null
"placeholder fan image 01" | Set-Content -Encoding UTF8 examples/assets/fan_01.jpg
"placeholder fan image 02" | Set-Content -Encoding UTF8 examples/assets/fan_02.jpg
"placeholder celebrity image" | Set-Content -Encoding UTF8 examples/assets/star_01.jpg
"placeholder openpose image" | Set-Content -Encoding UTF8 examples/assets/openpose.png
Write-Host "Demo reference placeholders written to examples/assets"
