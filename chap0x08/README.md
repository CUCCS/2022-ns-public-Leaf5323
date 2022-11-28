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

- [x] 请对以上脚本逐行添加代码注释
- [x] 回答问题：
  - host-1可以ping通ip: 172.16.18.1吗？
  - host-1可以ping通ip: 192.168.1.1吗？
  - host-1可以ping通域名: www.baidu.com吗？
  - host-1可以访问： `http://www.baidu.com` 吗？
  - host-1可以访问：`http://61.135.169.121` 吗？
  - host-3可以ping通ip: 172.16.18.1吗？
  - host-3可以ping通ip: 192.168.1.1吗？
  - host-3可以访问互联网吗？

## 实验记录

### 脚本内容逐行代码注释

```bash
# 说明：为了阅读方便添加了空行，每一行的注释写在命令的上一行

# 首先是常规的shebang操作
#!/bin/bash

# 定义变量IPT为/sbin/iptables用于后续直接执行iptables，免去PATH的麻烦并适当简写了名称
IPT="/sbin/iptables" 

# 没有指定某条链，于是清空所有链的规则
$IPT --flush

# 没有指定某条链，上一步已经清空了所有链的规则，于是删除所有非内置链
$IPT --delete-chain

# 指定内置INPUT链，对该链设置基础规则DROP，即逻辑上采取白名单机制
$IPT -P INPUT DROP

# 指定内置FORWARD链，对该链设置基础规则DROP，同上一条的白名单机制
$IPT -P FORWARD DROP

# 指定内置OUTPUT链，对该链设置基础规则ACCEPT，和上面不一样了，出口走黑名单机制的样子
$IPT -P OUTPUT ACCEPT

# 新建名为forward_demo的链
$IPT -N forward_demo

# 新建名为icmp_demo的链
$IPT -N icmp_demo

# 在INPUT链追加规则：ACCEPT本地回环网络lo接口接收的包
$IPT -A INPUT -i lo -j ACCEPT

# 在OUTPUT链追加规则：ACCEPT本地回环网络lo接口发送的包
$IPT -A OUTPUT -o lo -j ACCEPT

# 在INPUT链追加规则：DROP接收的任何来源地址的状态为NEW但是没有SYN标记的TCP包
# 关于状态为NEW，可能是已经建立了新的连接，或者是与连接双方都没有数据包记录的连接有关
$IPT -A INPUT -p tcp ! --syn -m state --state NEW -s 0.0.0.0/0 -j DROP

# 在INPUT链追加规则：ACCEPT接收的状态为ESTABLISHED和RELATED的包
# 关于状态为ESTABLISHED，指与连接双方有数据包记录的连接有关
# 关于状态为RELATED，指当前包正在新建连接，同时包又和已存在的连接有关
$IPT -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# 在INPUT链追加规则：将接收的ICMP包交付icmp_demo链
# 关于使用jump而不是goto，jump能够保证即使jump到的链不存在仍然能够回到jump之前的链，goto则不能
$IPT -A INPUT -p icmp -j icmp_demo

# 在icmp_demo链追加规则：ACCEPT以太网eth0接口接收的ICMP包
$IPT -A icmp_demo -p icmp -i eth0 -j ACCEPT

# 在icmp_demo链追加规则：将icmp_demo链返回
# 衔接前面INPUT链jump到icmp_demo链，有点像栈的感觉，icmp_demo链进栈并结束后出栈回到原来的链
$IPT -A icmp_demo -j RETURN

# 在FORWARD链追加规则：将接收的包交付forward_demo链
# 看样子自建链而不动内置链是个好习惯捏
$IPT -A FORWARD -j forward_demo

# 在forward_demo链追加规则：LOG接收的包，LOG前缀为FORWARD_DEMO
$IPT -A forward_demo -j LOG --log-prefix FORWARD_DEMO

# 在forward_demo链追加规则：DROP接收的以Boyer-Moore算法匹配到baidu字符串的目的端口为80的TCP包
# 查了一下，据说BM算法在较小的字母表情况下表现会不太高效，比如DNA，此时会有KMP算法出现
$IPT -A forward_demo -p tcp --dport 80 -m string --algo bm --string 'baidu' -j DROP

# 在forward_demo链追加规则：ACCEPT接收的源地址为172.16.18.11的TCP包
$IPT -A forward_demo -p tcp -s 172.16.18.11 -j ACCEPT

# 在forward_demo链追加规则：ACCEPT接收的目的地址为172.16.18.11的TCP包
$IPT -A forward_demo -p tcp -d 172.16.18.11 -j ACCEPT

# 在forward_demo链追加规则：ACCEPT接收的源地址为172.16.18.11且目的端口为53的UDP包
# 53端口，嗅到了DNS的味道（警觉
$IPT -A forward_demo -p udp -s 172.16.18.11 --dport 53 -j ACCEPT

# 在forward_demo链追加规则：ACCEPT接收的源地址为172.16.18.1且目的端口为53的UDP包
# 递归查询吗（思考
$IPT -A forward_demo -p udp -s 172.16.18.1  --dport 53 -j ACCEPT

# 在forward_demo链追加规则：ACCEPT接收的源地址为192.168.1.1且源端口为53的UDP包
# 有点乱，似乎192.168.1.1是最终的上游了
$IPT -A forward_demo -p udp -s 192.168.1.1  --sport 53 -j ACCEPT

# 在forward_demo链追加规则：ACCEPT接收的源地址为172.16.18.1的TCP包
$IPT -A forward_demo -p tcp -s 172.16.18.1 -j ACCEPT

# 在forward_demo链追加规则：将forward_demo链返回
# 和前面的icmp_demo一样，走完forward_demo链后返回到jump前的链上去
$IPT -A forward_demo -s 172.16.18.1 -j RETURN

# 在nat表的POSTROUTING链追加规则：对源地址为172.16.18.1/24的包从以太网eth0接口执行MASQUERADE
# 关于MASQUERADE，man手册的说法是给包发送的接口指定IP地址映射
# 参考其他问答，MASQUERADE也是构造NAT，相比SNAT其不需要知道出口IP
$IPT -t nat -A POSTROUTING -s 172.16.18.1/24 -o eth0 -j MASQUERADE
```

