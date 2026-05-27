# WARP 韩国/朝鲜 IPv4 方案（需自有 IPv6 段）

## 前提条件
- 自有 IPv6 地址段（且该段已被 MaxMind 等数据库认领为对应国家）
- MaxMind 同步完成（提交修正后约 2 周）

## 核心原理
Cloudflare WARP 分配的 IPv4 地址定位 = 你当前 IPv6 地址的定位。  
WARP 通过 MaxMind 查询 IPv6 定位，再分配对应国家的 IPv4。

## 流程
1. 拥有目标国家的 IPv6 段（如朝鲜 `KP`）
2. 提交 IP 定位修正到 MaxMind、IPInfo（理由：定位错误导致访问受限）
3. 等待数据库同步（1-2 周）
4. 在服务器上配置 WARP：
   ```bash
   # 安装 wgcf
   curl -fsSL git.io/wgcf.sh | sudo bash
   wgcf register && wgcf generate
   
   # 编辑配置文件，Endpoint 改为 IPv6
   vim wgcf-profile.conf
   # Endpoint = [2606:4700:d0::a29f:c001]:2408
   
   # 启动
   cp wgcf-profile.conf /etc/wireguard/warp.conf
   wg-quick up warp
   
   # 验证
   curl https://www.cloudflare.com/cdn-cgi/trace
   # 应显示 loc=KP, warp=on
   ```

## 适用场景
- 给 IPv6-only 小鸡获取双栈出口
- 获取特定国家 IPv4（如朝鲜装逼、韩国游戏等）

## 注意事项
- **必须有自有 IPv6 段**，借用别人的段无效
- MaxMind 对南极洲(AQ)近期不受理
- 全程约 1 个月才生效
- **不要提及用于匿名代理**
