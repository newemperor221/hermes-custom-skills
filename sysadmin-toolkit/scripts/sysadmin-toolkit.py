#!/usr/bin/env python3
"""
sysadmin-toolkit: 常用运维操作工具
用法:
  python3 sysadmin-toolkit.py disk-analysis [--servers "洛杉矶1"]
  python3 sysadmin-toolkit.py service-status ssh [--servers "洛杉矶1"]
  python3 sysadmin-toolkit.py service-restart nginx [--servers "洛杉矶1"]
  python3 sysadmin-toolkit.py user-list
  python3 sysadmin-toolkit.py install fail2ban
"""
import paramiko
import json
import argparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

SERVERS = {
    "洛杉矶1": {"ip": "155.94.180.55", "port": 58193, "user": "root", "pass": "Rjmc22LynqWt"},
    "纽约":    {"ip": "172.245.159.219", "port": 27391, "user": "root", "pass": "GPxrUp5B561WWt7er6"},
    "洛杉矶2": {"ip": "23.95.201.153", "port": 47283, "user": "root", "pass": "4561834"},
    "堪萨斯":  {"ip": "45.39.12.227", "port": 63841, "user": "root", "pass": "4561834"},
    "亚特兰大": {"ip": "23.95.218.144", "port": 53621, "user": "woioeow", "pass": "4561834"},
}


def ssh_cmd(ip, port, user, pw, cmd):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, port=port, username=user, password=pw, timeout=15, banner_timeout=15)
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        out = stdout.read().decode('utf-8', errors='ignore')
        err = stderr.read().decode('utf-8', errors='ignore')
        client.close()
        return out.strip(), err.strip(), 0
    except Exception as e:
        return "", str(e), 1


def action_disk_analysis(name, info):
    ip, port, user, pw = info["ip"], info["port"], info["user"], info["pass"]
    cmd = (
        "echo '<<DF>>'; df -h | grep -v tmpfs | grep -v devtmpfs; "
        "echo '<<TOP10>>'; du -shx /* 2>/dev/null | sort -rh | head -10; "
        "echo '<<LARGE>>'; find / -type f -size +100M 2>/dev/null | xargs ls -lh 2>/dev/null | sort -k5 -rh | head -10"
    )
    out, err, _ = ssh_cmd(ip, port, user, pw, cmd)

    def grab(key, next_key=None):
        idx = out.find(key)
        if idx == -1:
            return ""
        start = idx + len(key)
        end_idx = out.find(next_key, start) if next_key else -1
        return out[start:end_idx].strip() if end_idx == -1 else out[start:end_idx].strip()

    df_out = grab('<<DF>>', '<<TOP10>>')

    disks = []
    for line in df_out.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('Filesystem'):
            continue
        parts = line.split()
        if len(parts) >= 6:
            try:
                disks.append({
                    "mount": parts[5],
                    "size": parts[1],
                    "used": parts[2],
                    "use_percent": int(parts[4].replace('%', '')),
                })
            except (ValueError, IndexError):
                pass

    top10 = grab('<<TOP10>>', '<<LARGE>>')
    top10_list = [l.strip() for l in top10.split('\n') if l.strip()]

    return {"name": name, "status": "online", "disk": disks, "top10": top10_list}


def action_service(name, info, service, svc_action):
    ip, port, user, pw = info["ip"], info["port"], info["user"], info["pass"]
    action_map = {
        "status": f"systemctl is-active {service}",
        "restart": f"systemctl restart {service} && echo OK",
        "stop": f"systemctl stop {service} && echo OK",
        "start": f"systemctl start {service} && echo OK",
        "enable": f"systemctl enable {service} && echo OK",
        "reload": f"systemctl reload {service} && echo OK",
    }
    cmd = action_map.get(svc_action, f"systemctl status {service}")
    out, err, rc = ssh_cmd(ip, port, user, pw, cmd)
    status = "active" if "active" in out.lower() or out.endswith("OK") else out.strip() or "inactive"
    return {"name": name, "service": service, "action": svc_action, "status": status, "output": out[:200]}


def action_user_list(name, info):
    ip, port, user, pw = info["ip"], info["port"], info["user"], info["pass"]
    cmd = "cat /etc/passwd | grep -v 'nologin\\|false' | awk -F: '{print $1,\"UID:\"$3,\"GID:\"$4,\"Shell:\"$7}' | column -t"
    out, err, _ = ssh_cmd(ip, port, user, pw, cmd)
    users = [l.strip() for l in out.strip().split('\n') if l.strip()]
    return {"name": name, "status": "online", "users": users}


def action_install(name, info, package):
    ip, port, user, pw = info["ip"], info["port"], info["user"], info["pass"]
    cmd = f"DEBIAN_FRONTEND=noninteractive apt-get install -y {package} 2>&1 | tail -5"
    out, err, rc = ssh_cmd(ip, port, user, pw, cmd)
    if rc == 0:
        return {"name": name, "package": package, "status": "installed"}
    else:
        return {"name": name, "package": package, "status": "failed", "error": err[-200:]}


