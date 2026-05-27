# Komari SSO 绑定错误排查

## 错误现象

点击 "Login with Github" 后返回：
```json
{"message":"please log in and bind your external account first.","status":"error"}
```

## 根本原因

Komari 的 SSO 实现采用 **两步绑定机制**：
1. **第一步**：必须先用本地账号（用户名 + 密码）登录到 Komari 后台
2. **第二步**：在 Account 页面点击 "Bind External Account" 绑定 GitHub
3. **第三步**：绑定成功后，才可用 GitHub 直接登录

这是 Komari 的安全设计，**不是配置错误**。

## 排查步骤

### 1. 确认 GitHub OAuth 配置

访问 **Sign-On** 页面，检查：
- ✅ Single Sign-On 已启用（switch 打开）
- ✅ Provider 选择 `github`
- ✅ GitHub Client ID 已填写
- ✅ GitHub Client Secret 已填写
- ✅ Callback URL 显示：`https://stat.357561.xyz/api/oauth_callback`

### 2. 确认 GitHub OAuth App 配置

在 GitHub Developer Settings 中：
- **Homepage URL**: `https://stat.357561.xyz`
- **Authorization callback URL**: `https://stat.357561.xyz/api/oauth_callback`
- 两者必须完全一致（包括协议 `https://`）

### 3. 执行绑定流程

1. 用本地账号登录（默认 `admin` 或自定义用户名）
2. 点击左侧 **Account** 菜单
3. 滚动到 **Single Sign-On** 部分
4. 点击 **Bind External Account** 按钮
5. 在 GitHub 授权页面点击 "Authorize"
6. 返回 Komari，检查显示 `External Account: Bound`

### 4. 验证绑定成功

**Account 页面显示**：
- 绑定前：`External Account: Unbound`
- 绑定后：`External Account: Bound` + 显示 GitHub 用户名

## 常见问题

### Q: 为什么不能直接用 GitHub 登录？

A: Komari 的 SSO 实现要求先绑定。这是为了防止账号劫持和确保本地账号存在。

### Q: 绑定后还能用本地密码登录吗？

A: 可以。绑定后两种登录方式并存：
- 本地账号 + 密码
- GitHub 一键登录

### Q: 如何解绑？

A: Account 页面目前没有解绑入口。如需解绑，需手动编辑数据库：
```sql
UPDATE users SET external_provider = NULL, external_uid = NULL WHERE username = 'xxx';
```

## 参考

- Komari 官方文档：https://komari.dev/docs
- GitHub OAuth 配置：https://docs.github.com/en/developers/apps/building-oauth-apps/creating-an-oauth-app
- 本案例：2026-05-04 会话，用户 `woioeow` 在 56idc 服务器遇到此问题
