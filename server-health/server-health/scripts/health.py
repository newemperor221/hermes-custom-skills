#!/usr/bin/env python3
"""
server-health: 跨服务器健康检查工具 (paramiko版)
用法: python3 health.py [--servers "洛杉矶1,纽约"] [--quick] [--deep] [--json]
"""
import paramiko
import json
import argparse
import re

SERVERS = {
    "洛杉矶1": {"ip": "155.94.180.55", "port": 58193, "user": "root", "pass": "Rjmc22LynqWt"},
    "纽约":    {"ip": "172.245.159.219", "port": 27391, "user": "root", "pass": "GPxrUp5B561WWt7er6"},
    "洛杉矶2": {"ip": "23.95.201.153", "port": 47283, "user": "root", "pass": "4561834"},
    "堪萨斯":  {"ip": "45.39.12.227", "port": 63841, "user": "root", "pass": "4561834"},
    "亚特兰大": {"ip": "23.95.218.144", "port": 53621, "user": "woioeow", "pass": "4561834"},
}


def ssh_batch(ip, port, user, pw, cmd):
    """一条 SSH 连接执行所有命令，避免频繁建连被限速"""
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, port=port, username=user, password=pw, timeout=15, banner_timeout=15)
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        out = stdout.read().decode('utf-8', errors='ignore')
        client.close()
        return out.strip(), 0
    except Exception as e:
        return "", str(e)


def parse_cpu(raw):
    """从 top -bn1 输出解析 CPU 使用率"""
    for line in raw.split('\n'):
        if '%Cpu(s)' in line or 'Cpu(s):' in line:
            line = line.strip()
            m = re.search(r'([\d.]+)\s+id[, ]', line)
            if m:
                idle = float(m.group(1))
                if idle <= 100:
                    return round(100 - idle, 1)
            m2 = re.search(r'([\d.]+)%id', line)
            if m2:
                idle = float(m2.group(1))
                return round(100 - idle, 1)
    return None


