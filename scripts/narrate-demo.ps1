$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$rippleRoot = Split-Path $PSScriptRoot -Parent
$rippleFilm = Get-Content -LiteralPath (Join-Path $rippleRoot 'demo/film-script.json') -Raw | ConvertFrom-Json
$rippleAudio = Join-Path $rippleRoot 'artifacts/film-audio'
New-Item -ItemType Directory -Force -Path $rippleAudio | Out-Null
$rippleVoice = New-Object System.Speech.Synthesis.SpeechSynthesizer
$rippleVoice.SelectVoice($rippleFilm.voice)
$rippleVoice.Rate = 3
$rippleVoice.Volume = 100
foreach ($rippleChapter in $rippleFilm.chapters) {
  $rippleVoice.SetOutputToWaveFile((Join-Path $rippleAudio ($rippleChapter.id + '.wav')))
  $rippleVoice.Speak($rippleChapter.text)
  $rippleVoice.SetOutputToNull()
}
$rippleVoice.Dispose()
Write-Output 'Generated local narration for all 12 chapters.'