### Q&A

- host-1可以ping通ip: 172.16.18.1吗？

  - 可以的，172.16.18.1即host-2，属于内部网络走INPUT链，而ICMP包会被交付给icmp_demo链处理，而icmp_demo链内规则为ACCEPT入口接口为eth0的ICMP包，eth0分配到的地址正好是172.16.18.1，而OUTPUT链默认为ACCEPT并且没有规则丢弃ICMP回复，则host-1可以ping通172.16.18.1

- host-1可以ping通ip: 192.168.1.1吗？

  - 不可以，192.168.1.1对于host-2为外部网络，需要走FORWARD链，而白名单机制的FORWARD链交付的forward_demo链中没有针对ICMP包的ACCEPT规则，则会因为默认DROP规则被丢弃，表现为不能ping通

- host-1可以ping通域名: www.baidu.com吗？

  - 不可以，和第二题类似，先看补充信息中说到host-1配置了网关指向host-2而DNS服务器指向了dns-svr，首先host-1的DNS请求目的地址应当为192.168.1.1，会进入host-2的FORWARD链，查看host-2在FORWARD链对DNS请求也就是对53端口UDP包的处理，首先由FORWARD链进入forward_demo链，源地址为172.16.18.11目的端口为53的UDP包对应规则为ACCEPT，则请求能够正确被发送，再看DNS响应即源地址为192.168.1.1且源端口为53的UDP包，对应规则为ACCEPT，则响应也能被正确返回，host-1平稳拿到域名www.baidu.com的IP地址，回到不能ping通这件事，百度的IP显然是外部网络，需要走FORWARD链，然而白名单机制的FORWARD链交付的forward_demo链中没有对ICMP的ACCEPT规则，于是不能ping通，但是上网是没问题的（怎么好像是下下一题的内容）

