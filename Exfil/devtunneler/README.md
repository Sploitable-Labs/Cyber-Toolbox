# PoC Using devtunnels

## What is devtunnel?
A Microsoft signed binary that can be used to establish a tunnel between any two Windows devices.

[Official docs](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/overview)

## What does it do?
It runs a python webshell on the device where the script is executed. It then binds an anonymous devtunnel to the same port and emails you the URL of the devtunnel. You can then open the link in a browser and access the webshell from anywhere.

The script forces "device code" authenication with GitHub, scrapes the 2FA code and emails it to you so that YOU can authorize the creation of a devtunnel - even if the script is executed from another machine :) effectively bypassing the authentication safety mechanism.

## Setup Part 1
Deploy tunneler.js using [Google App Script](https://script.google.com/home) as a webhook. This script handles POST requests from tunneler.ps1 and emails you the contents.

Note down the URL of the webhook.

## Setup Part 2

Edit the config section of tunneler.ps1:

1. Set your email address.
2. Set the webhook URL.

## How to Operate
In PowerShell run `.\tunneler.ps1`

If you don't already have a copy of devtunnel.exe it will download a fresh copy from Microsoft. This can take a while as its about 22MB!

Check you email inbox. You will get a 2FA code and a link. Use the code to sign-in to GitHub.
Once the tunnel is established you will recieve a second email with a hyperlink to the tunnel.
The link will connect you through to the webshell.

Enjoy.

## Debugging / Experimentation
An example of the python webshell is included in web_shell.py.
You can encode the web shell using encode_webshell.py.
There is an example of how to run encoded_shell.txt using run_webshell.py.
