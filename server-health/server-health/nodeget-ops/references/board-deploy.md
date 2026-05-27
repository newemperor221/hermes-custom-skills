# Board 管理面板 Cloudflare Pages 部署

## 与 StatusShow 的区别

| | StatusShow | Board |
|---|---|---|
| 环境变量 | `SITE_1` 等 | `VITE_BACKEND_WS` + `VITE_BACKEND_TOKEN` |
| Node 版本 | 无要求（默认 18 即可） | `^20.19.0 \|\| >=22.12.0` |
| 后端配置时机 | 仅 build 时 | build 时 + 运行时 UI 都可 |
| 官方仓库 | NodeSeekDev/NodeGet-StatusShow | NodeSeekDev/NodeGet-board |

## Cloudflare Pages 构建设置

- **框架预设**: 无
- **构建命令**: `npm run build`
- **输出目录**: `dist`
- **环境变量**:
  - `NODE_VERSION` = `20`（⚠️ 必须，默认 18 不满足 engines 要求）
  - `VITE_BACKEND_WS` / `VITE_BACKEND_TOKEN` 对 Board 无效，不用设

## Fork 官方仓库

```bash
gh repo fork NodeSeekDev/NodeGet-board --clone --remote-name origin
cd NodeGet-board
git push -u origin main
```

## ⚠️ Board 不读构建时环境变量

与 StatusShow 不同，Board 不使用 `VITE_BACKEND_WS` / `VITE_BACKEND_TOKEN` 连接后端。
部署后必须在 UI 里手动添加主控：

1. 打开 `dash.yourdomain.com`
2. 弹出 "Add Server" 模态框
3. 填写：
   - **Name**: 随意，如 `主控`
   - **WSS URL**: `wss://statapi.yourdomain.com`
   - **Token**: 超级 token（如 `iePL8J9iJQEr1xoG`），不是 agent 的 `super:agent` 格式
4. 点 **+ Add Server**

Token 存在浏览器 localStorage，清除浏览器数据后需重新添加。

## ⚠️ 服务器已添加但数据不刷新（localStorage 为空）

**症状:** Board 右上角没有"Add Server"提示（说明已添加过），但数据全是空白的，数据刷新不出来。

**排查:** 浏览器 Console 输入 `localStorage.getItem('nodeget-servers')` 返回 `empty` → 服务器信息没存进浏览器。

**原因:** localStorage 是空的，说明之前虽然添加过，但被清除或从未成功保存。

**解决:** 手动重新 Add Server：
1. 地址栏敲 `#/node-manage` 手动触发 Add Server 弹窗
2. 填入 WSS URL + Token（从 `/root/.config/nodeget-agent/config.toml` 获取 agent 的 `ws_url` 和 `token`）
3. 点 Add Server 后应立即看到节点状态变为 Active

⚠️ **Board 的服务器配置存在浏览器 localStorage，不是服务端。** 不同浏览器/设备需要各自添加。

## Token 格式说明

- **超级 token**（Board 用）: `iePL8J9iJQEr1xoG`（单段）
- **Agent token**（agent 配置用）: `iePL8J9iJQEr1xoG:106FlaZyBHYKmRwkoVeFncqmZxdoVNZZ`（`super_token:agent_token` 两段）
- Board 只需超级 token 部分，不要填完整的 agent token

## package.json engines 要求

```json
"engines": {
  "node": "^20.19.0 || >=22.12.0"
}
```

Cloudflare Pages 默认 Node 18，不指定 `NODE_VERSION=20` 会构建失败。
StatusShow 无此限制。
