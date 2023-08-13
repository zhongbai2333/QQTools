# QQTools
**A MCDR plugin which can helps people to use QQ to manage their Minecraft Server.**

## 插件说明
QQChat的升级版本，我重写了机器人逻辑，使用go-cqhttp作为机器人，支持多服务器、Mysql数据库，增加了许多自定义config。  

有回复信息的MCDR和RCON，可供管理员无法上线的时候对服务器进行管理，对服务器自动启停的适配，可修改的自定义服务器名称等等，将来预计还会有自动项目审核、玩家指数评分等等自动化功能研发中……  

此插件我专门作为ZFS服务器插件，且我个人经验不足，请多多包涵！如有问题，可使用issues向我提交！  

## 配置说明

| 配置项 | 含义 | 默认值 | 注意事项 |
| - | - | - | - |
| `send_host` | 机器人发送端口 | `127.0.0.1` | 你的go-cqhttp机器人的HTTP地址 |
| `send_port` | 机器人发送端口 | `5700` | 你的go-cqhttp机器人的HTTP地址 |
| `post_port` | 机器人接收端口 | `0.0.0.0` | 你的go-cqhttp机器人的PostServer地址 |
| `post_port` | 机器人接收端口 | `5701` | 你的go-cqhttp机器人的PostServer地址 |
| `groups` | 群列表 | `[1234563, 1234564]` | 需要处理的群号 |
| `admins` | 管理员列表 | `[1234567, 1234568]` | 管理员的QQ号 |
| `server_name` | 服务器名 | `'Survival Server'` | 发送到qq时会加上server_name的前缀 |
| `main_server` | 是否为主服务器 | `true` | 关乎于大量命令是否会有回复 |
| `whitelist_add_with_bound` | 群成员绑定游戏 id 时自动添加白名单 | `true` | 关闭的时候可以写理由 |
| `why_no_whitelist` | 为什么服务器不会自动加白名单 | `` | 如果空着就不会有任何提示 |
| `whitelist_path` | 白名单的位置 | `./server/whitelist.json` | 如果你的server不叫server就改一个吧 |
| `whitelist_remove_with_leave` | 退群自动解绑 | `true` | 白名单和绑定都受此影响 |
| `forwards_mcdr_command` | 自动转发服务器信息的时候是否过滤MCDR命令 | `False` | 建议关了，挺危险的 |
| `forwards_server_start_and_stop` | 是否转发服务器核心启停的消息 | `true` | 有自动启停的时候挺好用的 |
| `debug` | 是否开启debug模式 | `false` | 可以在群里使用`#debug <on/off>`来临时开启或关闭 |
| `online_mode` | 是否开启正版用户名检测 | `true` | 离线服只检测玩家名是否为合法的、没有特殊字符的**不支持中文** |
| `mc_to_qq` | 是否自动转发服务器消息到QQ | `false` | 开启的时候会转发玩家进出服的消息 |
| `qq_to_mc` | 是否自动转发QQ消息到服务器 | `false` | 开启时群内用户必须绑定，不然会一直提示 |
| `mysql_enable` | 是否启用MySQL支持 | `false` | 需安装`mysql-connector-python`包 |
| `mysql_config` | MySQL的设置 | `略` | 数据库的权限必须分配给这个用户**不要使用root用户，危险！** |
| `to_mcdr` | 设置 执行MCDR命令功能 的命令名称 | `tomcdr` | `#admin_help`内会自动修改，群组服建议使用不同的命令 |
| `to_minecraft` | 设置 执行RCON命令功能 的命令名称 | `togame` | `#admin_help`内会自动修改，群组服建议使用不同的命令 |


## 命令帮助

> 普通群聊命令帮助如下

`#help` 获取帮助信息

`#list` 获取在线玩家列表

`#bound <ID>` 绑定游戏ID

`#admin_help` 管理员帮助菜单（**仅管理员可执行**）

`: <msg>` 发送消息至服务器（**仅在启动了手动转发命令至服务器时可见**）

> 管理员群聊命令帮助如下

`#admin_help` 获取管理员信息

`#【自定义】（配置文件内的"to_mcdr"选项）` 使用MCDR命令(**默认为`tomcdr`**)

`#【自定义】（配置文件内的"to_minecraft"选项）` 使用Minecraft命令(**默认为`togame`**)

`#debug <on/off>` 临时开启或关闭debug模式

`#debug_json <all/no_heart/stop>` 测试Json数据包（**仅在配置文件Debug模式启动的时候可见（命令Debug启用后也可正常执行）**）

> 普通私聊命令帮助如下

`#help` 获取本条信息
    
`#list` 获取在线玩家列表

> 管理员私聊命令帮助如下(**仅管理员可见\可用**)

`#help` 获取本条信息

`#list` 获取在线玩家列表

`#bound` 绑定相关帮助列表

`#【自定义】（配置文件内的"to_mcdr"选项）` 使用MCDR命令(**默认为`tomcdr`**)

`#【自定义】（配置文件内的"to_minecraft"选项）` 使用Minecraft命令(**默认为`togame`**)

> bound 私聊命令帮助如下(**仅管理员可见\可用**)

`#bound list` 查看绑定列表

`#bound check <qq/player> <ID>` 查询绑定信息

`#bound unbound <qq/player> <ID>` 解除绑定

懒得写英语了哈哈哈(๑•̀ㅂ•́)و✧
