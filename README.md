# 简单的 DDNS 脚本

由于 hub 里的各种 DDNS 脚本无法满足本人的扭曲需求，故编写此脚本：

- 奇怪的 IP 获取方式
- Boom in one
- DNSPod 分线路解析
- 超大多子域名

## 如何使用

1. 安装 Python 3
2. 拉取本项目 `git clone`
3. 安装依赖 `pip3 install -r requirements.txt`
4. 修改配置文件 `config.yaml`
5. 开润！ `python3 main.py`

## 配置

本脚本配置文件采用 `yaml` 格式：

```yaml
providers: [ ]
methods: [ ]
domains: [ ]
```

通过 `--config` 参数可以指定配置文件

```shell
python3 main.py --config ddns.yaml
```

### providers

> 在这里配置 DNS 服务商的参数

```yaml
providers:
  - name:  # 必填，provider 名称，可以乱填，不能重复
    provider:  # 可选，服务商类型，不填则引用 name，当前支持 dnspod 和 gandi 两种
    config: { }  # 必填，服务商配置
```

- DNSPod

```yaml
providers:
  - name: dnspod_demo
    provider: dnspod
    config:
      ua:  # 必填，用于请求的 User-Agent，按照官方要求，应当为 <script name>/<script version> (<your email>)
      id:  # 必填，API ID
      token:  # 必填，API Key
      user:  # 可选，子用户 ID
```

- Gandi

> 仅简单支持

```yaml
providers:
  - name: gandi
    config:
      token:  # 必填，API Token
```

### methods

> 这里配置 IP 获取方式，若目标方式无必填项，则无需配置

````yaml
methods:
  - name:  # 必填，method 名称，可以乱填，不能重复
    method:  # 可选，类型，不填则引用 name，当前支持 command curl interface requests routeros routeros-rest 六种
    config: { }  # 可选
````

- Command

> 在本地或远程执行命令
>
> ssh 内的参数将直接传递给 paramiko SSHClient 类的 connect 方法，更多参数请见官方文档
>
> *默认 10s 超时，禁用 SSH 代理，允许在 ~/.ssh 下搜索私钥*
>
> 不会对执行结果进行任何处理，故需要结果直接为 IP

```yaml
methods:
  - name: cloud
    method: cmd
    config:
      ssh: # 可选，为空则本地执行
        hostname:  # 目标地址，不可为空
        port:  # 目标端口，默认 22
        username:  # 用户名，默认为本机用户名
        password:  # 密码，用于身份校验或解锁私钥
      cmd:  # 必填，获取 IP 的指令
```

- Curl

> 间接调用 command 方式
>
> 对于 JSON 格式的返回，会尝试解析其中的 `ip` 项，否则认为返回值为 IP

```yaml
methods:
  - name: wget
    method: curl
    config:
      ssh: { }  # 可选
      url: [ ]  # 可选，覆盖内置接口，支持单个或多个链接
```

- Interface

> 通过 psutil 获取
>
> 无可配置项

```yaml
methods:
  - name: interface
```

- Requests

> 最简单的 requests

```yaml
methods:
  - name: requests
    config:
      url: [ ]  # 可选，覆盖内置接口，支持单个或多个链接
```

- RouterOS

> 间接调用 command 方式，通过 SSH 连接漏油
>
> 使用 /ip address print 获取 IP

```yaml
methods:
  - name: core-router
    method: routeros
    config:
      hostname: 192.168.88.1  # 必填
      port: 22  # 可选
      username: admin  # 可选
      password: 114514  # 可选
```

- RouterOS-REST

> RouterOS v7.1beta4 引入了 RESTful API，故本方式仅适用于 v7.1beta4+
>
> 是本人放弃适配传统 API 的直接原因（

```yaml
methods:
  - name: core-router
    method: routeros-rest
    config:
      hostname: 192.168.88.1  # 必填
      port: 443  # 可选，默认为 443，rest api 仅在 www-ssl 下开启
      username: admin  # 必填
      password: 1919810  # 必填
```

### domains

> 在这里配置子域名啥的

```yaml
domains:
  - domain: example.com  # 必填，域名
    provider: dnspod  # 必填，服务商名称
    ttl: 60  # 可选，该域名的全局 TTL，默认 600
    clean: False  # 可选，未获取到 IP 时是否清除记录，默认否
    sub:
      - name: test1.test2  # 必填，子域名
        ttl: 60  # 可选，该子域名的 TTL，覆盖域名全局 TTL
        clean: False  # 可选，覆盖域名全局设置
        records: # 可选，具体记录及获取方式
          - type: A  # 可选，记录类型，默认为 A
            line: 电信  # 可选，仅适用于 dnspod，默认为默认，当且仅当值为默认时 gandi 会进行处理
            ttl: 60  # 可选，具体线路 TTL，覆盖子域名全局 TTL
            clean: True  # 可选，覆盖子域名全局设置
            method: core-router  # 可选，方法名称，默认为 requests
            interface: pppoe  # 可选，获取 IP 的网卡，部分方式不支持：command requests
            start: "2409"  # 可选，用以筛选出特定开头的 IP，适合当一张网卡上有多个 IP 时使用
```

### 样例

```yaml
providers:
  - name: dp
    provider: dnspod
    config:
      ua: Another DDNS Service/0.0.1 (ztell@foxmail.com)
      id: 114514
      token: 1919810
  - name: gd
    provider: gandi
    config:
      token: 1919810
methods:
  - name: core
    method: routeros-rest
    config:
      hostname: 192.168.88.1
      port: 443
      username: user
      password: 1919810
  - name: secure
    method: routeros
    config:
      hostname: 192.168.88.2
      username: root
domains:
  - domain: example.net
    provider: dp
    ttl: 60
    sub:
      - name: core.router
        records:
          - type: A
            line: 默认
            method: core
            interface: pppoe-ct
          - type: A
            line: 联通
            clean: True
            method: core
            interface: pppoe-cu
      - name: ct.core.router
        records:
          - type: A
            line: 默认
            method: core
            interface: pppoe-ct
      - name: cu.core.router
        records:
          - type: A
            line: 默认
            method: core
            interface: pppoe-cu
      - name: dev
        ttl: 120
        records:
          - type: AAAA
            line: 默认
            method: curl
            start: "2408"
  - domain: example.com
    provider: gd
    sub:
      - name: naaaaaaas
        records:
          - type: A
            ttl: 300
            method: secure
            interface: wan
          - type: AAAA
            ttl: 600
            method: curl
```

## Docker

```shell
docker run -d --name ddns -v /path/to/config.yaml:/config.yaml --network host ghcr.io/ztelliot/ddns:latest
```

## 定时更新？

试试 Crontab！

> 每 5 分钟一次
>
> ```
> */5 * * * * /path/main.py --config /path/config.yaml
> ```

## Kubernetes

> 如果你碰巧有一个 Kubernetes 集群，那 CronJob 无疑是最合适的方式

参照 `cronjob.yaml` 进行修改，然后

```shell
kubectl apply -f cronjob.yaml
```
