# push_to_github.ps1
# Run this from PowerShell inside the commercial-pricing-simulator folder,
# AFTER you have created an empty repository on GitHub.com (no README/license,
# so it stays empty) and copied its HTTPS URL.
#
# Usage:
#   .\push_to_github.ps1 -RepoUrl "https://github.com/<your-username>/commercial-pricing-simulator.git"

param(
    [Parameter(Mandatory = $true)]
    [string]$RepoUrl
)

Write-Host "Initializing git repository..." -ForegroundColor Cyan
git init

Write-Host "Setting default branch to main..." -ForegroundColor Cyan
git branch -M main

Write-Host "Adding all files..." -ForegroundColor Cyan
git add .

Write-Host "Creating initial commit..." -ForegroundColor Cyan
git commit -m "Initial commit: Commercial Proposal & Pricing Simulator"

Write-Host "Adding remote origin: $RepoUrl" -ForegroundColor Cyan
git remote add origin $RepoUrl

Write-Host "Pushing to GitHub..." -ForegroundColor Green
git push -u origin main

Write-Host "Done. Check your repository on GitHub." -ForegroundColor Green
