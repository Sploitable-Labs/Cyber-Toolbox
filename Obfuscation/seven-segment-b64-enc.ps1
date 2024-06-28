$script = @'
$sevenSegmentDigits = @(
    @(' _ ','| |','|_|'),  # 0
    @('   ','  |','  |'),  # 1
    @(' _ ',' _|','|_ '),  # 2
    @(' _ ',' _|',' _|'),  # 3
    @('   ','|_|','  |'),  # 4
    @(' _ ','|_ ',' _|'),  # 5
    @(' _ ','|_ ','|_|'),  # 6
    @(' _ ','  |','  |'),  # 7
    @(' _ ','|_|','|_|'),  # 8
    @(' _ ','|_|','  |')   # 9
)

$number = Read-Host "Enter a number"

if ($number -match '^\d+$') {
    $digits = $number.ToCharArray() 
    for ($i = 0; $i -lt 3; $i++) {
        $line = ''
        foreach ($digit in $digits) {
            $line += $sevenSegmentDigits[$digit-48][$i]
        }
        Write-Output $line
    }
}
else {
    Write-Output "Invalid input: Please enter a number."
}
'@

$encodedScript = [System.Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($script))
Write-Output $encodedScript