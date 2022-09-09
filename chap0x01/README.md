# 基于VirtualBox的网络攻防基础环境搭建

## 实验环境

- Host Machine

  - Windows 11 22H2 build 22622.590

- Virtual Machine Platform

  - VirtualBox 6.1.38 r153438

- Guest Machine

  - Attacker:
  
    - attacker-kali: Kali 2022.3 kali-rolling

  - Gateway:
  
    - gateway-debian: Debian 10 buster

  - Victim:

    - victim-kali: Kali 2022.3 kali-rolling

    - victim-xp-1: Windows xp 5.1 build 2600.xpsp.080413-2111:ServicePack3

    - victim-debian: Debian 10 buster

    - victim-xp-2: Windows xp 5.1 build 2600.xpsp.080413-2111:ServicePack3

## 实验要求

- [x] 虚拟硬盘配置成多重加载，效果如下图所示：

  ![image](./img/vb-multi-attach.png)

- [x] 搭建满足如下拓扑图所示的虚拟机网络拓扑

  ![image](./img/vb-exp-layout.png)

- 完成以下网络连通性测试：

  - [x] 靶机可以直接访问攻击者主机

  - [x] 攻击者主机无法直接访问靶机

  - [x] 网关可以直接访问攻击者主机和靶机

  - [x] 靶机的所有对外上下行流量必须经过网关

  - [x] 所有节点均可以访问互联网

## 实验过程记录

### Guest Machine Configuration

#### Multiattach Set Up

首先从来没有听说过`多重加载`这个名词，真白玩了那么久虚拟机，由于不确定翻译于是用直接咕咕噜中文`virtualbox 多重加载`，然后通过某个搜索结果进入的博客转载网站找到了CSDN的原文😓，了解了一下操作流程，大致分为以下两步：

1. 在VirtualBox菜单栏中的`管理`>`虚拟介质管理`中找到目标介质

2. 选中目标介质，如果介质已被分配则需要先点击`释放`，此时会提醒将介质从添加到的虚拟机移除，确认后再点击`属性`切换出窗口下方的属性页面，在`类型`选单内选择多重加载后在右下角点击应用即可；如果没有被分配则直接可以在属性页面内直接选择类型并应用

如是进行操作之后很轻松地将攻击者主机、网关和4台靶机的磁盘配置了多重加载，效果如下图所示：

![screenShot](./img/kaliMultiattach.png)

![screenShot](./img/debianMultiattach.png)

![screenShot](./img/xpMultiattach.png)

显然我们有6台虚拟机但只放了3张截图，主要是考虑到多重加载的特性，CSDN的那篇文章说实话我没看太懂，但大概理解到多重加载的意思就是

>可以使此类型的磁盘介质拥有“在某个时间点上，被新建的相同系统的虚拟机直接使用，便可复制出这个时间点上的旧的相同系统的虚拟机”的能力

说白了有点像树，多重加载的磁盘介质每被新建的虚拟机直接引用就会多一个当前时间点的子节点🤔

所以剩余的相同系统均是由同一磁盘介质复制出来的，自然也不需要那么多截图（自信）

讲道理万一错了就很尴尬😂，所以为了保险起见我专门去查了VirtualBox的文档，而里面的解释通俗易懂，恰好是我理解的意思，原文是这样说的：

>Multiattach mode images can be attached to more than one virtual machine at the same time, even if these machines are running simultaneously. For each virtual machine to which such an image is attached, a differencing image is created. As a result, data that is written to such a virtual disk by one machine is not seen by the other machines to which the image is attached. Each machine creates its own write history of the multiattach image.

就不翻译了，总之我理解的没错，同时再吐槽一下CSDN上的文章真的一言难尽

#### 虚拟机网络拓扑搭建

这里其实不太难理解，在完成上一步的内容时已经就顺手把网卡给分配了，还是按图说话：

![image](./img/vb-exp-layout.png)

首先图片里面有两个`内部网络`，里面分别有两台系统不一样的靶机，我没有擅自修改太多，直接照着图进行摆放，感觉有点像用复杂化的Packet Tracer，只能通过手动设置网卡来划分子网的那种🤔

图上左侧黄色部分的`Internal Network 1`我在VirtualBox网卡配置时给的名称为`intnet0`，右上侧灰色的`Internal Network 2`则是被我配置为`intnet1`，两个内部网络中的靶机分别仅配置一张`内部网络`连接方式的网卡，网络名称分别设置为对应内网的名称，于是两个内网首先设置完毕

然后是网关部分，上课时快速记忆下来了网关所需的4张网卡的配置方式，这里直接配置：

- 网卡1：NAT连接方式，用于连接外网

- 网卡2：Host-Only网络，用于宿主机SSH连接

- 网卡3：内部网络`intnet0`，用于路由`Internal Network 1`

- 网卡4：内部网络`intnet1`，用于路由`Internal Network 2`

最后是攻击者主机部分，这个显然是只连接了外网所以只需要配置一张NAT方式的网卡即可

这里其实有一点`散装黑盒`的意思：由于直接导入使用了老师提供的磁盘介质，整个系统的安装与配置过程并不是由我完成，在完成这部分配置的过程中我所出的力仅在于`新建虚拟机`+`按需设置网卡`，而关于网关设备`gateway-debian`系统内最初的网卡硬件固定IP地址分配与两个内网对于外网攻击者`attacker-kali`的屏蔽分流两部分内容则是没有在意，磁盘介质完全是被当作黑盒直接拿来使用了😂

配置完成之后这里分别放上6台虚拟机的系统内IP配置，应该就足以说明网络的配置情况了：

Virtual Machine|IP Configuration
:-:|:-:
attacker-kali|![screenShot](./img/attackerKaliIP.png)
gateway-debian|![screenShot](./img/gatewayDebianIP.png)
victim-kali|![screenShot](./img/victimKaliIP.png)
victim-xp-1|![screenShot](./img/victimXP1IP.png)
victim-debian|![screenShot](./img/victimDebianIP.png)
victim-xp-2|![screenShot](./img/victimXP2IP.png)

### 网络连通性目标要求实现

众所周知：

>连通性=能`ping`通

所以以下的连通性相关目标测试均通过这条古老但是有效的命令实现

#### 靶机可以直接访问攻击者主机

翻译一下，需要4台靶机能ping通攻击者主机`attacker-kali`

首先从上一步的操作中得知`attacker-kali`的IP地址是`10.0.2.15`，由于Windows系统默认只执行4次ping包发送，于是计划在4台靶中的Linux机器中执行ping命令时也添加`-c 4`来限制ping次数

(电脑死机了，到这里是之前写的内容，好多证明用的虚拟机状态无了，晚点再继续写)

#### 攻击者主机无法直接访问靶机

#### 网关可以直接访问攻击者主机和靶机

#### 靶机的所有对外上下行流量必须经过网关

#### 所有节点均可以访问互联网

## 总结

## 参考链接

- [Virtualbox 多重加载 高级功能介绍](https://blog.csdn.net/Jeanphorn/article/details/45056251)

- [Chapter 5. Virtual Storage](https://www.virtualbox.org/manual/ch05.html)
