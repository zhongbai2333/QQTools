from typing import List, Dict

import json
import re
import requests
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from .MySQL_Control import (connect_and_query_db, create_table_if_not_exists, connect_and_insert_db,
                            connect_and_delete_data)
from mcdreforged.api.all import *

global httpd, config, data, help_info, online_players, admin_help_info, answer, mysql_use, server_status, wait_list
global debug_json_mode, help_private_info, admin_help_private_info, bound_help
__mcdr_server: PluginServerInterface
data: dict
try:  # 试图导入mysql处理
    import mysql.connector
except ImportError:
    mysql = None


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
    whitelist_path: str = "./server/whitelist.json"
    whitelist_remove_with_leave: bool = True
    forwards_mcdr_command: bool = True
    forwards_server_start_and_stop: bool = True
    debug: bool = False
    online_mode: bool = True
    auto_forwards: Dict[str, bool] = {
        'mc_to_qq': False,
        'qq_to_mc': False
    }
    mysql_enable: bool = False
    mysql_config: Dict[str, str] = {
        'host': "127.0.0.1",
        'port': "3306",
        'database': "MCDR_QQTools",
        'user': "root",
        'password': "123"
    }
    admin_commands: Dict[str, str] = {
        'to_mcdr': "tomcdr",
        'to_minecraft': "togame"
    }


# 初始化帮助信息
def initialize_help_info():
    global help_info, admin_help_info, help_private_info, admin_help_private_info, bound_help
    if config.auto_forwards['qq_to_mc']:
        help_info = '''-帮-助-菜-单-
    #help 获取本条信息
    #list 获取在线玩家列表
    #bound <ID> 绑定游戏ID
    #admin_help 管理员帮助菜单
--(๑•̀ㅂ•́)و✧--'''
    elif not config.auto_forwards['qq_to_mc']:
        help_info = '''-帮-助-菜-单-
    #help 获取本条信息
    #list 获取在线玩家列表
    #bound <ID> 绑定游戏ID
    #admin_help 管理员帮助菜单
    : <msg> 转发消息至游戏
--(๑•̀ㅂ•́)و✧--'''
    if config.debug:
        admin_help_info = f'''管理员·帮助菜单
    #{config.admin_commands['to_mcdr']} 使用MCDR命令
    #{config.admin_commands['to_minecraft']} 使用Minecraft命令
    #debug_json <all/no_heart/stop> 测试Json数据包
    #debug 开发通用触发器
--(๑•̀ㅂ•́)و✧--'''
    else:
        admin_help_info = f'''管理员·帮助菜单
    #{config.admin_commands['to_mcdr']} 使用MCDR命令
    #{config.admin_commands['to_minecraft']} 使用Minecraft命令
--(๑•̀ㅂ•́)و✧--'''
    help_private_info = f'''{config.server_name}·私聊·帮助菜单
    #help 获取本条信息
    #list 获取在线玩家列表
--(๑•̀ㅂ•́)و✧--'''
    admin_help_private_info = f'''{config.server_name}·私聊·帮助菜单·管理特供
    #help 获取本条信息
    #list 获取在线玩家列表
    #bound 绑定相关帮助列表
    #{config.admin_commands['to_mcdr']} 使用MCDR命令
    #{config.admin_commands['to_minecraft']} 使用Minecraft命令
--(๑•̀ㅂ•́)و✧--'''
    bound_help = f'''{config.server_name}·私聊·帮助菜单·bound
    #bound list 查看绑定列表
    #bound check <qq/player> <ID> 查询绑定信息
    #bound unbound <qq/player> <ID> 解除绑定
--(๑•̀ㅂ•́)و✧--'''


# -------------------------
# WebServer event listener
# -------------------------


@new_thread('QQListen')
def cq_listen(host: str, port: int):
    global httpd
    # 设置服务器地址和端口
    server_address = (host, port)
    httpd = HTTPServer(server_address, MyRequestHandler)
    __mcdr_server.logger.info("Serving http on port {0}...".format(str(port)))
    httpd.serve_forever()


