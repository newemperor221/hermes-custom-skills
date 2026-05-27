# 部署 — `--strip-components=1` 陷阱排查

## 现象

桌面端 stat.357561.xyz 主页 4 个统计卡片（stats-grid）显示为 1 列，但对线上文件发现 `.stats-grid { grid-template-columns: 1fr 1fr 1fr 1fr; }` 是正确的 4 列 CSS。

## 排查路径

1. **浏览器检查 computed style** → `gridTemplateColumns: "278px 278px 278px 278px"` 正确 ✅
2. **但用户说本地显示 1 列** → 怀疑 Cloudflare 缓存
3. **直接 SSH 检查远程文件** → CSS 文件在根目录（与 index.html 同级），但 index.html 引用的是 `styles/components.css` 🚩
4. **检查 deploy.sh** → `tar xzf ... --strip-components=1`
5. **追溯 tar 结构**：`tar czf -C src index.html styles/ scripts/` 创建的文件结构为 `index.html`, `styles/components.css`, `scripts/config.js`（无子目录层叠）
6. **`--strip-components=1` 对单层目录的效果**：
   - `index.html` → `index.html`（无 directory component，不变）
   - `styles/components.css` → `components.css`（剥掉了 `styles/`）
7. **结果**：CSS/JS 全部散落在 `/opt/komari/data/theme/` 根目录，而非 `styles/` 和 `scripts/` 子目录
8. **index.html 加载 `styles/components.css`** → 404 → 所有 CSS 不加载 → Grid 回退浏览器默认渲染（1列）

## 修复

```diff
- $SSH "cd $REMOTE && rm -f styles/*.css scripts/*.js index.html && tar xzf /tmp/galaxy-deploy.tar.gz --strip-components=1 && rm /tmp/galaxy-deploy.tar.gz"
+ $SSH "cd $REMOTE && rm -f styles/*.css scripts/*.js index.html && tar xzf /tmp/galaxy-deploy.tar.gz && rm /tmp/galaxy-deploy.tar.gz"
```

## 密码引号问题（同时发现）

```bash
# ❌ 错误：双引号里 $nE9A 被 bash 当变量解析
SSH="sshpass -p 'OX8w$nE9A%tfqb6v' ssh ..."

# ✅ 正确：用单引号赋值变量，再展开
PASS='OX8w$nE9A%tfqb6v'
SSH="sshpass -p '$PASS' ssh ..."
```

## 部署后验证清单

```bash
# 1. 验证文件位置
ssh ... "ls /opt/komari/data/theme/styles/"
ssh ... "ls /opt/komari/data/theme/scripts/"

# 2. 验证 CSS 可访问
curl -sI "https://stat.357561.xyz/styles/components.css?v=3" | head -3

# 3. 验证渲染
curl -s "https://stat.357561.xyz" | grep -c 'stats-grid'  # 应 >0
curl -s "https://stat.357561.xyz" | grep -o 'v=[0-9]'    # 检查版本号

# 4. 浏览器验证 grid layout
document.querySelector('.stats-grid')
  .computedStyleMap().get('grid-template-columns').toString()
# 应返回 "278.641px 278.656px 278.641px 278.656px"（4列）
```

## 教训

- `--strip-components=N` 绝对不要用在没有多层目录嵌套的 tar 上
- 不要假设部署脚本是正确的 — 每次修改 deploy.sh 后先用 `ssh ls` 验证文件落点
- CSS 不加载 → Grid 回退 1 列的现象和 CSS 写错成 1 列的现象完全一样，容易误判
