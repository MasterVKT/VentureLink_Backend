# Script de test upload média - PowerShell
# Lancez : .\test_upload.ps1

$BASE_URL = "http://localhost:8000"
$EMAIL = "admin@venturelink.com"
$PASSWORD = "admin123"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  TEST UPLOAD MÉDIAS - VENTURELINK" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# 1. Authentification
Write-Host "`n[1/4] Authentification..." -ForegroundColor Yellow

try {
    $body = @{
        email = $EMAIL
        password = $PASSWORD
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$BASE_URL/api/token/" -Method Post -Body $body -ContentType "application/json"
    $token = $response.access
    Write-Host "✅ Connecté avec succès" -ForegroundColor Green
} catch {
    Write-Host "❌ Échec authentification: $_" -ForegroundColor Red
    Write-Host "   Vérifiez email/mot de passe" -ForegroundColor Yellow
    exit 1
}

# 2. Récupérer un projet
Write-Host "`n[2/4] Récupération d'un projet..." -ForegroundColor Yellow

$headers = @{
    Authorization = "Bearer $token"
}

try {
    $projects = Invoke-RestMethod -Uri "$BASE_URL/api/v1/projects/my-projects/" -Method Get -Headers $headers
    
    if ($projects.results -and $projects.results.Count -gt 0) {
        $projectId = $projects.results[0].id
        Write-Host "✅ Projet trouvé: $projectId" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Aucun projet trouvé, créez-en un d'abord" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Erreur: $_" -ForegroundColor Red
    exit 1
}

# 3. Créer une image de test
Write-Host "`n[3/4] Création image de test..." -ForegroundColor Yellow

try {
    # Créer un bitmap
    $bitmap = New-Object System.Drawing.Bitmap 3000, 2000
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    
    # Fond bleu
    $graphics.Clear([System.Drawing.Color]::Blue)
    
    # Dessiner des cercles
    $brushRed = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::Red)
    $brushGreen = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::Green)
    $brushYellow = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::Yellow)
    
    $graphics.FillEllipse($brushRed, 500, 500, 500, 500)
    $graphics.FillEllipse($brushGreen, 1500, 500, 500, 500)
    $graphics.FillEllipse($brushYellow, 2000, 1000, 500, 500)
    
    # Sauvegarder
    $testImage = "C:\temp\test_upload.jpg"
    if (!(Test-Path "C:\temp")) {
        New-Item -ItemType Directory -Path "C:\temp" | Out-Null
    }
    
    $bitmap.Save($testImage)
    $bitmap.Dispose()
    $graphics.Dispose()
    
    $originalSize = (Get-Item $testImage).Length / 1MB
    Write-Host "✅ Image créée: $testImage" -ForegroundColor Green
    Write-Host "   Taille: $([math]::Round($originalSize, 2)) MB" -ForegroundColor Gray
    Write-Host "   Dimensions: 3000 x 2000 pixels" -ForegroundColor Gray
} catch {
    Write-Host "❌ Erreur création image: $_" -ForegroundColor Red
    exit 1
}

# 4. Uploader l'image
Write-Host "`n[4/4] Upload de l'image..." -ForegroundColor Yellow

try {
    $formData = @{
        file = Get-Item $testImage
        media_type = "IMAGE"
        title = "Test Upload PowerShell"
        description = "Test de compression automatique"
    }
    
    $uploadResponse = Invoke-RestMethod -Uri "$BASE_URL/api/v1/projects/$projectId/media/" -Method Post -Headers $headers -Form $formData
    
    Write-Host "✅ Upload réussi!" -ForegroundColor Green
    Write-Host "   ID: $($uploadResponse.id)" -ForegroundColor Gray
    Write-Host "   Titre: $($uploadResponse.title)" -ForegroundColor Gray
    Write-Host "   URL: $($uploadResponse.file_url)" -ForegroundColor Gray
    
    # Nettoyer
    Remove-Item $testImage -Force
    Write-Host "`n🗑️ Fichier de test supprimé" -ForegroundColor Gray
    
} catch {
    Write-Host "❌ Erreur upload: $_" -ForegroundColor Red
    Write-Host "   Détails: $($_.ErrorDetails.Message)" -ForegroundColor Gray
}

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  TEST TERMINÉ" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