# 自定义请求处理器类
class MyRequestHandler(BaseHTTPRequestHandler):
    def log_request(self, code='-', size='-'):
        # 重写log_request方法，取消日志打印
        pass

    def do_POST(self):
        # 设置响应头
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        # 读取请求数据
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        json_str = post_data.decode('utf-8')  # byte 转 str
        json_str = re.sub('\'', '\"', json_str)  # 单引号转双引号, json.loads 必须使用双引号
        json_dict = json.loads(json_str)  # （注意：key值必须双引号）
        if debug_json_mode == 1:
            send_group_qq(config.groups[0], str(json_dict))
        elif debug_json_mode == 2:
            if json_dict['post_type'] == 'meta_event':
                if json_dict['meta_event_type'] != 'heartbeat':
                    send_group_qq(config.groups[0], str(json_dict))
            elif json_dict['post_type'] == 'message':
                send_group_qq(config.groups[0], str(json_dict))
            elif json_dict['post_type'] == 'notice':
                send_group_qq(config.groups[0], str(json_dict))
        if json_dict['post_type'] == 'message':  # 过滤message数据包
            parse_msg(json_dict)  # 调用处理模块
        elif json_dict['post_type'] == 'notice':  # 过滤notice数据包
            join_and_leave_group(json_dict)
        try:
            # 处理请求数据
            data_post = json.loads(post_data)
            response_data = {"message": "Success", "received_data": data_post}
        except json.JSONDecodeError:
            response_data = {"message": "Invalid JSON"}

        # 发送响应
        self.wfile.write(json.dumps(response_data).encode('utf-8'))


# -------------------------
# MCDR event listener
# -------------------------


def on_load(server: PluginServerInterface, prev_module):
    global __mcdr_server, config, data, help_info, online_players, admin_help_info, wait_list, debug_json_mode
    __mcdr_server = server  # mcdr init
    config = server.load_config_simple(target_class=Config)  # Get Config setting
    initialize_help_info()
    wait_list = []
    online_players = []
    debug_json_mode = 0

    if not config.auto_forwards['mc_to_qq']:
        server.register_help_message(': <msg>', '向QQ群发送消息')
        server.register_command(
            Literal(':')
            .then(
                GreedyText('message').runs(command_qq)
            )
        )

    if not config.mysql_enable:
        data = server.load_config_simple(
            'data.json',
            default_config={'data': {}},
            echo_in_console=False
        )['data']

    source = __mcdr_server.get_plugin_command_source()
    __mcdr_server.logger.info(source)

    if not config.mysql_enable:  # 未开启mysql功能
        cq_listen(config.post_host, config.post_port)  # 调用监听服务器启动模块
    elif config.mysql_enable and mysql:  # 启用mysql功能且mysql-connector-python已安装
        MySQL_Control.create_table_if_not_exists("user_list", "id INT AUTO_INCREMENT PRIMARY KEY,qq_id VARCHAR(15),"
                                                              "player_id VARCHAR(20),event_time TIMESTAMP DEFAULT "
                                                              "CURRENT_TIMESTAMP", config.mysql_config)
        __mcdr_server.logger.info("MySQL数据库功能已正常启动！")
        cq_listen(config.post_host, config.post_port)  # 调用监听服务器启动模块
    elif config.mysql_enable and not mysql:
        __mcdr_server.logger.info("QQTools无法启动，请安装mysql-connector-python或关闭数据库功能！")


