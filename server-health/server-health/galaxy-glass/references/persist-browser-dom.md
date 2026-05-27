# 持久化浏览器运行时 DOM 改动到源文件

GalaxyGlass 是单文件 SPA（`index.html`），CSS/JS/HTML 全部在同一个文件中。当 `browser_tool` 中的 DOM 操作修改了运行时页面状态（如 JS 注入的样式、DOM 元素），这些改动**只存在于内存中**，页面刷新即丢失。

## 什么时候需要持久化

| 场景 | 例 | 是否需要落盘 |
|------|----|------------|
| JS 运行时代码添加了新的 HTML 元素（下拉菜单、登录按钮） | sort-btn、login-btn | ✅ 必须保存 |
| JS 动态注入了 `<style>` 标签包含额外 CSS | sort-btn、dropdown 样式 | ✅ 必须保存 |
| JS 整体替换了 inline script | IIFE 版本 | ✅ 必须保存 |
| 通过 DOM API 修改了已有元素的 style 属性 | `el.style.color = 'red'` | ⛔ 下次页面加载即恢复 |
| 通过 `addEventListener` 绑定了交互 | 不需要保存 |

## 推荐方法：直接捕获 browser outerHTML

```js
// 在 browser_console 中执行
document.documentElement.outerHTML
```

返回值是整个页面的完整 HTML 字符串（包含 `<style>`、`<script>`、所有 DOM 元素）。将其写入源文件即可完整保存所有运行时状态。

### 注意事项

- **输出大小限制**：`browser_console` 返回值有限制（通常 ~100KB）。GalaxyGlass 完整 HTML 约 82KB，一次调用即可获取。
- **Cloudflare 注入**：如果通过 Cloudflare 域名访问，outerHTML 可能包含 CF Challenge 的 script 标签。部署前确认需要保留还是剔除。
- **不要用 innerHTML**：`document.documentElement.outerHTML` 包含完整的 `<!DOCTYPE html>` + `<html>` 包裹。
- **覆盖写入**：拿到 outerHTML 后直接用 `write_file` 覆盖源文件。
- **验证完整性**：写入后 grep 关键 class（如 `.sort-btn`、`.chip`）确认已包含。`wc -c` 确认文件大小合理。

## 不推荐的方法

| 方法 | 问题 |
|------|------|
| 逐个 JS 函数补丁 | 不知道完整变更范围，容易漏 |
| 仅保存 CSS diff | JS 同时改了很多东西 |
| 手动重建 HTML | 容易遗漏细节、样式不一致 |

## 何时不需要持久化

- 只调整了 CSS 变量值（`:root` 中的值）
- 只修改了 CSS 中的字体/颜色/间距
- 只通过 `patch` 工具修改了源文件
- 这些都已直接写入了源文件，不需要从浏览器捕获
