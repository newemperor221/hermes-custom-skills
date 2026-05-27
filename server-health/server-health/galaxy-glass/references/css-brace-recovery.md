# CSS 花括号修复日志 (2026-05-14)

## 背景
用 regex 提取 `@media (max-width: ...)` 规则时，`re.sub(r'\s*@media\s*\(max-width:\s*\d+px\)\s*\{[^}]*[^}]*\}', ...)` 只匹配到 2 层花括号深度。但 CSS 媒体查询里可能嵌套更多 `{}`，导致 regex 只去掉了一部分，留下多余的花括号。

## 症状
- 页面上部分 CSS 规则不生效（筛选栏偏移、卡片无间距等）
- 浏览器无 JS 错误，但排版异常
- 检查 `<style>` 块发现花括号不匹配

## 诊断方法
```python
s = content.find('<style>')
e = content.find('</style>')
style = content[s+7:e]
opens = style.count('{')
closes = style.count('}')
print(f'opens={opens}, closes={closes}, diff={opens - closes}')
```

## 修复方法
1. 逐行扫描找 balance 变负的行（多出关闭花括号的位置）
2. 对每个 `} } }` 序列精确替换为 `}`（用 `str.replace` 定位上下文）
3. 反复检查直到 balance = 0

## 教训
**绝不用正则操作 CSS。** CSS 花括号嵌套无法用简单 regex 处理。任何 CSS 重构都必须用精确的 `str.replace()` 或逐行 Python 操作。
