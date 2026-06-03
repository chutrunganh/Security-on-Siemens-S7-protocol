#!/bin/bash
echo "=== Reachability ==="
for ip in 172.16.16.145 172.16.16.44 172.16.16.136 172.16.16.1; do
  if ping -c1 -W1 "$ip" >/dev/null 2>&1; then echo "UP   $ip"; else echo "DOWN $ip"; fi
done

echo "=== Port 102 scan ==="
for ip in 172.16.16.145 172.16.16.44 172.16.16.136; do
  if nc -z -w2 "$ip" 102 2>/dev/null; then echo "OPEN $ip:102"; else echo "CLOSED $ip:102"; fi
done

echo "=== Tools ==="
command -v nmap || echo "NO nmap"
command -v python3 || echo "NO python3"
python3 -c "import snap7" 2>/dev/null && echo "snap7 OK" || echo "NO snap7"
ls /usr/share/nmap/scripts/s7-info.nse 2>/dev/null || echo "NO s7-info.nse"
