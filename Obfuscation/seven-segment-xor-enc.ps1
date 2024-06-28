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

$bytes = [System.Text.Encoding]::UTF8.GetBytes($script)

$key = 123
for ($i = 0; $i -lt $bytes.Length; $i++) {
    $bytes[$i] = $bytes[$i] -bxor $key
}

$xorString = [System.Text.Encoding]::UTF8.GetString($bytes)
Write-Output $xorString


# Define the XOR-encoded string
$xorEncodedString = $xorString

# Convert the XOR-encoded string to bytes
$bytes = [System.Text.Encoding]::UTF8.GetBytes($xorEncodedString)

# Define the XOR key (should be the same key used for encoding)
$key = 123

# Perform XOR operation on each byte using the key to decode
for ($i = 0; $i -lt $bytes.Length; $i++) {
    $bytes[$i] = $bytes[$i] -bxor $key
}

# Convert the resulting bytes back to a string
$decodedString = [System.Text.Encoding]::UTF8.GetString($bytes)

# Output the decoded string
Write-Output $decodedString