- host-1可以访问： `http://www.baidu.com` 吗？

  - 不可以，首先上一问已经确定了DNS请求和响应是没问题的，目前host-1拥有域名www.baidu.com的IP地址，然后是已知host-2作为host-1的网关，并且在host-2中明确设置了用字符串匹配的方式丢弃包含`baidu`字段的目的端口为80的TCP包，至此题目本身的回答就结束了  
    （但是其实可以更复杂一点，其实是写之前以为是ACCEPT规则才导致了后续内容的出现，但是是我切实想到的，决定有必要写下来，详见“[关于不看规则先回答问题而带来的额外思考](#关于不看规则先回答问题而带来的额外思考)”）

- host-1可以访问：`http://61.135.169.121` 吗？

  - 可以的，根据host-2的forward_demo链内规则可知，源地址和目的地址为172.16.18.11的TCP包是ACCEPT的，所以访问不会受限（这是要以IP形式上网绕过对baidu的限制吗）

- host-3可以ping通ip: 172.16.18.1吗？

  - 可以的，这个和第一题是一样的吧，172.16.18.1对应host-2的eth0，INPUT链对ICMP的包交给icmp_demo处理，而icmp_demo中的规则是只要入口为eth0并且为ICMP包则ACCEPT，同样是OUTPUT链为默认ACCEPT状态，于是请求和回应都没有问题

- host-3可以ping通ip: 192.168.1.1吗？

  - 不可以，和第二题的逻辑相同，对于外部网络192.168.1.1，host-2需要走FORWARD链，而白名单机制下FORWARD交付的forward_demo链没有ICMP的ACCEPT规则，会被丢弃，于是不能ping通

- host-3可以访问互联网吗？

  - 不可以，互联网首先为外部网络，需要走FORWARD链，但是FORWARD交付的forward_demo链中仅对源地址和目的地址为172.16.18.11的TCP包进行了ACCEPT,也就是仅做了host-1的适配，按照白名单机制，host-3的所有对外TCP和UDP请求和响应都会被丢弃（其实连不上网反而更安全）

## 实验总结

### 一点心得

#### 对iptables有了强化的了解

之前实验五的时候为了模拟主机的不同状态其实已经自学过一边iptables了，这次再来做这部分实验感到非常舒适，并且也弥补了我之前很多因为按需学习而丢弃的知识，比如不同链的逻辑，入站出站还是转发，包括NAT是最后配置于POSTROUTING链的等等，收获颇丰🍾

#### 一些额外的思考

关于上面的问题，虽然是给出了答案，但似乎很多是有可能被逆转的，比如如果host-3使用ARP欺骗让host-2认为172.16.18.11是host-3的物理地址，那么其实在被发现之前也是有一定可能可以访问互联网的，还想到了正向代理，结果好像因为host-3和孤岛一样的处境好像雀食也没什么办法😂

### 各种踩坑

#### 关于不看规则先回答问题而带来的额外思考

回答当中其实已经说明了是以为80端口加字符串匹配那个是ACCEPT规则于是想多了，但是反而是很有意思的坑，倒是建议黄药师把这部分内容作为题目给师弟师妹们玩😂

题目还是host-1能否访问`http://www.baidu.com`，但是现在host-2对于目的端口为80的TCP包中`baidu`字符串匹配的规则是ACCEPT或者改为仅针对80端口ACCEPT

此时就变得比较有趣了，答案变成了不一定，分歧在于时间点，目前时间为2022年11月28日，此时当我尝试使用HTTP协议以域名www.baidu.com的形式访问百度时，会被307重定向到HTTPS的页面，而此时使用的端口为443端口，即SSL加密端口，回看作为host-1网关的host-2的相关规则，如果是白名单机制，并且只给了80端口ACCEPT，则重定向会失败，变成了不能访问的状态，但是如果时间回到10年前或者更早，在HTTPS还没有普及的年代，百度也还没有全站使用HTTPS，那时或许又变成可以访问到页面的状态了

另外是和下一题有一点呼应的意思，因为正巧`http://61.135.169.121`就是百度的页面，甚至直接用了HTTP协议，总感觉有点HTTPS了但是又没有完全HTTPS的意思🤔

说白了不过是个纯脑洞，考察的其实也不是关于iptables的知识，只是一个网络相关的小坑，并且也是在前几年所谓的百度全站转用HTTPS才有这部分想法

总之希望这部分内容不会太无聊就好，也就看看，图一乐😂

## 参考链接

- [iptables(8) - Linux man page](https://linux.die.net/man/8/iptables)

- [linux - iptables -j vs. -g parameters - Stack Overflow](https://stackoverflow.com/questions/31606411/iptables-j-vs-g-parameters)

- [theory - What are the main differences between the Knuth-Morris-Pratt and Boyer-Moore search algorithms? - Stack Overflow](https://stackoverflow.com/questions/12656160/what-are-the-main-differences-between-the-knuth-morris-pratt-and-boyer-moore-sea)

- [cuc-ns/main.md at master · c4pr1c3/cuc-ns](https://github.com/c4pr1c3/cuc-ns/blob/master/chap0x08/main.md)
