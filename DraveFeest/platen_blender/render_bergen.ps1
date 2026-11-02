# render_bergen.ps1 [snel] [seizoen] - rendert de bergpanorama's (standaard alle 8: 4 seizoenen x dag/avond)
$d = $PSScriptRoot
$b = Join-Path $env:ProgramFiles "Blender Foundation\Blender 5.2\blender.exe"
$uit = Join-Path (Split-Path $d -Parent) "assets\platen"
New-Item -ItemType Directory -Force $uit | Out-Null
$snel = if ($args -contains "snel") { "snel" } else { "" }
$seizoenen = @($args | Where-Object { $_ -in "winter","lente","zomer","herfst" })
if ($seizoenen.Count -eq 0) { $seizoenen = @("winter","lente","zomer","herfst") }
$klaar = Join-Path $env:TEMP "dravefeest_bergen_klaar.txt"; Remove-Item $klaar -ErrorAction SilentlyContinue
foreach ($s in $seizoenen) { foreach ($t in "dag","avond") {
  & $b -b --factory-startup -P "$d\bouw_bergen.py" -- "$uit" $s $t $snel *> (Join-Path $env:TEMP "dravefeest_log_${s}_$t.txt")
} }
"KLAAR" | Out-File $klaar