def on_server_startup(server: PluginServerInterface):
    global server_status
    server_status = True
    if wait_list:  # 服务器核心重启后处理堆积命令
        for i in wait_list:
            send_execute_mc(i)
    if config.mysql_enable and config.whitelist_add_with_bound:
        db_player_list = connect_and_query_db("player_id", "user_list", config.mysql_config)
        result_list = [element for tup in db_player_list for element in tup]
        if config.debug:
            __mcdr_server.logger.info(f"UserList: {result_list}")
            __mcdr_server.logger.info(f"WhiteList: {get_whitelist()}")
        diff_player = get_diff_list(  # 检查数据库有没有新的玩家
            result_list,
            get_whitelist()
        )
        if diff_player:
            for i in diff_player:
                __mcdr_server.logger.info(f"New Player! Name:{i}")
                send_execute_mc(f'whitelist add {i}')  # 加一下新玩家

        diff_player = get_diff_list(  # 检查数据库有没有老的玩家
            get_whitelist(),
            result_list
        )
        if diff_player:
            for i in diff_player:
                __mcdr_server.logger.info(f"Wrong Player! Name:{i}")
                send_execute_mc(f'whitelist remove {i}')  # 删一下老玩家

    if config.forwards_server_start_and_stop:
        if config.auto_forwards['qq_to_mc']:  # 检测服务器是否自动转发QQ信息
            msg_start = config.server_name + ' 启动完成，服务器已启用自动转发QQ信息！'
        else:
            msg_start = config.server_name + ' 启动完成，服务器已启用手动转发QQ信息！'
        for i in config.groups:
            send_group_qq(i, msg_start)


def on_server_stop(server: PluginServerInterface, server_return_code: int):
    global server_status
    server_status = False
    if config.forwards_server_start_and_stop:
        msg_stop = config.server_name + ' 服务器核心已关闭！'
        for i in config.groups:
            send_group_qq(i, msg_stop)


def on_unload(server: PluginServerInterface):
    __mcdr_server.logger.info("Http server stopping now...")
    time.sleep(0.5)


# 在线玩家检测
def on_player_joined(server, player, info):
    if player not in online_players:
        online_players.append(player)
    if config.auto_forwards['mc_to_qq']:
        for i in config.groups:
            send_group_qq(i, f'{player} joined the game')
    if config.auto_forwards['mc_to_qq']:  # 自动提醒
        time.sleep(0.5)
        __mcdr_server.tell(player, "QQTools提醒您，服务器已启用自动转发MC消息！")
    else:
        time.sleep(0.5)
        __mcdr_server.tell(player, "QQTools提醒您，服务器已启用手动转发MC消息！")


def on_player_left(server, player):
    if player in online_players:
        online_players.remove(player)
    if config.auto_forwards['mc_to_qq']:
        for i in config.groups:
            send_group_qq(i, f'{player} left the game')


# 自动转发到QQ
def on_user_info(server: PluginServerInterface, info):
    if info.is_player and config.auto_forwards['mc_to_qq']:
        msg = info.content
        if config.forwards_mcdr_command:
            for i in config.groups:
                send_group_qq(i, f'[{info.player}] {info.content}')
        else:
            if msg[0:2] != '!!':
                for i in config.groups:
                    send_group_qq(i, f'[{info.player}] {info.content}')


# -------------------------
# Message parse listener
# -------------------------


# 手动命令转发到QQ
def command_qq(src, ctx):
    player = src.player if src.is_player else 'Console'
    for i in config.groups:
        send_group_qq(i, f'[{player}] {ctx["message"]}')


# 消息处理模块
def parse_msg(get_json):
    if get_json['message_type'] == 'group' and get_json['group_id'] in config.groups:  # 处理群聊消息
        send_id = str(get_json['user_id'])
        msg = get_json['message']
        if msg[0] == '#':  # 分辨命令消息
            send_group_qq(get_json['group_id'], pares_group_command(send_id, msg[1:]))  # 调用命令处理模块并返回消息
        elif not config.auto_forwards['qq_to_mc'] and msg[0] == ':':  # 确认是否开启手动转发以及是否使用命令
            if msg[2:] != "":  # 检测命令语句是否合法
                user_list = get_user_list()
                if not str(get_json['user_id']) in user_list.keys():  # 检测玩家是否已绑定
                    send_group_qq(get_json['group_id'],
                                  f"[CQ:at,qq={send_id}] 在绑定 ID 前无法互通消息，请使用 #bound <ID> 绑定游戏ID")
                else:
                    __mcdr_server.say(f"§7[QQ][{user_list[send_id]}] {msg[2:]}")  # 删除命令部分并转发消息
            else:
                send_group_qq(get_json['group_id'], "错误的格式，请使用 : <msg>")  # 错误提示
        elif config.auto_forwards['qq_to_mc']:
            user_list = get_user_list()
            if str(get_json['user_id']) in user_list.keys():  # 检测是否绑定
                __mcdr_server.say(f"§7[QQ][{user_list[send_id]}] {msg}")  # 转发消息
            elif not str(get_json['user_id']) in data.keys() and config.main_server:
                send_group_qq(get_json['group_id'],
                              f"[CQ:at,qq={send_id}] 在绑定 ID 前无法互通消息，请使用 #bound <ID> 绑定游戏ID")
    elif get_json['message_type'] == 'private':  # 处理私聊消息
        send_id = str(get_json['user_id'])
        msg = get_json['message']
        if msg[0] == '#':  # 分辨命令消息
            send_private_qq(get_json['user_id'], pares_private_command(send_id, msg[1:]))  # 调用命令处理模块并返回消息
        else:
            send_private_qq(get_json['user_id'], "你有什么事嘛^_^")


