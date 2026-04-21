import { NextResponse } from "next/server";

// One-shot PowerShell script to bootstrap SSH on a remote Windows machine.
// Usage on target: irm https://aaa-srv.taile7cd0a.ts.net/api/ssh-setup | iex
const SCRIPT = [
  "Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 -ErrorAction SilentlyContinue",
  "Set-Service sshd -StartupType Automatic",
  "Start-Service sshd -ErrorAction SilentlyContinue",
  "Set-Service ssh-agent -StartupType Automatic",
  "Start-Service ssh-agent",
  "New-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -DisplayName 'OpenSSH Server' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 -ErrorAction SilentlyContinue",
  "New-Item -Force -Path \"$env:USERPROFILE\\.ssh\" -ItemType Directory | Out-Null",
  "$key = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFKTM/JRE4M+oNYQEhVErq5eWRyCBh6q4xg9I+yx1uys isaalia@gmail.com0'",
  "Add-Content \"$env:USERPROFILE\\.ssh\\authorized_keys\" $key",
  "icacls \"$env:USERPROFILE\\.ssh\\authorized_keys\" /inheritance:r /grant \"${env:USERNAME}:(F)\" | Out-Null",
  "Write-Host \"SSH ready. Test from JARVIS: ssh $env:USERNAME@100.77.186.86\"",
].join("\r\n");

export async function GET() {
  return new NextResponse(SCRIPT, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
    },
  });
}
