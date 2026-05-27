# DeepSeek 网页版反代 API

> 将 chat.deepseek.com 的免费对话反代为 OpenAI/Anthropic 兼容 API
> 更新: 2026-05-11

## 原理

```
你的客户端 → 反向代理 → chat.deepseek.com (用网页版 cookie/token)
                     ↓
                   OpenAI / Anthropic 标准 API 输出
```

需要从 chat.deepseek.com 的 LocalStorage 获取 `userToken`（登录后对话一次，F12 → Application → LocalStorage）。

---

## 项目对比

### 🥇 LLM-Red-Team/deepseek-free-api

- **语言**: Node.js
- **协议**: ✅ OpenAI 兼容
- **部署**: Docker / Vercel / Render / PM2 原生
- **多账号**: Token 拼接 `Bearer TOKEN1,TOKEN2`
- **工具调用**: ❌ 不支持
- **文件上传**: ❌ 不支持
- **管理面板**: ❌
- **Stars**: ~3.5k (最成熟)

**Docker 部署**:
```bash
docker run -it -d --init --name deepseek-free-api \
  -p 8000:8000 \
  -e TZ=Asia/Shanghai \
  vinlic/deepseek-free-api:latest
```

---

### 🏆 NIyueeE/ds-free-api

- **语言**: Rust（musl 静态编译，单二进制）
- **协议**: ✅ **OpenAI + Anthropic 双协议**
- **部署**: Docker / 单二进制
- **多账号**: ✅ 空闲最久优先轮转
- **工具调用**: ✅ 三层自修复管道（文本修复→JSON修复→模型兜底）
- **文件上传**: ✅ 支持 file/image_url 内联上传
- **管理面板**: ✅ Web面板（账号池/API Key/配置/日志/热重载）
- **自带测试账号**: ✅ 15个免费 Gmail 别名

**Docker 部署**:
```bash
docker run -d --name ds-free-api -p 22217:22217 \
  ghcr.io/niyueee/ds-free-api:latest
```

**Rust 二进制部署（推荐 Alpine）**:
```bash
# 下载 musl 静态编译版（约10MB）
wget https://github.com/NIyueeE/ds-free-api/releases/latest/download/ds-free-api-x86_64-unknown-linux-musl.tar.gz
tar xzf ds-free-api-x86_64-unknown-linux-musl.tar.gz

# 配置
cp config.example.toml config.toml

# 运行
./ds-free-api
# 或指定配置
./ds-free-api -c /path/to/config.toml
```

**管理面板**: `http://你的IP:22217/admin`（首次设置管理密码）

---

## Token 获取

1. 打开 https://chat.deepseek.com 并登录
2. 发起任意对话
3. F12 → Application → LocalStorage → 复制 `userToken` 的 value
4. 在请求中作为 `Authorization: Bearer <token>` 使用

Token 会过期，需定期重新获取。

---

## 与那个 PHP 项目配合

之前讨论的 `dirk1983/deepseek`（PHP版AI聊天）无法直接调用 DeepSeek 网页 Token。
但可以用这个反代项目做中间层：

```
PHP 前端 ← OpenAI API → ds-free-api ← 反代 → chat.deepseek.com
```

PHP 项目改 `stream.php` 中的 API 地址为 ds-free-api 地址即可。

---

## 免费 API 替代方案

不折腾反代的话，也可以直接用这些平台的免费额度：

| 平台 | 免费额度 | 接口 |
|:----|:---------|:----:|
| **硅基流动** | DeepSeek-R1 每天200次 | `api.siliconflow.cn/v1` |
| **阿里云百炼** | R1+V3各100万Token(一次性) | 百炼API |
| **火山引擎** | 注册送15元代金券 | 火山API |

---

## 部署注意事项

- ⚠️ **严禁商用**，仅供自用/学习，避免对 DeepSeek 官方造成压力
- ⚠️ Token 可能被封（降低频率，并行数=账号数/2）
- ⚠️ 逆向 API 不稳定，可能随时失效
- ✅ 优先支持 DeepSeek 官方 API（非常便宜）