# 进出群处理
def join_and_leave_group(get_json):
    send_id = str(get_json['user_id'])
    if get_json['notice_type'] == 'group_increase':  # 进群处理
        if config.auto_forwards['qq_to_mc']:  # 是否已开启自动转发
            send_group_qq(get_json['group_id'],
                          f"[CQ:at,qq={send_id}] 在绑定 ID 前无法互通消息，请使用 #bound <ID> 绑定游戏ID，注：服务器将自动把群消息同步至服务器聊天栏")
        else:
            send_group_qq(get_json['group_id'],
                          f"[CQ:at,qq={send_id}] 在绑定 ID 前无法互通消息，请使用 #bound <ID> 绑定游戏ID，注：服务器需使用命令: <msg>把群消息同步至服务器聊天栏")
    elif get_json['notice_type'] == 'group_decrease':  # 退群处理
        user_list = get_user_list()
        if config.whitelist_remove_with_leave:  # 是否自动删除白名单
            if send_id in user_list.keys():  # 确认是否绑定过
                send_execute_mc(f'whitelist remove {user_list[send_id]}')
                send_group_qq(get_json['group_id'], f'{user_list[send_id]}({send_id}) 已退群，已在服务器移除他的白名单')
                delete_user(send_id)
            else:
                send_group_qq(get_json['group_id'], f'{send_id} 已退群，此人未在服务器绑定')
        else:
            if send_id in user_list.keys():
                send_group_qq(get_json['group_id'], f'{user_list[send_id]}({send_id}) 已退群')
                delete_user(send_id)
            else:
                send_group_qq(get_json['group_id'], f'{send_id} 已退群，此人未在服务器绑定')


