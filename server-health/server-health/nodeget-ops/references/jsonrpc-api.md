# NodeGet JSON-RPC API 参考

## 端点
- HTTP POST: `https://statapi.yourdomain.com/`
- WebSocket: `wss://statapi.yourdomain.com/`

## Token 格式

⚠️ **API 认证 token 必须是 `key:secret` 格式**（super_token:agent_token），不能只用 super_token。

```bash
# ❌ 错误
"token": "iePL8J9iJQEr1xoG"

# ✅ 正确
"token": "iePL8J9iJQEr1xoG:106FlaZyBHYKmRwkoVeFncqmZxdoVNZZ"
```

Agent config.toml 里的 token 也是这个格式。如果格式不对会报：
```
Parse error: Failed to parse token: Invalid token format: must be 'key:secret' or 'username|password'
```

## 🔴 获取真实可用 Token 的正确方法

**从服务器上的 agent config 读取，不要从 dashboard 获取。** dashboard 显示的 token 可能已过期或格式不对，但服务器上 `/root/.config/nodeget-agent/config.toml` 里的是当前实际生效的。

```bash
# SSH 登录服务器，读取 agent 配置中的 token
ssh -p <port> root@<server_ip> "cat /root/.config/nodeget-agent/config.toml | grep token"
# 输出格式: token = "key:secret"

# 验证 token 是否可用（必须能返回 uuids 列表才说明有效）
curl -s -X POST https://statapi.yourdomain.com/ \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"nodeget-server_list_all_agent_uuid","params":{"token":"key:secret"},"id":1}'

# 返回 {"result":{"uuids":[...]}} 即有效
# 返回 {"error":{"code":102,"message":"Permission denied: Invalid credentials"}} 即失效
```

**注意区分两个不同的配置文件：**
- `/etc/nodeget-agent.conf` — 旧机器或示例配置，token 可能已失效
- `/root/.config/nodeget-agent/config.toml` — 当前实际运行使用的配置，token 有效

本项目中 56idc 服务器 token 路径：`/root/.config/nodeget-agent/config.toml`

⚠️ **服务器上有两个 config 文件，别搞混：**
- `/etc/nodeget-agent.conf` — 旧/示例配置，token 可能已失效
- `/root/.config/nodeget-agent/config.toml` — 当前实际运行使用的配置，token 有效

## 已知方法

### nodeget-server_list_all_agent_uuid
列出所有已连接的 Agent UUID。

```json
{"jsonrpc":"2.0","method":"nodeget-server_list_all_agent_uuid","params":{"token":"SUPER:AGENT"},"id":1}
```

响应：
```json
{"jsonrpc":"2.0","id":1,"result":{"uuids":["uuid1","uuid2"]}}
```

### agent_static_data_multi_last_query
批量查询 Agent 静态数据（系统信息等）。

```json
{"jsonrpc":"2.0","method":"agent_static_data_multi_last_query","params":{"token":"SUPER:AGENT","uuids":["uuid1"],"fields":["cpu","system"]},"id":1}
```

### agent_dynamic_summary_multi_last_query
批量查询 Agent 动态摘要（CPU/内存/磁盘/网络实时数据）。

```json
{"jsonrpc":"2.0","method":"agent_dynamic_summary_multi_last_query","params":{"token":"SUPER:AGENT","uuids":["uuid1"],"fields":["cpu_usage","used_memory","total_memory"]},"id":1}
```

### kv_list_all_namespace
列出所有 KV 命名空间（包含 agent UUID 和系统 namespace）。

```json
{"jsonrpc":"2.0","method":"kv_list_all_namespace","params":{"token":"SUPER:AGENT"},"id":1}
```

响应：
```json
{"jsonrpc":"2.0","id":1,"result":["07cbe62c-...","global","extension-information","script_snippet"]}
```

### kv_get_multi_value
批量读取 KV 存储。

```json
{"jsonrpc":"2.0","method":"kv_get_multi_value","params":{"token":"SUPER:AGENT","namespace_key":[{"namespace":"AGENT_UUID","key":"metadata_name"}]},"id":1}
```

### kv_set_value
设置 KV 值（用于设置 StatusShow 显示名称等元数据）。

```json
{"jsonrpc":"2.0","method":"kv_set_value","params":{"token":"SUPER:AGENT","namespace":"AGENT_UUID","key":"metadata_name","value":"自定义名称"},"id":1}
```

响应（成功）：
```json
{"jsonrpc":"2.0","id":1,"result":{"success":true}}
```

响应（namespace 不存在）：
```json
{"jsonrpc":"2.0","id":1,"error":{"code":103,"message":"Database error: Namespace 'xxx' not found"}}
```

**⚠️ Namespace 不存在的处理：** agent 必须先连接并上报 static data 才会创建 namespace。如果报 namespace not found，重启 agent 等待连接后再试。

## StatusShow 用到的 KV 键

StatusShow 从 KV 读取节点元数据，namespace 是 agent UUID：

| Key | 类型 | 说明 |
|-----|------|------|
| `metadata_name` | string | 节点显示名称 |
| `metadata_region` | string | 地区代码（如 US、JP） |
| `metadata_tags` | string[] | 标签数组 |
| `metadata_hidden` | boolean | 是否隐藏 |
| `metadata_virtualization` | string | 虚拟化类型 |
| `metadata_latitude` | number | 纬度 |
| `metadata_longitude` | number | 经度 |

## 错误码
- `-32601`: Method not found（方法名拼写错误）
- `-32602`: Invalid params（参数格式错误）
- `101`: Token 格式错误
- `103`: Database error（namespace 不存在等）

## 验证命令
```bash
# 检查 Server 是否在线
curl -s https://statapi.yourdomain.com/ | head -5

# 列出 Agent
curl -s -X POST https://statapi.yourdomain.com/ \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"nodeget-server_list_all_agent_uuid","params":{"token":"SUPER:AGENT"},"id":1}'

# 列出 KV namespace
curl -s -X POST https://statapi.yourdomain.com/ \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"kv_list_all_namespace","params":{"token":"SUPER:AGENT"},"id":1}'
```
