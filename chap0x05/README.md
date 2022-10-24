# 基于Scapy编写端口扫描器

## 实验要求

- [x] 禁止探测互联网上的IP，严格遵守网络安全相关法律法规

- 完成以下扫描技术的编程实现

  - [x] TCP connect scan / TCP stealth scan

  - [x] TCP Xmas scan / TCP fin scan / TCP null scan

  - [x] UDP scan

- [x] 上述每种扫描技术的实现测试均需要测试端口为：`开放`、`关闭`和`过滤`状态时的程序执行结果

- [x] 提供每一次扫描测试的抓包结果并分析与课本中的扫描方法原理是否相符？如果不同，试分析原因

- [x] 在实验报告中详细说明实验网络环境拓扑、被测试IP的端口状态时如何模拟的

- [ ] (可选) 复刻`nmap`的上述扫描技术实现的命令行参数开关

## 实验环境

### 编程环境

- Python 3.10.X

- Scapy 2.4.5

  - ```powershell
                         aSPY//YASa
                 apyyyyCY//////////YCa       |
                sY//////YSpcs  scpCY//Pp     | Welcome to Scapy
    ayp a yyyyyyySCP//Pp           syY//C    | Version 2.4.5
    AYAs AYYYYYYYY///Ps              cY//S   |
             pCCCCY//p          cSSps y//Y   | https://github.com/secdev/scapy
             SPPPP///a          pP///AC//Y   |
                  A//A            cyP////C   | Have fun!
                  p///Ac            sC///a   |
                  P////YCpc           A//A   | We are in France, we say Skappee.
           scccccp///pSP///p          p//Y   | OK? Merci.
          sY/////////y  caa           S//P   |             -- Sebastien Chabal
           cayCyayP//Ya              pY/Ya   |
             sY/PsY////YCc          aC//Yp
              sc  sccaCY//PCypaapyCP//YSs
                       spCPY//////YPSps
                           ccaacs
    ```

### 测试平台

- Kali Rolling on WSL 0.70.0.0 (作为扫描者)

  - ```neofetch
    $ neofetch
    ..............                                     leaf@ZephyrusG15
                ..,;:ccc,.                             ----------------
              ......''';lxO.                           OS: Kali GNU/Linux Rolling on Windows 10 x86_64
    .....''''..........,:ld;                           Kernel: 5.15.68.1-microsoft-standard-WSL2
               .';;;:::;,,.x,                          Uptime: 1 day, 18 hours, 35 mins
          ..'''.            0Xxoc:,.  ...              Packages: 2792 (dpkg)
      ....                ,ONkc;,;cokOdc',.            Shell: bash 5.2.0
     .                   OMo           ':ddo.          Theme: Kali-Dark [GTK2], adw-gtk3-dark [GTK3]
                        dMc               :OO;         Icons: Flat-Remix-Blue-Dark [GTK2/3]
                        0M.                 .:o.       Terminal: Windows Terminal
                        ;Wd                            CPU: AMD Ryzen 9 4900HS with Radeon Graphics (16) @ 2.994GHz
                         ;XO,                          GPU: 28b8:00:00.0 Microsoft Corporation Basic Render Driver
                           ,d0Odlc;,..                 Memory: 538MiB / 7650MiB
                              ..',;:cdOOd::,.
    ```

