# Komari 用户名修改导致无法登录的修复

## 问题现象

在 Komari 后台修改 admin 用户名后，无法登录。

## 根本原因

Komari 后端使用用户名 + 密码双重验证，**用户名是登录凭证的一部分**，不是显示名称。修改后前端仍用旧用户名提交，后端验证失败。

## 修复步骤

### 1. 检查当前用户名

```bash
ssh -p 52137 root@<洛杉矶2_IP> "sqlite3 /opt/komari/data/komari.db 'SELECT username FROM users;'"
```

### 2. 获取用户 UUID（用于精准定位）

```bash
# 如果用户名是 woioeow
UUID=$(ssh -p 52137 root@<洛杉矶2_IP> "sqlite3 /opt/komari/data/komari.db \"SELECT uuid FROM users WHERE username='woioeow';\"")
echo $UUID
```

### 3. 改回 admin

```bash
# 注意：WHERE 条件用 uuid 而不是 id（users 表没有 id 字段，只有 uuid 主键）
ssh -p 52137 root@<洛杉矶2_IP> "sqlite3 /opt/komari/data/komari.db \"UPDATE users SET username='admin' WHERE uuid='$UUID';\""
```

### 4. 重置密码（如果密码也改了）

Komari 用 bcrypt 加密密码，需要生成新的哈希值。

#### 方法 A：用 Python 生成（需先安装 bcrypt）

```bash
# 安装 bcrypt
ssh -p 52137 root@<洛杉矶2_IP> "apt-get update -qq && apt-get install -y python3-pip -qq && pip3 install bcrypt -q"

# 生成哈希
ssh -p 52137 root@<洛杉矶2_IP> "python3 -c \"import bcrypt; print(bcrypt.hashpw(b'Komari@2026', bcrypt.gensalt()).decode())\""
```

#### 方法 B：用临时脚本（推荐，避免 pip 依赖）

```bash
# 1. 在本地生成脚本
cat > /tmp/reset_komari.py << 'EOF'
import bcrypt, sqlite3
hashed = bcrypt.hashpw(b'Komari@2026', bcrypt.gensalt()).decode()
conn = sqlite3.connect('/opt/komari/data/komari.db')
c = conn.cursor()
c.execute("UPDATE users SET passwd=? WHERE username=?", (hashed, 'admin'))
conn.commit()
print(f"Updated with hash: {hashed[:30]}...")
conn.close()
EOF

# 2. 上传到服务器
scp -P 52137 /tmp/reset_komari.py root@<洛杉矶2_IP>:/tmp/reset_komari.py

# 3. 执行
ssh -p 52137 root@<洛杉矶2_IP> "python3 /tmp/reset_komari.py"
```

### 5. 验证修复

```bash
# 检查用户名和哈希前缀
ssh -p 52137 root@<洛杉矶2_IP> "sqlite3 /opt/komari/data/komari.db \"SELECT username, substr(passwd,1,30) FROM users;\""
```

## 如果用户名改成了 woioeow 且想保留

1. 直接用 `woioeow` + `Komari@2026` 登录
2. 如果密码也改了，用上面方法重置密码
3. **不要再次修改用户名**（Komari 没有用户名修改的 UI 入口，只能改数据库）

## 预防措施

- Komari admin 用户名默认是 `admin`，**不要修改**
- 如果必须改，先用 `chpasswd` 重置密码，确保新用户名能登录后再改其他配置
- 用户名修改后，所有 Agent 的认证配置不变（只认用户名 + 密码）
- 修改前备份数据库：`cp /opt/komari/data/komari.db /opt/komari/data/komari.db.bak`

## 数据库结构说明

```sql
CREATE TABLE `users` (
  `uuid` varchar(36),
  `username` varchar(50) NOT NULL,
  `passwd` varchar(255) NOT NULL,
  `sso_type` varchar(20),
  `sso_id` varchar(100),
  `two_factor` varchar(255),
  `created_at` datetime,
  `updated_at` datetime,
  PRIMARY KEY (`uuid`),
  CONSTRAINT `uni_users_username` UNIQUE (`username`)
);
```

- `uuid`：主键，UUID 格式（如 `75527bb3-abb9-45e8-af2b-fcf517611315`）
- `username`：登录用户名，唯一约束
- `passwd`：bcrypt 加密的密码哈希，格式 `$2b$12$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## 相关命令

```bash
# 查看用户表
sqlite3 /opt/komari/data/komari.db "SELECT * FROM users;"

# 备份数据库
cp /opt/komari/data/komari.db /opt/komari/data/komari.db.bak

# 重置 admin 密码（官方命令）
cd /opt/komari && ./komari chpasswd -p 'Komari@2026'
```
