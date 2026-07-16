$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$externalDataDir = Join-Path $repoRoot "docs\external_data"
$outputPath = Join-Path $externalDataDir "34_WORKBOOK_EXECUCAO_HUMANA_PILOTO_VIDEO_V1.xlsm"

$taxonomyCsvPath = Join-Path $externalDataDir "31_TAXONOMIA_PILOTO_VIDEO_V1.csv"
$dimensionsCsvPath = Join-Path $externalDataDir "32_DIMENSOES_COMPLEMENTARES_PILOTO_VIDEO_V1.csv"
$sampleCsvPath = Join-Path $externalDataDir "33_AMOSTRA_PILOTO_10_VIDEOS_V1.csv"

function Escape-XmlText {
    param([AllowNull()][string]$Value)

    if ($null -eq $Value) {
        return ""
    }

    return [System.Security.SecurityElement]::Escape($Value)
}

function Get-ExcelColumnName {
    param([int]$ColumnNumber)

    $name = ""
    $current = $ColumnNumber

    while ($current -gt 0) {
        $current--
        $name = [char](65 + ($current % 26)) + $name
        $current = [math]::Floor($current / 26)
    }

    return $name
}

function New-InlineCellXml {
    param(
        [string]$CellRef,
        [AllowNull()][string]$Value
    )

    $escaped = Escape-XmlText $Value
    return "<c r=`"$CellRef`" t=`"inlineStr`"><is><t xml:space=`"preserve`">$escaped</t></is></c>"
}

