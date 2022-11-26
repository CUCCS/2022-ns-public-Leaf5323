# 防火墙

## 实验内容

### 场景描述

局域网拓扑如下：

```text
+----------------------+          +-------------------------+       +----------------------+     
|     host-1           |          |   host-2                |       |     host-3           |  
|     172.16.18.11     |          |   eth0:0 172.16.18.1    |       |     172.16.18.12     |  
|                      |          |   eth0: 192.168.1.123   |       |                      |  
+-------------+--------+          +----------+--------------+       +-------------+--------+  
              |                              |                                    |
              |                              |                                    |
     +--------+------------------------------+--+                                 |
     |                交换机                    |---------------------------------+
     +-----------------+------------------------+
                       |
                       |
                 +-----+-----------+
                 |   eth0          |   `
                 |   192.168.1.1   |
              +--+-----------------+---------+
              |                              |
              |        host-gw / dns-svr     |
              |                              |
              +------------------+----------++
                                 |  eth1    |
                                 +----------+
```

上图的补充文字说明如下：

- host-gw 指的是该局域网的网关，已经配置为 NAT 方式，局域网内的主机 host-2 可以正常无障碍访问互联网；
- dns-svr 指的是该局域网中的 DNS 解析服务器，可以正常提供域名解析服务；
- 交换机没有设置 VLAN，所有端口正常工作；
- host-2上配置了 iptables规则；
- host-1上配置了默认网关指向 IP 地址：172.16.18.1，域名解析服务器配置为 IP：192.168.1.1
- host-3上配置了默认网关指向 IP 地址：172.16.18.1，域名解析服务器配置为 IP：192.168.1.1

### host-2 上的 iptables 配置脚本如下

```bash
#!/bin/bash
IPT="/sbin/iptables"
$IPT --flush
$IPT --delete-chain
$IPT -P INPUT DROP
$IPT -P FORWARD DROP
$IPT -P OUTPUT ACCEPT
$IPT -N forward_demo
$IPT -N icmp_demo
$IPT -A INPUT -i lo -j ACCEPT
$IPT -A OUTPUT -o lo -j ACCEPT
$IPT -A INPUT -p tcp ! --syn -m state --state NEW -s 0.0.0.0/0 -j DROP
$IPT -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
$IPT -A INPUT -p icmp -j icmp_demo
$IPT -A icmp_demo -p icmp -i eth0 -j ACCEPT
$IPT -A icmp_demo -j RETURN
$IPT -A FORWARD -j forward_demo
$IPT -A forward_demo -j LOG --log-prefix FORWARD_DEMO
$IPT -A forward_demo -p tcp --dport 80 -m string --algo bm --string 'baidu' -j DROP
$IPT -A forward_demo -p tcp -s 172.16.18.11 -j ACCEPT
$IPT -A forward_demo -p tcp -d 172.16.18.11 -j ACCEPT
$IPT -A forward_demo -p udp -s 172.16.18.11 --dport 53 -j ACCEPT
$IPT -A forward_demo -p udp -s 172.16.18.1  --dport 53 -j ACCEPT
$IPT -A forward_demo -p udp -s 192.168.1.1  --sport 53 -j ACCEPT
$IPT -A forward_demo -p tcp -s 172.16.18.1 -j ACCEPT
$IPT -A forward_demo -s 172.16.18.1 -j RETURN
$IPT -t nat -A POSTROUTING -s 172.16.18.1/24 -o eth0 -j MASQUERADE
```

### 实验任务要求

- 请对以上脚本逐行添加代码注释
- host-1可以ping通ip: 172.16.18.1吗？
- host-1可以ping通ip: 192.168.1.1吗？
- host-1可以ping通域名: www.baidu.com吗？
- host-1可以访问： `http://www.baidu.com` 吗？
- host-1可以访问：`http://61.135.169.121` 吗？
- host-3可以ping通ip: 172.16.18.1吗？
- host-3可以ping通ip: 192.168.1.1吗？
- host-3可以访问互联网吗？

## 实验记录

## 实验总结

## 参考链接