- Debian 10 on VirtualBox 7.0.0 (作为被扫描者)

  - ```neofetch
    # neofetch
           _,met$$$$$gg.          root@debian
        ,g$$$$$$$$$$$$$$$P.       -----------
      ,g$$P"     """Y$$.".        OS: Debian GNU/Linux 10 (buster) x86_64
     ,$$P'              `$$$.     Host: VirtualBox 1.2
    ',$$P       ,ggs.     `$$b:   Kernel: 4.19.0-22-amd64
    `d$$'     ,$P"'   .    $$$    Uptime: 20 hours, 9 mins
     $$P      d$'     ,    $$P    Packages: 462 (dpkg)
     $$:      $$.   -    ,d$$'    Shell: bash 5.0.3
     $$;      Y$b._   _,d$P'      Terminal: /dev/pts/0
     Y$$.    `.`"Y$$$$P"'         CPU: AMD Ryzen 9 4900HS with Radeon Graphics (1) @ 2.994GHz
     `$$b      "-.__              GPU: VMware SVGA II Adapter
      `Y$$                        Memory: 76MiB / 987MiB
       `Y$$.
        `$$b.
          `Y$$b.
             `"Y$b._
                  `"""
    ```

### “全新”的网络拓扑结构

是的，上面的测试平台其实已经在暗示了这次实验网络拓扑的诡异性：

>用Windows的Linux子系统安装的Kali进行扫描，流量通过WSL的虚拟网卡转出再由VirtualBox的Host-Only网卡转入，最后到达被扫描主机`gateway-debian`（老面孔了，第一次实验那会儿搭起来的Debian10）

下面是在Kali上`traceroute`到`gateway-debian`IP的输出结果：

```bash
# gateway-debian的IP地址为192.168.56.113
$ traceroute 192.168.56.113
traceroute to 192.168.56.113 (192.168.56.113), 30 hops max, 60 byte packets
 1  ZephyrusG15.mshome.net (172.17.176.1)  1.647 ms  1.126 ms  0.757 ms
 2  192.168.56.113 (192.168.56.113)  2.609 ms  3.493 ms  3.124 ms
```

可以看到，其实仅经过了两跳，并且两台“虚拟机”的网络也属于完全内网，符合相关法律要求😂

### 被扫描端口状态模拟

这一块其实挺有趣的，因为并不需要每次扫描一个端口，然后每次配置过滤规则，只需要选好已知的TCP端口和UDP端口各3个，分别对应`开放`、`关闭`和`过滤`的状态即可，在分别测试不同方式的扫描时分别扫描不同状态的端口就达到目的了，具体的端口选择和状态分配可以看下面的图示：

```mermaid
flowchart TD
A[选择扫描协议]-->B{TCP or UDP?}
B-->|TCP|C[选择目标端口]
B-->|UDP|D[选择目标端口]
C-->E{22 or 8000 or 8080?}
D-->F{53 or 67 or 3389?}
E-->|Port 22|G["SSH端口:开放✅"]
E-->|Port 8000|H["Python http.server端口:设置过滤规则🚮"]
E-->|Port 8080|I["HTTP服务备用端口:关闭⛔"]
F-->|Port 53|J["DNS端口:开放✅"]
F-->|Port 67|K["DHCP端口:设置过滤规则🚮"]
F-->|Port 3389|L["远程桌面端口:关闭⛔"]
```

应该有一图胜千言的效果吧🤔

## 实验记录

### 代码编写部分

这一部分没有打算写太多内容，主要是说清楚代码的思路

另外是代码的可读性很高，这点我充满自信( •̀ ω •́ )✧

#### TCP Connect扫描

由于是先写的TCP SYN扫描，结果回过头写这个的时候发现大部分就是直接复制粘贴SYN扫描的代码😂

以下是代码设计思路：

```mermaid
flowchart TD
  A["向目标TCP端口发送SYN包📶"]-->B{收到回复?}
  B-->|收到SYN,ACK|C[发送ACK包建立连接]
  C-->D["认为目标TCP端口开放✅"]
  B-->|收到RST,ACK|E["认为目标TCP端口关闭⛔"]
  B-->|没有响应|F["认为目标TCP端口被过滤🚮"] 
  D-->G[发送RST包拆除连接]
```

有没有觉得和下面SYN扫描的设计图有亿点点相似😏

#### TCP Stealth扫描

首先这个命名很具有迷惑性，咕咕噜了一下得知其实是TCP SYN扫描，只是比TCP Connect扫描少了收到SYN,ACK后返回ACK而已，只是不建立连接，也不知道为什么就“stealth”了🤔

代码内容这里不赘述，稍微画一下设计思路：

```mermaid
flowchart TD
  A["向目标TCP端口发送SYN包📶"]-->B{收到回复?}
  B-->|收到SYN,ACK|C["认为目标TCP端口开放✅"]
  C-->D[发送RST包拆除连接]
  B-->|收到RST,ACK|E["认为目标TCP端口关闭⛔"]
  B-->|没有响应|F["认为目标TCP端口被过滤🚮"]
```

#### TCP Xmas扫描

先写的TCP FIN扫描，于是这一块又是很多可以复制粘贴的代码内容😂

不过确实也很像，和TCP FIN扫描的区别在于构造的TCP数据包拥有更多的flags，也就是PSH和URG标记，虽然判定上完全一致就是了

以下是设计思路：

```mermaid
flowchart TD
  A["向目标TCP端口发送Xmas包📶"]-->B{收到回复?}
  B-->|收到RST|C["认为目标TCP端口关闭⛔"]
  B-->|没有响应|D["认为目标TCP端口开放✅或被过滤🚮"]
```

当然，其中的Xmas包其实就是FIN,PSH,URG包

#### TCP FIN扫描

以下是设计思路：

```mermaid
flowchart TD
  A["向目标TCP端口发送FIN包📶"]-->B{收到回复?}
  B-->|收到RST|C["认为目标TCP端口关闭⛔"]
  B-->|没有响应|D["认为目标TCP端口开放✅或被过滤🚮"]
```

判定逻辑上和下面的UDP扫描很像，但是好在是TCP协议，可靠度大大提升了😮

#### TCP NULL扫描

仍然是很多复制粘贴，实在没办法，TCP FIN、Xmas和NULL扫描的逻辑完全是一样的

以下是设计思路：

```mermaid
flowchart TD
  A["向目标TCP端口发送NULL包📶"]-->B{收到回复?}
  B-->|收到RST|C["认为目标TCP端口关闭⛔"]
  B-->|没有响应|D["认为目标TCP端口开放✅或被过滤🚮"]
```

其中NULL包是flags被设置为0的TCP包

#### UDP扫描

先放上设计思路：

```mermaid
flowchart TD
  A["向目标UDP端口发送UDP数据包📶"]-->B{收到回复?}
  B-->|收到ICMP_PORT_UNREACHABLE|C["认为目标UDP端口关闭⛔"]
  B-->|没有响应|D["认为目标UDP端口开放✅或被过滤🚮"]
```

感觉就是非常不可靠，过滤状态和开放状态都不会有响应，唯一能稍微稳定一些的判定一个端口是否不开放还可能因为ICMP错误报文在传输中丢失而同样变得不稳定，总之是一种矛盾的扫描方式，但从存在即合理的角度思考，肯定有不得不用UDP扫描的情况，比如TCP的各种扫描都不好用的时候🤔

### 代码测试部分

首先我觉得有必要把`iptables`的过滤规则放在这里，这样有问题的话也不太需要继续看下去了

- TCP 8000端口

  - ```bash
    # DROP掉SYN包，用于过滤TCP Connect和TCP Stealth扫描
    iptables -t raw -A PREROUTING -p tcp --dport 8000 --tcp-flags SYN,ACK,FIN,RST SYN -j DROP
    # 添加检测PSH和URG，DROP掉FIN,PSH,URG包，用于过滤TCP Xmas扫描
    iptables -t raw -A PREROUTING -p tcp --dport 8000 --tcp-flags SYN,ACK,FIN,RST,PSH,URG FIN,URG,PSH -j DROP
    # 仅DROP掉FIN包，用于过滤TCP FIN扫描
    iptables -t raw -A PREROUTING -p tcp --dport 8000 --tcp-flags SYN,ACK,FIN,RST FIN -j DROP
    # 检测所有flags并DROP没有flag的包，用于过滤TCP NULL扫描
    iptables -t raw -A PREROUTING -p tcp --dport 8000 --tcp-flags ALL NONE -j DROP
    ```

- UDP 67端口

  - ```bash
    # 匹配协议为UDP且目标端口为67则DROP
    iptables -t raw -A PREROUTING -p udp --dport 67 -j DROP
    ```

诚然上面的这些过滤规则一旦生效，各自端口的服务估计也寄了，可能防火墙是这样的吧🤔

其次是说明一下端口选择：

- 对TCP扫描来说，首先22端口是SSH的端口，由于宿主机刚好通过SSH连接到`gateway-debian`虚拟机所以肯定是开放的，并且也不会设置过滤规则；然后是8000端口很显然是我在`gateway-debian`上通过命令`python3 -m http.server &`令其在后台以默认8000端口开了一个HTTP的服务器，对这个端口进行了上述非常完整的`iptables`TCP扫描规则过滤；8080端口则是一些网页服务器的备用端口，由于没有配置任何进程使用该端口，默认是关闭状态

- 对UDP扫描来说，首先53端口是DNS端口，为了正常的域名解析该端口一定是开放的；然后是67端口，这个端口选择是搜索使用UDP协议的服务时偶然发现的，归属于DHCP服务，由于扫描期间也不会有新设备接入，于是选择对该端口设置`iptables`UDP扫描过滤规则；3389端口是RDP端口也就是常说的远程桌面，`gateway-debian`连GUI都没有，纯CLI的，自然也没有使用到该端口，于是默认是关闭状态

#### TCP协议

为了便于阅读，统一将结果绘制为表格：

端口|22|8000|8080
:-:|:-:|:-:|:-:
真实状态|开放✅|设置过滤规则🚮|关闭⛔
TCP Connect扫描结果|![screenShot](./img/tcpConnectScan22.png)|![screenShot](./img/tcpConnectScan8000.png)|![screenShot](./img/tcpConnectScan8080.png)
TCP Stealth扫描结果|![screenShot](./img/tcpStealthScan22.png)|![screenShot](./img/tcpStealthScan8000.png)|![screenShot](./img/tcpStealthScan8080.png)
TCP Xmas扫描结果|![screenShot](./img/tcpXmasScan22.png)|![screenShot](./img/tcpXmasScan8000.png)|![screenShot](./img/tcpXmasScan8080.png)
TCP FIN扫描结果|![screenShot](./img/tcpFINscan22.png)|![screenShot](./img/tcpFINscan8000.png)|![screenShot](./img/tcpFINscan8080.png)
TCP NULL扫描结果|![screenShot](./img/tcpNULLscan22.png)|![screenShot](./img/tcpNULLscan8000.png)|![screenShot](./img/tcpNULLscan8080.png)

#### UDP协议

相比上面各种TCP扫描简洁多了，仍然是以表格的形式：

端口|真实状态|UDP扫描结果
:-:|:-:|:-:
53|开放✅|![screenShot](./img/udpScan53.png)
67|设置过滤规则🚮|![screenShot](./img/udpScan67.png)
3389|关闭⛔|![screenShot](./img/udpScan3389.png)

### 抓包分析部分

对于上述的扫描操作，都通过`tcpdump -i enp0s8 -w scanDump.pcap`进行了抓包保存，并在Windows宿主机上在本仓库文件夹>`chap0x05`>`pcap`文件夹下通过`scp debian:/root/scanDump.pcap ./scanDump.pcap`，原文件我也会一并上传

关于分析数据包这块，说实话没什么头绪，整个实验折腾到最后的最后反而没有耐心去看具体抓到的包是什么情况😔

下面是用Wireshark的流量图功能观看整个扫描测试过程，当然有使用包过滤规则`(tcp or udp or icmp) and not (ssdp or dhcp or mdns)`进行了筛选：

![screenShot](./img/scanDump.png)

我的感觉是没有什么问题，举例说明的话TCP的8000端口可以看到SYN包并没有回复，说明确实有被过滤掉，UDP则是非常清爽，除了3389端口确实Unreachable之外其他的一点反应都没有🤔

## 实验总结

### 各种踩坑

#### 论提前了解黑话的重要性

可以看到参考链接里面有放上我搜索TCP的flags简写并“采纳”的回答（这么说感觉自己好狂😂），是的，上来看Scapy的文档，甚至看不明白RA的意思，看到SA猜测了一下是SYN,ACK的缩写，但是疑惑RA是不是RST,ACK的缩写，咕咕噜一下`tcp ra flag`很快找到了很详尽的解释，用得上的简写用表格记录一下吧：

flag简写|含义
:-:|:-:
TCP:RA|RST,ACK
TCP:FA|FIN,ACK
TCP:SA|SYN,ACK

#### 或许`iptables`应该优先于本次实验学习

当然，需要先了解攻击，然后才会有防御的相关考量，这一点之前课上有说过，所以才说“或许”，但是只是针对这次实验来说，如果没有`iptables`的相关知识，首先就不能创造出drop包的filtered端口环境，于是也不能很好地得知扫描filtered的端口时在包被drop没有回应的情况下scapy的`sr()`函数会如何return，这种情况下又怎么编写工具呢，判断逻辑这块就已经断了😔

又或者这次实验就是为了以这种旁敲侧击的方式让人学习也说不定🤔总之是先去学习了drop一些常见端口扫描的`iptables`规则，才能进一步研究扫描工具的判定逻辑

当然也可以研究Windows的防火墙就是了，但是没有选这条路

另外是放上学习`iptables`的记录，是之前老师配好的Debian10系统中的`iptables`的开机自启规则文件`/etc/network/interfaces`的一些阅读理解注释，话说为了找到这个文件也算是费了不少功夫（这里就不说了）：

```bash
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

source /etc/network/interfaces.d/*

# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
allow-hotplug enp0s3
iface enp0s3 inet dhcp
allow-hotplug enp0s8
iface enp0s8 inet dhcp
allow-hotplug enp0s9
iface enp0s9 inet static
  address 172.16.111.1
  netmask 255.255.255.0
  post-up echo 1 > /proc/sys/net/ipv4/ip_forward
  post-up   iptables -P FORWARD DROP #将FORWARD链规则设置为DROP（先设置为丢弃所有包，随后再一条条添加白名单规则的意思吧）
  post-up   iptables -t nat -A POSTROUTING -s '172.16.111.0/24' ! -d '172.16.111.0/24' -o enp0s3 -j MASQUERADE #选择nat表，向POSTROUTING链追加：出口为enp0s3的源网段“172.16.111.0/24”到目的网段非“172.16.111.0/24”的流量，规则为MASQUERADE（查了一下这个MASQUERADE规则，个人觉得的好理解的说法就是构建NAT网络，从出口无法得知入口的网络信息，实现了字面意义上的“Masquerade”，这一条规则的意思大致是172.16.111.0/24网段通过enp0s3访问外部网络要使用NAT逻辑，应该没理解错吧）
  post-up   iptables -I FORWARD -s '172.16.111.0/24' ! -d '172.16.111.0/24' -i enp0s9 -j ACCEPT #向FORWARD链插入：入口为enp0s9的源网段“172.16.111.0/24”到目的网段非“172.16.111.0/24”的流量，规则为ACCEPT（说人话就是允许入口为enp0s9的172.16.111.0/24网段内的主机互相访问）
  post-up   iptables -I FORWARD -s '172.16.111.0/24' -d '172.16.222.0/24' -i enp0s9 -j DROP #向FORWARD链插入：入口为enp0s9的源网段“172.16.111.0/24”到目的网段“172.16.222.0/24”的流量，规则为DROP（说人话就是阻止入口为enp0s9的172.16.111.0/24网段内的主机访问172.16.222.0/24网段）
  post-up   iptables -A FORWARD -m state --state RELATED,ESTABLISHED -j ACCEPT #向FORWARD链追加：匹配state模块中满足RELATED和ESTABLISHED状态的流量，规则为ACCEPT（最开始不是很理解这块，逐一分析就清楚了，首先是ESTABLISHED为防火墙允许且有跟踪的连接状态，RELATED为已经判定为由ESTABLISHED状态的连接生成的主连接之外的连接（好绕救命🤮），翻译过来的话就是防火墙允许的连接和其“子连接”都被允许通过）
  post-down iptables -t nat -D POSTROUTING -s '172.16.111.0/24' ! -d '172.16.111.0/24' -o enp0s3 -j ACCEPT #这里显然是ifdown时进行的操作，删掉之前追加的规则，不详细再写一遍了
  post-down iptables -D FORWARD -s '172.16.111.0/24' ! -d '172.16.111.0/24' -i enp0s9 -j ACCEPT #同样是删除操作
  post-down iptables -D FORWARD -m state --state RELATED,ESTABLISHED -j ACCEPT #仍然是删除操作
  post-down iptables -I FORWARD -s '172.16.111.0/24' -d '172.16.222.0/24' -i enp0s9 -j DROP #这里很有趣，到最后ifdown了仍然要插入阻止172.16.111.0/24内网访问到172.16.222.0/24网段的DROP规则，属于明确划分界限了😂
allow-hotplug enp0s10
iface enp0s10 inet static #下面的enp0s10网卡配置和上面的enp0s9几乎照抄，不赘述了
  address 172.16.222.1
  netmask 255.255.255.0
  post-up   iptables -P FORWARD DROP
  post-up   iptables -t nat -A POSTROUTING -s '172.16.222.0/24' ! -d '172.16.222.0/24' -o enp0s3 -j MASQUERADE
  post-up   iptables -I FORWARD -s '172.16.222.0/24' ! -d '172.16.222.0/24' -i enp0s10 -j ACCEPT
  post-up   iptables -I FORWARD -s '172.16.222.0/24' -d '172.16.111.0/24' -i enp0s10 -j DROP
  post-down iptables -t nat -D POSTROUTING -s '172.16.222.0/24' ! -d '172.16.222.0/24' -o enp0s3 -j MASQUERADE
  post-down iptables -D FORWARD -s '172.16.222.0/24' ! -d '172.16.222.0/24' -i enp0s10 -j ACCEPT
  post-down iptables -I FORWARD -s '172.16.222.0/24' -d '172.16.111.0/24' -i enp0s10 -j DROP
```

另外觉得必须说说`iptables`中有关--tcp-flags的解读，这里放上让我搞明白--tcp-flags工作原理的解释原文：

>[!] --tcp-flags mask comp  
>Match  when  the TCP flags are as specified.  The first argument mask is the flags which we should examine, written as a comma-separated list, and the second argument comp is a comma-separated list of flags which must be set.  Flags are: SYN ACK FIN RST URG PSH ALL NONE.  Hence the command iptables -A FORWARD -p tcp --tcp-flags SYN,ACK,FIN,RST SYN will only match packets with the SYN flag set, and the ACK, FIN and RST flags unset.

简单翻译一下，其中的核心在于，mask指明了对TCP包的哪些flags进行检测，当出现comp中列出的flags时认为匹配到规则，于是执行规则的DROP

这时再去写特定的TCP过滤规则感觉会清爽很多了😃

再次感慨：或许`iptables`应该优先于本次实验学习🤔

### 一点心得

说真的，这篇报告连续写了好几天，为了做这个实验也不得不先学习了很多别的知识，到最后真的就是累趴的感觉，有一点遗憾因为要到DDL了所以暂时没有进行个人复刻纸糊的虚假`nmap`，尤其是分开写的各个工具似乎都还挺稳定的情况下😔可能后续会找机会补上（一般这么说都很难再回过头折腾就是了）

另外是通过这个实验确实学到了太多东西，何况还是在我这种并不是100%达到目的的情况下（这里是指通过个人理解的需要完成的点，可能老师那边会有更高层次的一些要求，但是在被告知之前并不能意识到）

说点轻松的话题，这次学会了一些`iptables`的操作之后，总让我忍不住想去折腾看看家里的路由器😂（Merlin固件可是有的玩的，何况是Koolshare改版）毕竟到这次实验完成之前，也都只是用其自动化生成的一些规则，现在来看说不定能看懂一两条了也说不定

结束，准备开PR！🎉

## 参考链接

- [Usage — Scapy 2.5.0 documentation](https://scapy.readthedocs.io/en/latest/usage.html)

- [networking - What do the following mean: TCP:RA, TCP:FA ,TCP:PA, TCP:S, TCP:SEC - Server Fault](https://serverfault.com/questions/1008268/what-do-the-following-mean-tcpra-tcpfa-tcppa-tcps-tcpsec)

- [TCP SYN (Stealth) Scan (-sS) | Nmap Network Scanning](https://nmap.org/book/synscan.html)

- [Block Well-Known TCP Attacks](https://serverfault.com/questions/245711/iptables-tips-tricks/245713#245713)

- [linux - What is MASQUERADE made for? - Super User](https://superuser.com/questions/935969/what-is-masquerade-made-for)

- [Iptables State Module - NovaOrdis Knowledge Base](https://kb.novaordis.com/index.php/Iptables_State_Module)

- [explainshell.com - iptables -A INPUT -p tcp --tcp-flags SYN,RST,ACK,FIN SYN -j ACCEPT # äquivalent zu: --syn](https://explainshell.com/explain?cmd=iptables+-A+INPUT+-p+tcp+--tcp-flags+SYN%2CRST%2CACK%2CFIN+SYN+-j+ACCEPT++%23+%C3%A4quivalent+zu%3A+--syn#)

- [Port scanning using Scapy | Infosec Resources](https://resources.infosecinstitute.com/topic/port-scanning-using-scapy/)

- [hashtaginfosec/portScan: Simple port scan scripts written in Python,](https://github.com/hashtaginfosec/portScan)

- [LayerStack Tutorials - LayerStack - How to check if TCP / UDP port is open on Linux & Windows Cloud Servers](https://www.layerstack.com/resources/tutorials/How-to-check-if-TCP-UDP-port-is-open)

- [Server Security - How to block Null Packets on a Linux Server - LopHost](https://www.lophost.com/tutorials/server-security-how-to-block-null-packets-on-a-linux-server/)
