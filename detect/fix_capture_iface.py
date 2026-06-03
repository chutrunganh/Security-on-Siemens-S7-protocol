#!/usr/bin/env python3
import paramiko
import os

HOST = "172.16.16.143"
USER = "lubuntu"
PASSWORD = "lubuntu"
BASE = os.path.dirname(os.path.abspath(__file__))


def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    sftp = ssh.open_sftp()
    sftp.put(os.path.join(BASE, "add_capture_iface.py"), "/tmp/add_capture_iface.py")
    sftp.close()

    cmds = [
        "sudo cp /etc/suricata/suricata.yaml /etc/suricata/suricata.yaml.bak.before-ens33",
        "sudo python3 /tmp/add_capture_iface.py ens33",
        "grep -n 'interface:' /etc/suricata/suricata.yaml | head -8",
        "sudo suricata -T -c /etc/suricata/suricata.yaml 2>&1 | tail -5",
        "sudo systemctl restart suricata && sleep 2 && systemctl is-active suricata",
        "sudo tail -5 /var/log/suricata/suricata.log",
    ]
    for c in cmds:
        print(">>>", c)
        _, out, err = ssh.exec_command(c, get_pty=True)
        text = out.read().decode("ascii", errors="replace")
        print(text)
    ssh.close()


if __name__ == "__main__":
    main()