# 私聊命令处理模块
def pares_private_command(send_id: str, command: str):
    command = command.split(' ')

    # help 命令
    if command[0] == 'help':
        if send_id in send_id in str(config.admins):
            return admin_help_private_info
        else:
            return help_private_info

    # list 命令
    elif command[0] == 'list':
        return f"{config.server_name} 在线玩家共{len(online_players)}人，" \
                f"玩家列表: {', '.join(online_players)}"

    # bound 命令
    elif command[0] == 'bound' and 1 < len(command) < 5:
        if send_id in str(config.admins):
            user_list = get_user_list()
            # list 命令
            if command[1] == 'list' and len(command) == 2:
                bound_list = [f'{a} - {b}' for a, b in user_list.items()]
                reply_msg = ''
                for i in range(0, len(bound_list)):
                    reply_msg += f'{i + 1}. {bound_list[i]}\n'
                reply_msg = '还没有人在生存服绑定' if reply_msg == '' else reply_msg
                return reply_msg
            elif command[1] == 'list' and len(command) != 2:
                return '错误的格式，请使用 #bound list'
            # check 命令
            elif command[1] == 'check' and len(command) == 4:
                if command[2] == 'qq':
                    if command[3] in user_list.keys():
                        return f'已为您查询到： {user_list[command[3]]}({command[3]})'
                    else:
                        return f'无法查询到此人！（{command[3]}）'
                elif command[2] == 'player':
                    if command[3] in user_list.values():
                        player_id_qq = list(user_list.keys())[list(user_list.values()).index(command[3])]
                        return f'已为您查询到： {command[3]}({player_id_qq})'
                    else:
                        return f'无法查询到此人！（{command[3]}）'
                else:
                    return '错误的格式，请使用 #bound check <qq/player> <ID>'
            elif command[1] == 'check' and len(command) != 4:
                return '错误的格式，请使用 #bound check <qq/player> <ID>'
            # unbound 命令
            elif command[1] == 'unbound' and len(command) == 4:
                if command[2] == 'qq':
                    if command[3] in user_list.keys():
                        if config.whitelist_add_with_bound:
                            player_name = user_list[command[3]]
                            send_execute_mc(f'whitelist remove {player_name}')
                            delete_user(command[3])
                            return f'已删除 {player_name}({command[3]}) 的绑定并自动解除了白名单'
                        else:
                            player_name = user_list[command[3]]
                            delete_user(command[3])
                            return f'已删除 {player_name}({command[3]}) 的绑定'
                    else:
                        return f'未找到该玩家，该玩家不存在或未绑定！({command[3]})'
                if command[2] == 'player':
                    if command[3] in user_list.values():
                        player_id_qq = list(user_list.keys())[list(user_list.values()).index(command[3])]
                        if config.whitelist_add_with_bound:
                            send_execute_mc(f'whitelist remove {command[3]}')
                            delete_user(player_id_qq)
                            return f'已删除 {command[3]}({player_id_qq}) 的绑定并自动解除了白名单'
                        else:
                            delete_user(player_id_qq)
                            return f'已删除 {command[3]}({player_id_qq}) 的绑定'
                    else:
                        return f'未找到该玩家，该玩家不存在或未绑定！({command[3]})'
                else:
                    return '错误的格式，请使用 #bound unbound <qq/player> <ID>'
            elif command[1] == 'unbound' and len(command) != 4:
                return '错误的格式，请使用 #bound unbound <qq/player> <ID>'
        else:
            return '抱歉您不是管理员，无权使用该命令！'
    elif command[0] == 'bound' and not 1 < len(command) < 5:
        return bound_help

    # tomcdr 命令
    elif command[0] == config.admin_commands['to_mcdr'] and len(command) >= 2:
        if send_id in str(config.admins):
            global answer
            user_list = get_user_list()
            answer = None
            __mcdr_server.logger.info(f"[{user_list[send_id]}] >> {' '.join(command[1:])}")
            __mcdr_server.execute_command(' '.join(command[1:]), RobotCommandSource("QQBot"))
            if answer:
                __mcdr_server.logger.info(answer)
                return str(answer)
            else:
                return "命令错误或没有回复！"
        else:
            return '抱歉您不是管理员，无权使用该命令！'
    elif command[0] == config.admin_commands['to_mcdr'] and len(command) < 2:
        return '错误的格式，请使用 #tomcdr <command>'

    # togame 命令
    elif command[0] == config.admin_commands['to_minecraft'] and len(command) >= 2:
        if send_id in str(config.admins):
            return rcon_execute(' '.join(command[1:]))
        else:
            return '抱歉您不是管理员，无权使用该命令！'
    elif command[0] == config.admin_commands['to_minecraft'] and len(command) < 2:
        return '错误的格式，请使用 #tomcdr <command>'

    # 未知命令
    else:
        return '错误的命令，请使用 #help 获取帮助！'


