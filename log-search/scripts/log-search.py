#!/usr/bin/env python3
"""
log-search: 跨服务器日志搜索工具
用法: python3 log-search.py --keyword "error" [--servers "洛杉矶1,纽约"] [--log-path "/var/log/syslog"] [--json]
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

DEFAULT_LOG_PATHS = [
    "/var/log/syslog",
    "/var/log/auth.log",
    "/var/log/nginx/access.log",
    "/var/log/nginx/error.log",
    "/var/log/apache2/access.log",
    "/var/log/apache2/error.log",
    "/var/log/fail2ban.log",
]


def search_server(name, info, keyword, log_paths, max_lines=50):
    ip, port, user, pw = info["ip"], info["port"], info["user"], info["pass"]
    results = []
    errors = []

    # 构造 grep 命令：搜索所有日志路径，限制输出行数
    path_list = " ".join(f'"{p}"' for p in log_paths)
    # 用 bash -c 执行，这样 grep 可以并查多个文件
    cmd = f'bash -c \'grep -rn --include="*" "{keyword}" {path_list} 2>/dev/null | tail -n {max_lines}\''

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, port=port, username=user, password=pw, timeout=15, banner_timeout=15)
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        out = stdout.read().decode('utf-8', errors='ignore')
        err = stderr.read().decode('utf-8', errors='ignore')
        client.close()

        if out.strip():
            for line in out.strip().split('\n'):
                if line.strip():
                    results.append(line.strip())
        if err.strip():
            errors.append(err.strip())

        return {
            "name": name,
            "ip": ip,
            "status": "online",
            "matches": results,
            "match_count": len(results),
            "errors": errors,
        }
    except Exception as e:
        return {
            "name": name,
            "ip": ip,
            "status": "offline",
            "error": str(e),
            "matches": [],
            "match_count": 0,
        }


def main():
    parser = argparse.ArgumentParser(description="跨服务器日志搜索")
    parser.add_argument("--keyword", "-k", required=True, help="搜索关键词")
    parser.add_argument("--servers", "-s", default="all", help="目标服务器，逗号分隔")
    parser.add_argument("--log-path", "-l", action="append", default=None,
                        help="日志路径，可指定多个（默认扫描常见路径）")
    parser.add_argument("--json", "-j", action="store_true", help="输出JSON格式")
    parser.add_argument("--max-lines", "-n", type=int, default=50, help="每服务器最多返回行数")
    args = parser.parse_args()

    targets = SERVERS if args.servers == "all" else {
        k: v for k, v in SERVERS.items()
        if k in [s.strip() for s in args.servers.split(",")]
    }

    log_paths = args.log_path if args.log_path else DEFAULT_LOG_PATHS

    print(f"🔍 搜索关键词: \"{args.keyword}\"")
    print(f"📂 日志路径: {', '.join(log_paths)}")
    print(f"🎯 服务器: {', '.join(targets.keys())}")
    print()

    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(search_server, name, info, args.keyword, log_paths, args.max_lines): name
            for name, info in targets.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            print(f"  {name}...", end=" ", flush=True)
            try:
                result = future.result()
                print(f"✓ ({result['match_count']} 条匹配)")
                results.append(result)
            except Exception as e:
                print(f"✗ ({e})")
                results.append({"name": name, "status": "offline", "error": str(e), "matches": []})

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    # 人类可读输出
    total_matches = sum(r.get('match_count', 0) for r in results)
    print(f"\n{'=' * 60}")
    print(f" 搜索结果: {total_matches} 条匹配 ".center(60))
    print(f"{'=' * 60}")

    for r in results:
        if r["status"] == "offline":
            print(f"\n❌ {r['name']}: {r.get('error', 'offline')}")
            continue
        if not r["matches"]:
            print(f"\n⚪ {r['name']} ({r['ip']}): 无匹配")
            continue
        print(f"\n🔵 {r['name']} ({r['ip']}): {r['match_count']} 条匹配")
        for line in r["matches"][:args.max_lines]:
            print(f"  {line}")


if __name__ == "__main__":
    main()