def check_all(name, info, quick=False):
    ip, port, user, pw = info["ip"], info["port"], info["user"], info["pass"]
    print(f"  {name}...", end=" ", flush=True)
    try:
        # ---------- 打包所有命令，一次 SSH 连接 ----------
        # 用标记分割输出，不用管道（top free df 等命令自己输出天然分隔）
        if quick:
            cmd = (
                "echo '<<CPU>>'; top -bn1 | head -8; "
                "echo '<<MEM>>'; free -m; "
                "echo '<<DISK>>'; df -h | grep -v tmpfs | grep -v devtmpfs; "
                "echo '<<UP>>'; uptime -s"
            )
        else:
            cmd = (
                "echo '<<CPU>>'; top -bn1 | head -8; "
                "echo '<<MEM>>'; free -m; "
                "echo '<<DISK>>'; df -h | grep -v tmpfs | grep -v devtmpfs; "
                "echo '<<UP>>'; uptime -s; "
                "echo '<<SSHD>>'; systemctl is-active ssh; "
                "echo '<<FB>>'; systemctl is-active fail2ban; "
                "echo '<<SEC>>'; awk '/^PasswordAuthentication|^PermitRootLogin|^Port/ {print}' /etc/ssh/sshd_config; "
                "echo '<<UFW>>'; ufw status | head -3"
            )

        out, err = ssh_batch(ip, port, user, pw, cmd)

        def grab(key, next_key=None):
            idx = out.find(key)
            if idx == -1:
                return ""
            start = idx + len(key)
            if next_key:
                end_idx = out.find(next_key, start)
                if end_idx == -1:
                    return out[start:].strip()
                return out[start:end_idx].strip()
            return out[start:].strip()

        cpu_raw = grab('<<CPU>>', '<<MEM>>')
        mem_raw = grab('<<MEM>>', '<<DISK>>')
        disk_raw = grab('<<DISK>>', '<<UP>>')
        up_raw = grab('<<UP>>', '<<SSHD>>') if not quick else grab('<<UP>>')
        sshd_out = grab('<<SSHD>>', '<<FB>>') if not quick else "active"
        fb_out = grab('<<FB>>', '<<SEC>>') if not quick else "unknown"
        sec_out = grab('<<SEC>>', '<<UFW>>') if not quick else ""
        ufw_out = grab('<<UFW>>') if not quick else ""

        # CPU
        cpu_pct = parse_cpu(cpu_raw)
        load_m = re.search(r'load average:\s*([\d.,\s]+)', cpu_raw)
        load = load_m.group(1).strip().split(',')[0] if load_m else "N/A"

        # 内存
        mem = {}
        lines = mem_raw.strip().split('\n')
        if len(lines) >= 2:
            parts = lines[1].split()
            if len(parts) >= 3:
                try:
                    total, used = int(parts[1]), int(parts[2])
                    mem = {"total_mb": total, "used_mb": used, "usage_percent": round(used/total*100, 1)}
                except (ValueError, IndexError):
                    pass

        # 磁盘
        disk = []
        for line in disk_raw.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('Filesystem'):
                continue
            parts = line.split()
            if len(parts) >= 6:
                try:
                    mount = parts[5] if len(parts) > 5 else parts[0]
                    usage = int(parts[4].replace('%', ''))
                    disk.append({"mount": mount, "usage_percent": usage})
                except (ValueError, IndexError):
                    pass

        # 安全配置
        security = {}
        for line in sec_out.split('\n'):
            parts = line.strip().split()
            if len(parts) >= 2:
                key, val = parts[0], parts[-1]
                if key == 'PasswordAuthentication':
                    security['ssh_password_auth'] = val
                elif key == 'PermitRootLogin':
                    security['ssh_root_login'] = val
                elif key == 'Port':
                    security['ssh_port'] = val

        result = {
            "name": name, "status": "online",
            "cpu": {"usage_percent": cpu_pct, "load": load},
            "memory": mem, "disk": disk,
            "uptime": {"boot_time": up_raw or "unknown"},
            "services": {
                "ssh": sshd_out or "unknown",
                "fail2ban": fb_out or "not installed",
            }
        }
        if not quick:
            result["security"] = security

        print("✓")
        return result

    except Exception as e:
        print(f"✗ ({e})")
        return {"name": name, "status": "offline", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Server Health Check")
    parser.add_argument("--servers", default="all")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    targets = SERVERS if args.servers == "all" else {
        k: v for k, v in SERVERS.items()
        if k in [s.strip() for s in args.servers.split(",")]
    }

    results = [check_all(name, info, quick=args.quick) for name, info in targets.items()]

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print("\n" + "=" * 60)
        print(" 服务器健康报告 ".center(60))
        print("=" * 60)
        for r in results:
            if r["status"] != "online":
                print(f"\n❌ {r['name']}: {r.get('error', 'offline')}")
                continue
            cpu = r.get("cpu", {})
            mem = r.get("memory", {})
            print(f"\n🔵 {r['name']}")
            if cpu.get("usage_percent") is not None:
                w = "⚠️ " if cpu["usage_percent"] > 80 else "✅ "
                print(f"  {w}CPU: {cpu['usage_percent']}%  负载: {cpu['load']}")
            elif cpu.get("load"):
                print(f"  ✅ 负载: {cpu['load']}")
            if mem:
                w = "⚠️ " if mem["usage_percent"] > 85 else "✅ "
                print(f"  {w}内存: {mem['used_mb']}/{mem['total_mb']} MB ({mem['usage_percent']}%)")
            for d in r.get("disk", []):
                w = "⚠️ " if d["usage_percent"] > 85 else "✅ "
                print(f"  {w}磁盘 {d['mount']}: {d['usage_percent']}%")
            for svc, st in r.get("services", {}).items():
                w = "⚠️ " if st != "active" else "✅ "
                print(f"  {w}{svc}: {st}")
            if not args.quick and "security" in r:
                sec = r["security"]
                pw_auth = sec.get("ssh_password_auth", "N/A")
                root = sec.get("ssh_root_login", "N/A")
                sport = sec.get("ssh_port", "N/A")
                fb = r.get("services", {}).get("fail2ban", "N/A")
                print(f"  {'⚠️' if pw_auth == 'yes' else '✅'} SSH密码登录: {pw_auth}")
                print(f"  {'⚠️' if root == 'yes' else '✅'} SSH root登录: {root}")
                print(f"  {'⚠️' if sport == '22' else '✅'} SSH端口: {sport}")
                print(f"  {'⚠️' if fb != 'active' else '✅'} fail2ban: {fb}")


if __name__ == "__main__":
    main()