# 群命令处理模块
def pares_group_command(send_id: str, command: str):
    command = command.split(' ')  # 解析信息为列表

    # help 命令
    if command[0] == 'help' and config.main_server:
        return help_info

    # admin_help 命令
    elif command[0] == 'admin_help' and config.main_server:
        if send_id in str(config.admins):
            return admin_help_info
        else:
            return '抱歉您不是管理员，无权使用该命令！'

    # list 命令
    elif command[0] == 'list':
        return f"{config.server_name} 在线玩家共{len(online_players)}人，" \
               f"玩家列表: {', '.join(online_players)}"

    # bound 命令
    elif command[0] == 'bound' and len(command) == 2 and \
            not (not config.main_server and config.mysql_enable):  # 检测 bound 命令和格式
        user_list = get_user_list()
        if send_id in user_list.keys():  # 检测玩家是否已经绑定
            if config.main_server:  # 确认服务器是否需要回复
                return f'[CQ:at,qq={send_id}] 您已在服务器绑定ID: {user_list[send_id]}, 请联系管理员修改'
        elif command[1] in user_list.values():  # 查看id是否已存在
            if config.main_server:  # 确认服务器是否需要回复
                player_id_qq = list(user_list.keys())[list(user_list.values()).index(command[1])]
                return f'[CQ:at,qq={send_id}] ID：{command[1]} 已被 [CQ:at,qq={player_id_qq}] 在服务器绑定, 请联系管理员修改'
        else:
            if real_name(command[1]) or not config.online_mode:
                if send_user_list(send_id, command[1]):  # 进行绑定
                    if config.whitelist_add_with_bound:  # 是否添加白名单
                        send_execute_mc(f'whitelist add {command[1]}')
                        if config.main_server:
                            return f'[CQ:at,qq={send_id}] 已在服务器成功绑定并为您自动获取白名单'
                    else:
                        send_execute_mc(f'whitelist reload')
                        if config.main_server:
                            return f'[CQ:at,qq={send_id}] 已在服务器成功绑定{config.why_no_whitelist}'
                        elif not config.main_server and config.why_no_whitelist != "":
                            return f'[CQ:at,qq={send_id}] {config.why_no_whitelist}'
                    if config.main_server:
                        return f'[CQ:at,qq={send_id}] 已在服务器成功绑定'
                else:
                    return f'[CQ:at,qq={send_id}] 不合法的用户名！'
            else:
                return f'[CQ:at,qq={send_id}] 玩家名不存在！'
    elif command[0] == 'bound' and len(command) != 2:
        if config.main_server:  # 确认是否需要回复
            return '错误的格式，请使用 #bound <ID>'

    # tomcdr 命令
    elif command[0] == config.admin_commands['to_mcdr'] and len(command) >= 2:
        if send_id in str(config.admins):
            global answer
            user_list = get_user_list()
            answer = None
            __mcdr_server.logger.info(f"[{user_list[send_id]}] >> {' '.join(command[1:])}")
            __mcdr_server.execute_command(' '.join(command[1:]), RobotCommandSource("QQBot"))
            if answer:
                __mcdr_server.logger.info(answer)
                return str(answer)
            else:
                return "命令错误或没有回复！"
        else:
            return '抱歉您不是管理员，无权使用该命令！'
    elif command[0] == config.admin_commands['to_mcdr'] and len(command) < 2:
        if config.main_server:  # 确认是否需要回复
            return '错误的格式，请使用 #tomcdr <command>'

    # togame 命令
    elif command[0] == config.admin_commands['to_minecraft'] and len(command) >= 2:
        if send_id in str(config.admins):
            return rcon_execute(' '.join(command[1:]))
        else:
            return '抱歉您不是管理员，无权使用该命令！'
    elif command[0] == config.admin_commands['to_minecraft'] and len(command) < 2:
        return '错误的格式，请使用 #tomcdr <command>'

    # debug_json 命令
    elif command[0] == 'debug_json' and config.debug and send_id in str(config.admins):
        global debug_json_mode
        if len(command) < 2:
            return '错误的命令，格式为#debug_json <all/no_heart/stop>'
        elif command[1] == "all":
            debug_json_mode = 1
            return 'Json测试开启，模式：全部Json'
        elif command[1] == "no_heart":
            debug_json_mode = 2
            return 'Json测试开启，模式：无心跳数据包'
        elif command[1] == "stop":
            debug_json_mode = 0
            return 'Json测试关闭'
        else:
            return '错误的命令，格式为#debug_json <all/no_heart/stop>'
    elif command[0] == 'debug_json' and config.debug and send_id not in str(config.admins):
        return '抱歉您不是管理员，无权使用该命令！'

    # debug 命令 作为测试触发器使用
    elif command[0] == 'debug' and config.debug and send_id in str(config.admins):
        return "1\n2\n3"
    elif command[0] == 'debug' and config.debug and send_id not in str(config.admins):
        return '抱歉您不是管理员，无权使用该命令！'

    # 未知命令
    else:
        return '错误的命令，请使用 #help 获取帮助！'


