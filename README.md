# NETCONF scripts for LNU Campus Network


BRAS 设备 IPoE 认证用户 IPv6 地址溯源程序

## 一、工作原理

本程序通过 NETCONF 协议获得 BRAS 设备 IPoE 认证用户 MAC、IPv4、IPv6 地址信息，并发送到 syslog 进行记录。可以通过 cron 每二十分钟定时执行本程序，记录用户地址信息，以供事后溯源。

本程序在 H3C SR8808-X 以及华为 ME60 上进行了测试。H3C SR8808-X IPoE 认证功能存在问题，需要关闭 IPv6 认证，目前本程序是按照关闭 IPv6 认证的情况编写的。华为 ME60 的 V800R013C00SPC100 版本软件 NETCONF 接口存在问题，无法正常获得 IPv6 地址。

## 二、开发环境

本项目使用了 PDM 设置开发环境，`src/netconf_lnu/mytest.py` 中的函数可以作为测试使用，具体命令类似如下：

```shell
pdm run netconf-lnu -c config/config.ini -t dispatch_test
```

其中 `config/config.ini` 是配置文件，可以参考 `config/config.ini.example` 来编写。

在 `src/netconf_lnu/mytest.py` 程序中的 `download_schema` 函数，能够下载网络设备的 YANG 文件，用户可以参考该测试函数编写自己的下载程序。

对于下载后的 YANG 文件，可以利用已经安装的 `pyang` 程序来浏览，命令如下：

```shell
pdm run pyang -f tree schema/huawei-bras-user-manage.yang
```

虽然可以从设备上获得 YANG 文件，但还是建议在 [Netconf Central](https://www.netconfcentral.org/) 查找并浏览。

对于程序基本功能可以通过下面命令进行测试：

```
pdm run netconf-lnu -c config/config.ini
```

## 三、打包部署

本项目可以通过 `pdm build` 命令可以打包，方便修改后部署。

项目已经在 PyPI 上发布，可以直接通过 pipx 安装，以 Debian 类系统为例，可以以 root 用户执行如下命令安装 pipx：

```
apt install pipx
cat >> ~/.bashrc << EOF

# For pipx
export PIPX_HOME=/opt/pipx
export PIPX_BIN_DIR=/usr/local/bin
EOF
```

然后重新登陆系统并安装 netconf-lnu

```
pipx install netconf-lnu
```

安装后需要建立配置文件 `/etc/netconf-lnu/config.ini` 并运行 `netconf-lnu` 命令测试。

测试无误后，可以建立 cron 配置文件 `/etc/cron.d/netconf-lnu`，每20分钟运行程序一次，其内容如下：

```shell-session
*/20 * * * * root /usr/local/bin/netconf-lnu
```



