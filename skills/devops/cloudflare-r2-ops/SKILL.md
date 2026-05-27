---
name: cloudflare-r2-ops
description: Cloudflare R2 存储桶全栈操作 — rclone/AWS CLI 配置、文件上传列出删除、预签名 URL 生成、批量迁移。触发："R2"、"r2 上传"、"img.<用户域名>"、"存储桶"、"rclone R2"。
---

# Cloudflare R2 存储桶运维

## 适用场景

- 向 `img.<用户域名>` (R2 桶) 上传/管理文件
- 列出桶内文件、删除旧文件
- 批量上传目录
- 生成临时访问链接（预签名 URL）
- 在 VPS 间同步 R2 数据

## 前置准备

### 1. 安装 rclone（推荐，功能最全）

```bash
# Debian/Ubuntu
sudo apt install rclone

# Alpine
sudo apk add rclone
```

### 2. 获取 R2 API 凭证

在 Cloudflare Dashboard → R2 → 右侧 "管理 R2 API 令牌" → 创建令牌：

- 权限：**读+写**（至少 Object Read + Object Write）
- 指定到具体桶（比全账户令牌更安全）
- 保存好 `Access Key ID` 和 `Secret Access Key`

### 3. 配置 rclone

```bash
rclone config
```

交互流程：
1. `n` (新建 remote)
2. 命名：`r2` （或其他名字）
3. 选 `4` (Amazon S3 Compliant Storage Provider)
4. 选 `2` (Cloudflare R2)
5. Access Key ID → 粘贴
6. Secret Access Key → 粘贴
7. Region 留空回车
8. Endpoint → `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`
   - ACCOUNT_ID 在 Cloudflare Dashboard 右侧 "帐户 ID" 可查
9. Location constraint 留空
10. ACL 留空
11. Server-side encryption 留空
12. `y` 确认，`q` 退出

### 4. 配置 AWS CLI（备选方案）

```bash
pip install awscli
aws configure
# AWS Access Key ID → 粘贴
# AWS Secret Access Key → 粘贴
# Default region name → auto
# Default output format → json

# 然后添加 endpoint
aws configure set default.s3.endpoint_url https://<ACCOUNT_ID>.r2.cloudflarestorage.com
```

## 常用操作

### 列出桶内文件

```bash
# 用 rclone
rclone ls r2:<bucket-name>
rclone tree r2:<bucket-name>     # 树形结构

# 用 AWS CLI
aws s3 ls s3://<bucket-name>/ --endpoint-url https://<ACCOUNT_ID>.r2.cloudflarestorage.com
```

### 上传文件

```bash
# 单个文件
rclone copy /path/to/file.jpg r2:<bucket-name>/path/in/bucket/

# 整个目录递归上传
rclone copy /local/dir/ r2:<bucket-name>/remote/dir/ --progress -v

# 上传并设置 Content-Type（对 WebP 必要）
rclone copy file.webp r2:<bucket-name>/ --s3-content-type "image/webp"

# AWS CLI 上传
aws s3 cp file.webp s3://<bucket-name>/ --content-type "image/webp"
```

### 下载文件

```bash
rclone copy r2:<bucket-name>/remote/file.jpg /local/path/
rclone sync r2:<bucket-name>/ /local/dir/   # 完整同步
```

### 删除文件

```bash
# 删除单个
rclone delete r2:<bucket-name>/old-file.jpg

# 删除目录（清空）
rclone purge r2:<bucket-name>/some-dir/

# 清空整个桶（谨慎！）
rclone delete r2:<bucket-name>/
```

### 生成预签名 URL（临时公开访问）

使用 AWS CLI：

```bash
# 生成 1 小时有效的下载链接
aws s3 presign s3://<bucket-name>/file.webp --expires-in 3600

# 生成上传链接（允许客户端直传）
aws s3 presign s3://<bucket-name>/uploads/ --expires-in 3600 --method PUT
```

### 批量迁移/同步

```bash
# 从一个桶到另一个
rclone sync r2:source-bucket/ r2:dest-bucket/ --progress

# 从 VPS 本地到 R2（增量同步，只传变化文件）
rclone sync /data/images/ r2:<bucket-name>/images/ --progress --checksum
```

### 设置公开访问

若桶需要可公开访问的文件，在 R2 Dashboard → 桶 → 设置 → 打开 "Public Access"，
然后绑定自定义域名（如 `img.<用户域名>`）。

### 检查桶用量

```bash
# rclone 统计
rclone size r2:<bucket-name>
```

## 踩坑记录

1. **Endpoint 必须填对** — 格式 `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`，不是 `r2.cloudflare.com`
2. **Content-Type 问题** — WebP 文件如果不设 Content-Type，浏览器可能不渲染。加 `--s3-content-type "image/webp"` 或 `--content-type "image/webp"`
3. **预签名 URL 跨域** — 如果前端用 pre-signed URL 上传，需要在 R2 桶设置 CORS 策略
4. **rclone 同步不删文件** — `rclone copy` 只添加不删除。要镜像删除用 `rclone sync`。永远先用 `--dry-run` 试跑
5. **中文文件名** — 可能乱码。建议用英文/数字命名或 URL-encode
6. **大文件上传超时** — rclone 会自动分片上传，但 `--timeout` 太低会断。加 `--timeout 60m`

## 验证步骤

```bash
# 1. 列出桶
rclone ls r2:<bucket-name>/ | head -5

# 2. 上传测试文件
echo "test" > /tmp/r2-test.txt
rclone copy /tmp/r2-test.txt r2:<bucket-name>/test.txt

# 3. 确认存在
rclone ls r2:<bucket-name>/test.txt

# 4. 访问（公开桶）
curl -I https://<your-domain>/test.txt

# 5. 清理测试文件
rclone delete r2:<bucket-name>/test.txt
```