# 发送群聊消息至QQ
def send_group_qq(gid: int, msg: str):
    if msg:
        msg = msg.replace('#', '%23')
        if config.debug:
            __mcdr_server.logger.info(msg)
        requests.get(
            url='http://{0}:{1}/send_group_msg?group_id={2}&message={3}'.format(config.send_host, config.send_port, gid,
                                                                                msg))


# 发送私聊消息至QQ
def send_private_qq(uid: int, msg: str):
    msg = msg.replace('#', '%23')
    if config.debug:
        __mcdr_server.logger.info(msg)
    requests.get(
        url='http://{0}:{1}/send_private_msg?user_id={2}&message={3}'.format(config.send_host, config.send_port, uid,
                                                                             msg))


# 把命令执行独立出来，以防服务器处在待机状态
def send_execute_mc(command: str):
    if server_status:  # 确认服务器是否启动
        __mcdr_server.execute(command)
    else:
        wait_list.append(command)  # 堆着等开服


# RCON相关
def rcon_execute(command: str):
    if __mcdr_server.is_rcon_running():
        result = __mcdr_server.rcon_query(command)
        if result == '':
            result = '该指令没有返回值'
    else:
        __mcdr_server.execute(command)
        result = '由于未启用 RCON，没有返回结果'
    return result


# 获取白名单
def get_whitelist():
    name_list = []
    with open(config.whitelist_path, 'r', encoding='utf8') as fp:
        json_data = json.load(fp)
        for i in json_data:
            name_list.append(i['name'])
        return name_list


# 保存data
def save_data(server: PluginServerInterface):
    server.save_config_simple({'data': data}, 'data.json')


# 集合处理
def get_diff_list(set1: list, set2: list):
    if set1 and set2:
        set1 = set(set1)
        set2 = set(set2)
        diff = set1 - set2
        return list(diff)
    return None


# 整合获取用户
def get_user_list():
    if config.mysql_enable:
        return dict(connect_and_query_db("qq_id,player_id", "user_list", config.mysql_config))
    else:
        return data


# 整合删除用户
def delete_user(send_id: str):
    if config.mysql_enable:
        if config.main_server:
            connect_and_delete_data("user_list", f"qq_id = {send_id}", config.mysql_config)
    else:
        del data[send_id]
        save_data(__mcdr_server)


# 整合绑定用户
def send_user_list(send_id: str, name: str):
    pattern = r'[^a-zA-Z0-9_]'
    if not re.search(pattern, name):
        if config.mysql_enable:
            if config.main_server:
                db_data = (send_id, name)
                connect_and_insert_db("qq_id,player_id", "user_list", db_data, config.mysql_config)
                return True
        else:
            data[send_id] = name  # 进行绑定
            save_data(__mcdr_server)
            return True
    else:
        return False


# 检测玩家名是否存在
def real_name(username: str):
    # 定义Minecraft API的URL
    url = "https://api.mojang.com/users/profiles/minecraft/{}"
    # 发送GET请求到Minecraft API
    response = requests.get(url.format(username))

    # 检查响应状态码
    if response.status_code == 200:
        # 如果状态码为200，则表示玩家用户名存在
        return True
    else:
        # 如果状态码不为200，则表示玩家用户名不存在
        return False


class RobotCommandSource(CommandSource):
    # 初始化方法，传入机器人的名字和权限等级
    def __init__(self, name):
        self.name = name

    # 重写get_permission_level方法，返回机器人的权限等级
    def get_permission_level(self):
        return PermissionLevel.OWNER

    # 重写get_name方法，返回机器人的名字
    def get_name(self):
        return self.name

    # 重写is_player方法，返回False，表示这不是一个玩家
    def is_player(self):
        return False

    # 重写reply方法，用来回复命令来源
    def reply(self, message, **kwargs):
        # 返回命令结果给answer
        global answer
        answer = message

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'QQbot[plugin=qq_tools]'
