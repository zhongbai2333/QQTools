import requests
import json
import re
import time
from mcdreforged.api.all import *
from typing import List, Dict
from wsgiref.simple_server import make_server

global httpd, config, data, help_info
__mcdr_server: PluginServerInterface
data: dict


class Config(Serializable):
    send_host: str = "127.0.0.1"
    send_port: int = 5700
    post_host: str = "0.0.0.0"
    post_port: int = 5701
    groups: List[int] = [11111111, 22222222]
    admins: List[int] = [11111111, 22222222]
    server_name: str = "Survival Server"
    main_server: bool = True
    whitelist_add_with_bound: bool = True
    why_no_whitelist: str = ""
    whitelist_remove_with_leave: bool = True
    forwards: Dict[str, bool] = {
        'mc_to_qq': False,
        'qq_to_mc': False
    }
    commands: Dict[str, bool] = {
        'list': True
    }
    mysql: Dict[str, str] = {
        'enable': "False",
        'host': "127.0.0.1",
        'port': "3306",
        'user': "root",
        'passwd': "123"
    }


@new_thread('QQListen')
def cq_listen(host: str, port: int):
    global httpd
    httpd = make_server(host, port, application)
    __mcdr_server.logger.info("Serving http on port {0}...".format(str(port)))
    httpd.serve_forever()


def application(environ, start_response):
    # 定义文件请求的类型和当前请求成功的code
    start_response('200 OK', [('Content-Type', 'application/json')])
    # environ是当前请求的所有数据，包括Header和URL，body

    request_body = environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0)))

    json_str = request_body.decode('utf-8')  # byte 转 str
    json_str = re.sub('\'', '\"', json_str)  # 单引号转双引号, json.loads 必须使用双引号
    json_dict = json.loads(json_str)  # （注意：key值必须双引号）
    if json_dict['post_type'] != 'meta_event':  # 过滤心跳数据包
        __mcdr_server.logger.info(json_dict)
        parse_msg(json_dict)  # 调用处理模块

    return ()


def on_load(server: PluginServerInterface, prev_module):
    global __mcdr_server, config, data, help_info
    __mcdr_server = server  # mcdr init
    config = server.load_config_simple(target_class=Config)  # Get Config setting
    if config.forwards['qq_to_mc']:
        help_info = '''-帮-助-菜-单-
#help 获取本条信息
#bound <ID> 绑定游戏ID
--(๑•̀ㅂ•́)و✧--'''
    else:
        help_info = '''-帮-助-菜-单-
#help 获取本条信息
#bound <ID> 绑定游戏ID
: < msg > 转发消息至游戏
--(๑•̀ㅂ•́)و✧--'''
    if config.mysql['enable'] == "False":
        data = server.load_config_simple(
            'data.json',
            default_config={'data': {}},
            echo_in_console=False
        )['data']
    cq_listen(config.post_host, config.post_port)  # 调用服务器启动模块


def on_server_startup(server: PluginServerInterface):
    if config.forwards['qq_to_mc']:  # 检测服务器是否自动转发QQ信息
        msg_start = config.server_name + ' 启动完成，服务器已启用自动转发QQ信息！'
    else:
        msg_start = config.server_name + ' 启动完成，服务器已启用手动转发QQ信息！'
    for i in config.groups:
        send_qq(i, msg_start)


def on_unload(server: PluginServerInterface):
    httpd.shutdown()
    __mcdr_server.logger.info("Http server stopping now...")
    time.sleep(0.5)


# 消息处理模块
def parse_msg(get_json):
    if get_json['message_type'] == 'group' and get_json['group_id'] in config.groups:  # 处理群聊消息
        send_id = str(get_json['user_id'])
        msg = get_json['message']
        if msg[0] == '#':  # 分辨命令消息
            send_qq(get_json['group_id'], pares_group_command(send_id, msg[1:]))  # 调用命令处理模块并返回消息
        elif not config.forwards['qq_to_mc'] and msg[0] == ':':  # 确认是否开启手动转发以及是否使用命令
            if msg[2:] != "":  # 检测命令语句是否合法
                if not str(get_json['user_id']) in data.keys():  # 检测玩家是否已绑定
                    send_qq(get_json['group_id'],
                            f"[CQ:at,qq={send_id}] 在绑定 ID 前无法互通消息，请使用 #bound <ID> 绑定游戏ID")
                else:
                    msg = msg[2:]  # 删除命令部分
                    __mcdr_server.say(f"§7[QQ][{data[send_id]}] {msg}")  # 转发消息
            else:
                send_qq(get_json['group_id'], "错误的格式，请使用 : <msg>")  # 错误提示
        else:
            if str(get_json['user_id']) in data.keys():  # 检测是否绑定且自动转发开了
                if config.forwards['qq_to_mc']:
                    __mcdr_server.say(f"§7[QQ][{data[send_id]}] {msg}")  # 转发消息
            elif not str(get_json['user_id']) in data.keys() and config.forwards['qq_to_mc'] and config.main_server:
                send_qq(get_json['group_id'], f"[CQ:at,qq={send_id}] 在绑定 ID 前无法互通消息，请使用 #bound <ID> 绑定游戏ID")
    elif get_json['message_type'] == 'private':  # 处理私聊消息
        __mcdr_server.logger.info("Private")


# 命令处理模块
def pares_group_command(send_id: str, command: str):
    command = command.split(' ')  # 解析信息为列表

    # help 命令
    if command[0] == 'help':
        return help_info

    # bound 命令
    elif command[0] == 'bound' and len(command) == 2:  # 检测 bound 命令和格式
        if send_id in data.keys():  # 检测玩家是否已经绑定
            if config.main_server:  # 确认服务器是否需要回复
                return f'[CQ:at,qq={send_id}] 您已在服务器绑定ID: {data[send_id]}, 请联系管理员修改'
        else:
            data[send_id] = command[1]  # 进行绑定
            save_data(__mcdr_server)
            if config.whitelist_add_with_bound:  # 是否添加白名单
                __mcdr_server.execute(f'whitelist add {command[1]}')
            else:
                __mcdr_server.execute(f'whitelist reload')
                if config.main_server:
                    return f'[CQ:at,qq={send_id}] 已在服务器成功绑定{config.why_no_whitelist}'
                if not config.main_server and config.why_no_whitelist != "":
                    return f'[CQ:at,qq={send_id}] {config.why_no_whitelist}'
            if config.main_server:
                return f'[CQ:at,qq={send_id}] 已在服务器成功绑定'
    elif command[0] == 'bound' and len(command) != 2:
        return '错误的格式，请使用 #bound <ID>'

    # 未知命令
    else:
        return '错误的命令，请使用 #help 获取帮助！'


# 发送消息指QQ
def send_qq(gid: int, msg: str):
    msg = msg.replace('#', '%23')
    __mcdr_server.logger.info(msg)
    requests.get(
        url='http://{0}:{1}/send_group_msg?group_id={2}&message={3}'.format(config.send_host, config.send_port, gid,
                                                                            msg))


# 保存data
def save_data(server: PluginServerInterface):
    server.save_config_simple({'data': data}, 'data.json')
