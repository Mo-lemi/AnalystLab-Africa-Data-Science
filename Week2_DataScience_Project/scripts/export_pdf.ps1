# Export every Word report in ..\Reports to PDF using Microsoft Word.
# Run from the scripts folder:  powershell -File export_pdf.ps1
$reports = Join-Path $PSScriptRoot "..\Reports" | Resolve-Path
$word = New-Object -ComObject Word.Application
$word.Visible = $false
foreach ($docx in Get-ChildItem $reports -Filter *.docx) {
    $pdf = [IO.Path]::ChangeExtension($docx.FullName, ".pdf")
    $doc = $word.Documents.Open($docx.FullName, $false, $true)
    $doc.SaveAs([ref]$pdf, [ref]17)  # 17 = wdFormatPDF
    "{0}: {1} pages" -f $docx.Name, $doc.ComputeStatistics(2)
    $doc.Close($false)
}
$word.Quit()
