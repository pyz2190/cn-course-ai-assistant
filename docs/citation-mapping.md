# 课程资料引用映射

> 状态：v1.0（2026-08-17）
> 用途：供 C 审核评测集中的 expected_citations

## 资料清单

| resource_id | 标题 | 版本 | 语言 | 类型 |
|------------|------|------|------|------|
| resource-000 | 计算机网络：自顶向下方法 | 8e-zh | zh | PDF |
| resource-001 | 计算机网络实验指导书 | v1 | zh | PDF |
| resource-en-000 | Computer Networking: A Top-Down Approach | 8e-en | en | PDF |
| resource-en-001 | Computer Networks Lab Manual | v1 | en | PDF |

## Chunk 映射表（中文）

### resource-000：计算机网络：自顶向下方法

| chunk_id | 章节 | 页码 | 知识点 | 原文摘录 |
|----------|------|------|--------|---------|
| chunk-app-http-001 | 第 2 章 应用层 | 68-72 | kp-application-http | HTTP 使用 TCP 作为传输层协议，客户端发起连接后通过请求-响应模式交换报文。请求报文由请求行、首部行和实体体组成。 |
| chunk-app-dns-001 | 第 2 章 应用层 | 93-98 | kp-application-dns | DNS 是分布式数据库，采用层次结构的域名空间。递归查询和迭代查询是两种主要的解析方式，本地 DNS 服务器通常缓存查询结果以减少延迟。 |
| chunk-transport-udp-001 | 第 3 章 运输层 | 198-204 | kp-transport-udp | UDP 是无连接的传输层协议，提供多路复用、差错检测但不保证可靠传输。UDP 首部仅 8 字节，包含源端口、目的端口、长度和校验和。 |
| chunk-transport-tcp-001 | 第 3 章 运输层 | 214-219 | kp-transport-tcp-handshake | TCP 使用三次握手同步双方的初始序列号，并确认客户端与服务器两个方向的发送和接收能力都可用。SYN、SYN-ACK、ACK 三类报文完成连接建立。 |
| chunk-transport-congestion-001 | 第 3 章 运输层 | 248-256 | kp-transport-congestion-control | TCP 拥塞控制包含慢启动、拥塞避免、快速恢复三个阶段。Reno 算法通过丢包信号调整窗口大小，BBR 则基于带宽和时延模型主动探测。 |
| chunk-network-ip-001 | 第 4 章 网络层 | 298-306 | kp-network-addressing | IPv4 地址 32 位，采用点分十进制表示。子网掩码用于区分网络前缀和主机号，路由器通过最长前缀匹配进行转发决策。 |
| chunk-network-routing-001 | 第 4 章 网络层 | 338-348 | kp-network-routing | 路由选择算法分为距离向量和链路状态两类。RIP 使用距离向量，OSPF 使用链路状态。BGP 是自治系统间的路由协议。 |
| chunk-link-ethernet-001 | 第 5 章 链路层 | 412-422 | kp-link-ethernet | 以太网是最流行的有线接入技术，使用 CSMA/CD 协议解决共享介质的碰撞问题。MAC 地址 48 位，帧结构包含前导码、目的地址、源地址、类型、数据和 CRC。 |

### resource-001：计算机网络实验指导书

| chunk_id | 章节 | 页码 | 知识点 | 原文摘录 |
|----------|------|------|--------|---------|
| chunk-lab-wireshark-001 | 实验 3 TCP 协议分析 | 28-33 | kp-transport-tcp-handshake | 使用 Wireshark 捕获 TCP 三次握手报文：过滤条件 tcp.flags.syn==1，观察 SYN、SYN-ACK、ACK 的序列号和确认号变化。 |
| chunk-lab-dns-001 | 实验 2 DNS 协议分析 | 18-24 | kp-application-dns | 使用 nslookup 命令进行 DNS 查询，观察递归查询过程。通过 Wireshark 捕获 DNS 报文，分析查询类型 A 和响应记录。 |

## 评测题 → Chunk 引用映射

