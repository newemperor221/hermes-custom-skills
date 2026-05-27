---
name: GitHub Actions Self-Hosted Runner
description: 在自有服务器部署 GitHub Actions self-hosted runner，实现 push 代码后自动触发部署。包含 gh 安装、runner 注册、SSH key 配置、workflow 踩坑。
---

# GitHub Actions Self-Hosted Runner 部署

## 触发场景
在自有服务器上部署 GitHub Actions self-hosted runner，push 代码后自动触发部署。

## 踩坑记录

### 1. runner 无 SSH 私钥
**问题**：`ssh user@server` 报 `Permission denied (publickey)`
**原因**：runner 部署在服务器上但没有 SSH 私钥
**解决**：
1. 把私钥存为 GitHub secret（如 `ATLANTA_SSH_KEY`）
2. workflow 里用 secret 写入私钥：
```yaml
- name: Setup SSH key
  env:
    ATLANTA_SSH_KEY: ${{ secrets.ATLANTA_SSH_KEY }}
  run: |
    mkdir -p ~/.ssh
    echo "$ATLANTA_SSH_KEY" > ~/.ssh/id_ed25519
    chmod 600 ~/.ssh/id_ed25519
    ssh-keyscan -H -p PORT IP >> ~/.ssh/known_hosts 2>/dev/null
```

### 2. 浅克隆没有 HEAD~1
**问题**：`git diff HEAD~1` 报错 `unknown revision`
**原因**：actions/checkout 默认 fetch-depth: 1
**解决**：`fetch-depth: 0`

### 3. SSH host key 未信任
**问题**：`Host key verification failed`
**解决**：`ssh-keyscan -H -p PORT IP >> ~/.ssh/known_hosts`

### 4. gh 和 git 凭证不互通
**问题**：gh auth login 成功后 git push 仍失败
**解决**：
```bash
git config --global credential.helper "/usr/bin/gh auth git-credential"
# remote 需用 HTTPS：https://github.com/xxx/xxx.git
```

### 5. apt source 写入变量转义
**问题**：heredoc 里的 shell 变量无法展开
**解决**：先存变量，再写入文件

## 完整部署流程

### 1. 服务器安装 gh
```bash
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
ARCH=$(dpkg --print-architecture)
echo "deb [arch=$ARCH signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list
sudo apt-get update && sudo apt-get install -y gh
```

### 2. gh 认证
```bash
GH_TOKEN=$(gh auth token)
echo "$GH_TOKEN" | ssh server "GH_TOKEN='$GH_TOKEN' bash -c 'echo \"\$GH_TOKEN\" | gh auth login --with-token'"
```

### 3. 下载并注册 runner
```bash
GH_TOKEN=<token>
RUNNER_VERSION=$(curl -s -H "Authorization: token $GH_TOKEN" \
  https://api.github.com/repos/actions/runner/releases/latest | \
  grep -o '"tag_name": "[^"]*"' | cut -d'"' -f4)
curl -L -o runner.tar.gz "https://github.com/actions/runner/releases/download/${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION#v}.tar.gz"
tar xzf runner.tar.gz && rm runner.tar.gz

REG_TOKEN=$(curl -s -X POST -H "Authorization: token $GH_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/actions/runners/registration-token | \
  grep -o '"token": "[^"]*"' | cut -d'"' -f4)

./config.sh --name runner-name --url https://github.com/OWNER/REPO \
  --token "$REG_TOKEN" --labels label --unattended
```

### 4. 安装为 systemd service
```bash
sudo ./svc.sh install && sudo ./svc.sh start
```

### 5. GitHub secret 添加 SSH 私钥
```bash
gh secret set ATLANTA_SSH_KEY --body "$(cat ~/.ssh/id_ed25519)" --repo OWNER/REPO
```

### 6. workflow 模板
```yaml
name: Deploy
on: [push, workflow_dispatch]
jobs:
  deploy:
    runs-on: [self-hosted, label]
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Setup SSH key
        env:
          SSH_KEY: ${{ secrets.SSH_KEY_SECRET_NAME }}
        run: |
          mkdir -p ~/.ssh
          echo "$SSH_KEY" > ~/.ssh/id_ed25519
          chmod 600 ~/.ssh/id_ed25519
          ssh-keyscan -H -p PORT IP >> ~/.ssh/known_hosts 2>/dev/null
      - name: Deploy
        run: |
          ssh -o StrictHostKeyChecking=no user@IP -p PORT << 'EOF'
            # commands here
          EOF
```

## 验证
```bash
gh api /repos/OWNER/REPO/actions/runners | python3 -c "import sys,json; d=json.load(sys.stdin); [print(r['name'], r['status']) for r in d['runners']]"
# 应显示: runner-name online
```