function New-WorksheetXml {
    param(
        [string]$SheetName,
        [string[]]$Headers,
        [object[]]$Rows,
        [hashtable]$HyperlinkMap = @{},
        [object[]]$DataValidationSpecs = @(),
        [int]$FreezeTopRows = 1
    )

    $sheetData = New-Object System.Collections.Generic.List[string]
    $hyperlinks = New-Object System.Collections.Generic.List[string]
    $hasSheetRelationships = $false

    $allRows = @()
    $allRows += ,$Headers
    foreach ($row in $Rows) {
        $allRows += ,$row
    }

    for ($rowIndex = 0; $rowIndex -lt $allRows.Count; $rowIndex++) {
        $excelRow = $rowIndex + 1
        $cells = New-Object System.Collections.Generic.List[string]
        $rowValues = $allRows[$rowIndex]
        for ($colIndex = 0; $colIndex -lt $Headers.Count; $colIndex++) {
            $cellRef = "{0}{1}" -f (Get-ExcelColumnName ($colIndex + 1)), $excelRow
            $value = ""
            if ($colIndex -lt $rowValues.Count) {
                $value = [string]$rowValues[$colIndex]
            }
            $cells.Add((New-InlineCellXml -CellRef $cellRef -Value $value))

            if ($rowIndex -gt 0 -and $HyperlinkMap.ContainsKey($cellRef)) {
                $relationId = $HyperlinkMap[$cellRef].RelationshipId
                $hyperlinks.Add("<hyperlink ref=`"$cellRef`" r:id=`"$relationId`"/>")
                $hasSheetRelationships = $true
            }
        }
        $sheetData.Add("<row r=`"$excelRow`">$($cells -join '')</row>")
    }

    $maxRow = [math]::Max(1, $allRows.Count)
    $maxColName = Get-ExcelColumnName $Headers.Count
    $dimensionRef = "A1:{0}{1}" -f $maxColName, $maxRow

    $sheetViewXml = ""
    if ($FreezeTopRows -gt 0) {
        $sheetViewXml = @"
  <sheetViews>
    <sheetView workbookViewId="0">
      <pane ySplit="$FreezeTopRows" topLeftCell="A$($FreezeTopRows + 1)" activePane="bottomLeft" state="frozen"/>
      <selection pane="bottomLeft" activeCell="A$($FreezeTopRows + 1)" sqref="A$($FreezeTopRows + 1)"/>
    </sheetView>
  </sheetViews>
"@
    }

    $dataValidationXml = ""
    if ($DataValidationSpecs.Count -gt 0) {
        $validationItems = foreach ($spec in $DataValidationSpecs) {
            "<dataValidation type=`"list`" allowBlank=`"1`" showErrorMessage=`"0`" sqref=`"$($spec.Sqref)`"><formula1>$([System.Security.SecurityElement]::Escape($spec.Formula1))</formula1></dataValidation>"
        }
        $dataValidationXml = "<dataValidations count=`"$($DataValidationSpecs.Count)`">$($validationItems -join '')</dataValidations>"
    }

    $hyperlinksXml = ""
    if ($hyperlinks.Count -gt 0) {
        $hyperlinksXml = "<hyperlinks>$($hyperlinks -join '')</hyperlinks>"
    }

    $worksheetXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <dimension ref="$dimensionRef"/>
$sheetViewXml  <sheetFormatPr defaultRowHeight="15"/>
  <sheetData>$($sheetData -join '')</sheetData>
  $hyperlinksXml
  $dataValidationXml
</worksheet>
"@

    return [pscustomobject]@{
        Xml = $worksheetXml
        HasRelationships = $hasSheetRelationships
    }
}

function New-RelationshipXml {
    param(
        [string]$Id,
        [string]$Type,
        [string]$Target,
        [string]$TargetMode = ""
    )

    if ($TargetMode) {
        return "<Relationship Id=`"$Id`" Type=`"$Type`" Target=`"$Target`" TargetMode=`"$TargetMode`"/>"
    }

    return "<Relationship Id=`"$Id`" Type=`"$Type`" Target=`"$Target`"/>"
}

function Format-DurationFromSeconds {
    param([AllowNull()][string]$SecondsText)

    if ([string]::IsNullOrWhiteSpace($SecondsText)) {
        return ""
    }

    $normalized = $SecondsText.Trim()
    $secondsValue = 0.0
    $parsed = [double]::TryParse(
        $normalized,
        [System.Globalization.NumberStyles]::Float,
        [System.Globalization.CultureInfo]::InvariantCulture,
        [ref]$secondsValue
    )
    if (-not $parsed) {
        $parsed = [double]::TryParse(
            $normalized,
            [System.Globalization.NumberStyles]::Float,
            [System.Globalization.CultureInfo]::CurrentCulture,
            [ref]$secondsValue
        )
    }
    if (-not $parsed) {
        return $normalized
    }

    $seconds = [int][math]::Round($secondsValue, 0, [MidpointRounding]::AwayFromZero)
    return ([TimeSpan]::FromSeconds($seconds)).ToString("hh\:mm\:ss")
}

function Write-Utf8File {
    param(
        [string]$Path,
        [string]$Content
    )

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

$taxonomyRows = @(Import-Csv -Path $taxonomyCsvPath -Encoding UTF8)
$dimensionRows = @(Import-Csv -Path $dimensionsCsvPath -Encoding UTF8)
$sampleRows = @(Import-Csv -Path $sampleCsvPath -Encoding UTF8)

$mergedTaxonomyRows = @($taxonomyRows + $dimensionRows | Sort-Object dimension, parent_code, code)
$primarySampleRows = @(
    $sampleRows |
        Where-Object { $_.slot_group -like "*_primary" } |
        Sort-Object @{
            Expression = {
                if ($_.slot_group -eq "short_primary") { 1 }
                elseif ($_.slot_group -eq "long_primary") { 2 }
                else { 3 }
            }
        }, @{ Expression = { [int]$_.priority_rank } }
)

$dropdownDimensions = @(
    "niche",
    "sub_niche",
    "sub_sub_niche",
    "content_type",
    "audience_intent",
    "vehicle_brand",
    "vehicle_model",
    "vehicle_year_or_generation",
    "automotive_system",
    "component",
    "problem"
)

$listValues = [ordered]@{}
foreach ($dimension in $dropdownDimensions) {
    $sourceRows = if ($dimension -in @("vehicle_brand", "vehicle_model", "vehicle_year_or_generation", "automotive_system", "component", "problem")) {
        $dimensionRows
    }
    else {
        $mergedTaxonomyRows
    }

    $values = @(
        $sourceRows |
            Where-Object { $_.dimension -eq $dimension } |
            ForEach-Object { $_.code } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
            Sort-Object -Unique
    )
    $listValues[$dimension] = $values
}
$listValues["classificacao_finalizada"] = @("sim", "nao")

$taxHeaders = @(
    "dimension",
    "code",
    "label_pt",
    "parent_code",
    "description",
    "example_signals",
    "allowed_in_pilot"
)

$taxRows = foreach ($row in $mergedTaxonomyRows) {
    @(
        $row.dimension,
        $row.code,
        $row.label_pt,
        $row.parent_code,
        $row.description,
        $row.example_signals,
        $row.allowed_in_pilot
    )
}

$execHeaders = @(
    "post_id",
    "video_url",
    "title",
    "creator",
    "video_type",
    "followers",
    "views",
    "likes",
    "comments",
    "engagement_pct",
    "post_date",
    "duration",
    "niche",
    "sub_niche",
    "sub_sub_niche",
    "content_type",
    "audience_intent",
    "vehicle_brand",
    "vehicle_model",
    "vehicle_year_or_generation",
    "automotive_system",
    "component",
    "problem",
    "observacoes",
    "classificacao_finalizada"
)

$execRows = New-Object System.Collections.Generic.List[object]
$execHyperlinks = @{}
$execSheetRelationships = New-Object System.Collections.Generic.List[string]
$execRelationshipCounter = 1

for ($index = 0; $index -lt $primarySampleRows.Count; $index++) {
    $row = $primarySampleRows[$index]
    $excelRow = $index + 2
    $videoLinkRef = "B$excelRow"
    $relationshipId = "rId$execRelationshipCounter"
    $execRelationshipCounter++
    $execHyperlinks[$videoLinkRef] = [pscustomobject]@{
        RelationshipId = $relationshipId
        Url = "https://www.youtube.com/watch?v=$($row.post_id)"
    }
    $execSheetRelationships.Add(
        (New-RelationshipXml -Id $relationshipId -Type "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" -Target $execHyperlinks[$videoLinkRef].Url -TargetMode "External")
    )

    $execRows.Add(@(
        $row.post_id,
        "abrir_video",
        $row.title,
        $row.creator,
        $row.video_type,
        $row.followers,
        $row.views,
        $row.likes,
        $row.comments,
        $row.engagement_pct,
        $row.post_date,
        (Format-DurationFromSeconds $row.duration_seconds),
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        ""
    ))
}

$listHeaders = @($listValues.Keys)
$maxListRows = ($listValues.Values | ForEach-Object { $_.Count } | Measure-Object -Maximum).Maximum
$listRows = New-Object System.Collections.Generic.List[object]
for ($i = 0; $i -lt $maxListRows; $i++) {
    $rowValues = @()
    foreach ($header in $listHeaders) {
        if ($i -lt $listValues[$header].Count) {
            $rowValues += $listValues[$header][$i]
        }
        else {
            $rowValues += ""
        }
    }
    $listRows.Add($rowValues)
}

$definedNames = New-Object System.Collections.Generic.List[string]
for ($i = 0; $i -lt $listHeaders.Count; $i++) {
    $header = $listHeaders[$i]
    $columnName = Get-ExcelColumnName ($i + 1)
    $endRow = $listValues[$header].Count + 1
    $definedNames.Add("<definedName name=`"$header`">listas!`$$columnName`$2:`$$columnName`$$endRow</definedName>")
}

$validationTargetEndRow = 200
$execDataValidationSpecs = @(
    @{ Sqref = "M2:M$validationTargetEndRow"; Formula1 = "=niche" },
    @{ Sqref = "N2:N$validationTargetEndRow"; Formula1 = "=sub_niche" },
    @{ Sqref = "O2:O$validationTargetEndRow"; Formula1 = "=sub_sub_niche" },
    @{ Sqref = "P2:P$validationTargetEndRow"; Formula1 = "=content_type" },
    @{ Sqref = "Q2:Q$validationTargetEndRow"; Formula1 = "=audience_intent" },
    @{ Sqref = "R2:R$validationTargetEndRow"; Formula1 = "=vehicle_brand" },
    @{ Sqref = "S2:S$validationTargetEndRow"; Formula1 = "=vehicle_model" },
    @{ Sqref = "T2:T$validationTargetEndRow"; Formula1 = "=vehicle_year_or_generation" },
    @{ Sqref = "U2:U$validationTargetEndRow"; Formula1 = "=automotive_system" },
    @{ Sqref = "V2:V$validationTargetEndRow"; Formula1 = "=component" },
    @{ Sqref = "W2:W$validationTargetEndRow"; Formula1 = "=problem" },
    @{ Sqref = "Y2:Y$validationTargetEndRow"; Formula1 = "=classificacao_finalizada" }
)

$taxonomySheet = New-WorksheetXml -SheetName "taxonomias" -Headers $taxHeaders -Rows $taxRows
$executionSheet = New-WorksheetXml -SheetName "execucao_humana" -Headers $execHeaders -Rows $execRows -HyperlinkMap $execHyperlinks -DataValidationSpecs $execDataValidationSpecs
$listsSheet = New-WorksheetXml -SheetName "listas" -Headers $listHeaders -Rows $listRows

$contentTypesXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.ms-excel.sheet.macroEnabled.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet3.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"@

$packageRelsXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"@

$workbookXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <bookViews>
    <workbookView xWindow="120" yWindow="120" windowWidth="28800" windowHeight="16800"/>
  </bookViews>
  <sheets>
    <sheet name="taxonomias" sheetId="1" r:id="rId1"/>
    <sheet name="execucao_humana" sheetId="2" r:id="rId2"/>
    <sheet name="listas" sheetId="3" state="hidden" r:id="rId3"/>
  </sheets>
  <definedNames>
    $($definedNames -join '')
  </definedNames>
</workbook>
"@

$workbookRelsXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet3.xml"/>
</Relationships>
"@

$executionSheetRelsXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  $($execSheetRelationships -join '')
</Relationships>
"@

$createdAt = (Get-Date).ToUniversalTime().ToString("s") + "Z"
$coreXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Workbook Execucao Humana Piloto Video v1</dc:title>
  <dc:subject>Sprint 6</dc:subject>
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">$createdAt</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">$createdAt</dcterms:modified>
</cp:coreProperties>
"@

$appXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex Open XML Builder</Application>
  <DocSecurity>0</DocSecurity>
  <ScaleCrop>false</ScaleCrop>
  <HeadingPairs>
    <vt:vector size="2" baseType="variant">
      <vt:variant><vt:lpstr>Worksheets</vt:lpstr></vt:variant>
      <vt:variant><vt:i4>3</vt:i4></vt:variant>
    </vt:vector>
  </HeadingPairs>
  <TitlesOfParts>
    <vt:vector size="3" baseType="lpstr">
      <vt:lpstr>taxonomias</vt:lpstr>
      <vt:lpstr>execucao_humana</vt:lpstr>
      <vt:lpstr>listas</vt:lpstr>
    </vt:vector>
  </TitlesOfParts>
  <Company>OpenAI</Company>
  <LinksUpToDate>false</LinksUpToDate>
  <SharedDoc>false</SharedDoc>
  <HyperlinksChanged>false</HyperlinksChanged>
  <AppVersion>1.0</AppVersion>
</Properties>
"@

$tempRoot = Join-Path $env:TEMP ("pilot_workbook_" + [guid]::NewGuid().ToString("N"))
if (Test-Path $tempRoot) {
    Remove-Item $tempRoot -Recurse -Force
}

New-Item -ItemType Directory -Path $tempRoot | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempRoot "_rels") | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempRoot "docProps") | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempRoot "xl") | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempRoot "xl\_rels") | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempRoot "xl\worksheets") | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempRoot "xl\worksheets\_rels") | Out-Null

Write-Utf8File -Path (Join-Path $tempRoot "[Content_Types].xml") -Content $contentTypesXml
Write-Utf8File -Path (Join-Path $tempRoot "_rels\.rels") -Content $packageRelsXml
Write-Utf8File -Path (Join-Path $tempRoot "docProps\core.xml") -Content $coreXml
Write-Utf8File -Path (Join-Path $tempRoot "docProps\app.xml") -Content $appXml
Write-Utf8File -Path (Join-Path $tempRoot "xl\workbook.xml") -Content $workbookXml
Write-Utf8File -Path (Join-Path $tempRoot "xl\_rels\workbook.xml.rels") -Content $workbookRelsXml
Write-Utf8File -Path (Join-Path $tempRoot "xl\worksheets\sheet1.xml") -Content $taxonomySheet.Xml
Write-Utf8File -Path (Join-Path $tempRoot "xl\worksheets\sheet2.xml") -Content $executionSheet.Xml
Write-Utf8File -Path (Join-Path $tempRoot "xl\worksheets\sheet3.xml") -Content $listsSheet.Xml
Write-Utf8File -Path (Join-Path $tempRoot "xl\worksheets\_rels\sheet2.xml.rels") -Content $executionSheetRelsXml

if (Test-Path $outputPath) {
    Remove-Item $outputPath -Force
}

$zipPath = "$outputPath.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Compress-Archive -Path (Join-Path $tempRoot "*") -DestinationPath $zipPath -Force
Move-Item -Path $zipPath -Destination $outputPath -Force
Remove-Item -Path $tempRoot -Recurse -Force

Write-Output "Workbook generated at $outputPath"