def action_firewall_status(name, info):
    ip, port, user, pw = info["ip"], info["port"], info["user"], info["pass"]
    out, err, _ = ssh_cmd(ip, port, user, pw, "ufw status verbose")
    return {"name": name, "status": "online", "output": out}


def run_on_targets(func, targets, parallel=True):
    results = []
    if parallel:
        with ThreadPoolExecutor(max_workers=len(targets)) as executor:
            futures = {executor.submit(func, name, info): name for name, info in targets.items()}
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    name = futures[future]
                    results.append({"name": name, "status": "error", "error": str(e)})
    else:
        for name, info in targets.items():
            try:
                results.append(func(name, info))
            except Exception as e:
                results.append({"name": name, "status": "error", "error": str(e)})
    return results


def print_report(results, action, json_output=False):
    if json_output:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    print(f"\n{'=' * 60}")
    for r in results:
        status = r.get("status", "unknown")
        if status == "offline" or status == "error":
            print(f"\n❌ {r['name']}: {r.get('error', 'offline')}")
            continue

        if action == "disk-analysis":
            print(f"\n🔵 {r['name']}")
            for d in r.get("disk", []):
                w = "⚠️ " if d["use_percent"] > 85 else "✅ "
                print(f"  {w}{d['mount']}: {d['use_percent']}% ({d['used']}/{d['size']})")
            if r.get("top10"):
                print(f"  📁 Top 目录:")
                for line in r["top10"][:5]:
                    print(f"    {line}")

        elif action.startswith("service-"):
            svc = r.get("service", "")
            act = r.get("action", "")
            st = r.get("status", "")
            w = "✅" if st == "active" else "⚠️ "
            print(f"  {w} {r['name']} / {svc} [{act}]: {st}")

        elif action == "user-list":
            print(f"\n🔵 {r['name']}: {len(r.get('users', []))} 用户")
            for u in r.get("users", [])[:8]:
                print(f"  {u}")

        elif action == "install":
            pkg = r.get("package", "")
            st = r.get("status", "")
            w = "✅" if st == "installed" else "⚠️ "
            print(f"  {w} {r['name']}: {pkg} → {st}")

        elif action == "firewall":
            print(f"\n🔵 {r['name']}")
            for line in r.get("output", "").split('\n')[:10]:
                if line.strip():
                    print(f"  {line}")


def main():
    parser = argparse.ArgumentParser(description="Sysadmin Toolkit", prog="sysadmin-toolkit")
    parser.add_argument("action", choices=[
        "disk-analysis", "user-list", "system-update",
        "service-status", "service-restart", "service-stop", "service-start", "service-enable",
        "install", "firewall-status",
    ])
    parser.add_argument("target", nargs="?", default=None, help="服务名或包名")
    parser.add_argument("--servers", "-s", default="all")
    parser.add_argument("--package", help="包名（配合 install）")
    parser.add_argument("--json", "-j", action="store_true")
    args = parser.parse_args()

    # 从 action 提服务名（如 service-restart nginx → service, nginx）
    a = args.action
    targets = {k: v for k, v in SERVERS.items()
               if k in [s.strip() for s in args.servers.split(",")]} if args.servers != "all" else SERVERS

    # 解析
    if a.startswith("service-"):
        svc_action = a.replace("service-", "")
        service = args.target or args.package
        if not service:
            print("错误: 需要指定服务名 (位置参数或 --package)")
            return
        print(f"🔧 服务操作: {service} / {svc_action}")
        results = run_on_targets(
            lambda n, i: action_service(n, i, service, svc_action), targets
        )
        print_report(results, a, args.json)

    elif a == "disk-analysis":
        print("📊 磁盘分析...")
        results = run_on_targets(action_disk_analysis, targets)
        print_report(results, a, args.json)

    elif a == "user-list":
        print("👥 用户列表...")
        results = run_on_targets(action_user_list, targets)
        print_report(results, a, args.json)

    elif a == "install":
        package = args.package or input("包名: ").strip() if not args.package else args.package
        if not package:
            print("错误: 需要 --package")
            return
        print(f"📦 安装: {package}")
        results = run_on_targets(
            lambda n, i: action_install(n, i, package), targets
        )
        print_report(results, a, args.json)

    elif a == "firewall-status":
        print("🔥 防火墙状态...")
        results = run_on_targets(action_firewall_status, targets)
        print_report(results, a, args.json)

    elif a == "system-update":
        print("⬆️ 系统更新...")
        results = run_on_targets(
            lambda n, i: action_install(n, i, "systemd"), targets
        )
        print_report(results, a, args.json)


if __name__ == "__main__":
    main()
