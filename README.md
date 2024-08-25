# 群晖阿里云DDNS

<br />
<p align="center">
  <h3 align="center">群晖阿里云DDNS插件</h3>
  <p align="center">
    实现了一个阿里DNS在本地运行的DDNS插件！
    <br />
  </p>
</p>

## 目录

- [上手指南](#上手指南)
  - [开发前的配置要求](#开发前的配置要求)
  - [安装步骤](#安装步骤)
- [文件目录说明](#文件目录说明)

### 上手指南

###### 开发前的配置要求

1. 开启群晖SSH，并登录切换到root账号
2. 一个阿里云域名，需要提前创建好子域名：aaa.xxxx.com 记录类型A；需要更新IPv6功能，还需要创建aaa.xxxx.com 记录类型AAAA
3. 阿里云控制台配置访问控制账号(AccessKey&AccessSecret)

###### **安装步骤**
1. 安装插件
```sh
$ cp aliyun_dns.py /usr/syno/bin/ddns/aliyun.py
$ chmod +x /usr/syno/bin/ddns/aliyun.py
$ cat << EOF >> /etc.defaults/ddns_provider.conf
[Aliyun]
    modulepath=/usr/syno/bin/ddns/aliyun.py
    queryurl=https://www.aliyun.com
EOF
```
2. 配置运行
 进入群晖控制面板/外部访问/DDNS - 新增配置
 - 服务供应商: Aliyun
 - 主机名：aaa.xxxx.com
 - 用户名：xxxxxxxxxxxx（AccessKey ）
 - 密码：ssssssssssssssssddddd（AccessSecret）
 - 外部地址：自动
点测试联机，如果一切正常会变绿，点确定保存。

### 文件目录说明
eg:

```
filetree 
├── aliyun_dns.py
├── aliyun_setup.py
├── setup.sh
├── README.md
```