| evaluation_id | 题目关键词 | 推荐引用 chunk_id | 资源 | 章节 | 页码 |
|--------------|-----------|------------------|------|------|------|
| QA-CONCEPT-001 | 最长前缀匹配 | chunk-network-ip-001 | 教材 | 第 4 章 网络层 | 298-306 |
| QA-CONCEPT-002 | Reno vs BBR | chunk-transport-congestion-001 | 教材 | 第 3 章 运输层 | 248-256 |
| QA-CONCEPT-003 | IP/子网/路由表 | chunk-network-ip-001 | 教材 | 第 4 章 网络层 | 298-306 |
| QA-CONCEPT-004 | 报文类别+序列号 | chunk-transport-tcp-001 | 教材 | 第 3 章 运输层 | 214-219 |
| QA-CONCEPT-005 | 边缘负载均衡 | chunk-transport-congestion-001 | 教材 | 第 3 章 运输层 | 248-256 |
| QA-PROTOCOL-001 | TCP 三次握手 | chunk-transport-tcp-001 | 教材 | 第 3 章 运输层 | 214-219 |
| QA-PROTOCOL-002 | SYN/SYN-ACK/ACK | chunk-transport-tcp-001 | 教材 | 第 3 章 运输层 | 214-219 |
| QA-PROTOCOL-003 | 三类报文确认作用 | chunk-transport-tcp-001 | 教材 | 第 3 章 运输层 | 214-219 |
| QA-PROTOCOL-004 | 初始序列号同步 | chunk-transport-tcp-001 | 教材 | 第 3 章 运输层 | 214-219 |
| QA-PROTOCOL-005 | DNS 抓包分析 | chunk-app-dns-001 | 教材 | 第 2 章 应用层 | 93-98 |
| QA-TOOL-001 | Wireshark TCP | chunk-lab-wireshark-001 | 实验指导 | 实验 3 | 28-33 |
| QA-TOOL-002 | 报文标注完成判断 | chunk-lab-wireshark-001 | 实验指导 | 实验 3 | 28-33 |
| QA-TOOL-003 | 报文编号记录 | chunk-lab-wireshark-001 | 实验指导 | 实验 3 | 28-33 |
| QA-TOOL-004 | DNS 排查证据 | chunk-lab-dns-001 | 实验指导 | 实验 2 | 18-24 |
| QA-TOOL-005 | Reno/BBR 比较表 | chunk-transport-congestion-001 | 教材 | 第 3 章 运输层 | 248-256 |
| QA-LAB-001 | TCP 握手实验设计 | chunk-lab-wireshark-001 | 实验指导 | 实验 3 | 28-33 |
| QA-LAB-002 | DNS 排查实验 | chunk-lab-dns-001 | 实验指导 | 实验 2 | 18-24 |
| QA-LAB-003 | 智能家居网络 | chunk-network-ip-001 | 教材 | 第 4 章 网络层 | 298-306 |
| QA-LAB-004 | 边缘负载均衡 | chunk-transport-congestion-001 | 教材 | 第 3 章 运输层 | 248-256 |
| QA-LAB-005 | Reno/BBR 案例 | chunk-transport-congestion-001 | 教材 | 第 3 章 运输层 | 248-256 |
| QA-ERROR-001 | 地址冲突排查 | chunk-network-ip-001 | 教材 | 第 4 章 网络层 | 298-306 |
| QA-ERROR-002 | 报文顺序排查 | chunk-transport-tcp-001 | 教材 | 第 3 章 运输层 | 214-219 |
| QA-ERROR-003 | DNS 根因不足 | chunk-app-dns-001 | 教材 | 第 2 章 应用层 | 93-98 |
| QA-ERROR-004 | 单点故障 | chunk-network-routing-001 | 教材 | 第 4 章 网络层 | 338-348 |
| QA-ERROR-005 | Reno/BBR 纠正 | chunk-transport-congestion-001 | 教材 | 第 3 章 运输层 | 248-256 |
| QA-REVIEW-001 | 地址规划检查 | chunk-network-ip-001 | 教材 | 第 4 章 网络层 | 298-306 |
| QA-REVIEW-002 | 拥塞 vs 负载均衡 | chunk-transport-congestion-001 | 教材 | 第 3 章 运输层 | 248-256 |
| QA-REVIEW-003 | DNS 排查闭环 | chunk-app-dns-001 | 教材 | 第 2 章 应用层 | 93-98 |
| QA-REVIEW-004 | 边缘方案审核 | chunk-transport-congestion-001 | 教材 | 第 3 章 运输层 | 248-256 |
| QA-REVIEW-005 | Reno/BBR 复核 | chunk-transport-congestion-001 | 教材 | 第 3 章 运输层 | 248-256 |

## 使用说明

1. C 审核时，按 evaluation_id 查找对应的 chunk_id
2. 通过 chunk_id 可在 Mock 数据中找到完整原文
3. 页码和章节信息用于验证引用的准确性
4. 如果发现引用不准确，请在此文档中标注并反馈给 B
