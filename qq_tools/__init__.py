import requests
import json
import re
import time
from mcdreforged.api.all import *
from typing import List, Dict
from wsgiref.simple_server import make_server

global httpd, config, data
__mcdr_server: PluginServerInterface
data: dict


class Config(Serializable):
    send_host: str = "127.0.0.1"
    send_port: int = 5700
    post_host: str = "0.0.0.0"
    post_port: int = 5701
    groups: List[int] = [00000000, 11111111]
    admins: List[int] = [00000000, 11111111]
    server_name: str = "Survival Server"
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
    if json_dict['post_type'] != 'meta_event':
        __mcdr_server.logger.info(json_dict)
        parse_msg(json_dict)

    return ()


def on_load(server: PluginServerInterface, prev_module):
    global __mcdr_server, config, data
    __mcdr_server = server  # mcdr init
    config = server.load_config_simple(target_class=Config)  # Get Config setting
    data = server.load_config_simple(
        'data.json',
        default_config={'data': {}},
        echo_in_console=False
    )['data']
    cq_listen(config.post_host, config.post_port)


def on_server_startup(server: PluginServerInterface):
    msg_start = config.server_name + ' 启动完成'
    for i in config.groups:
        send_qq(i, msg_start)


def on_unload(server: PluginServerInterface):
    httpd.shutdown()
    __mcdr_server.logger.info("Http server stopping now...")
    time.sleep(0.5)


def parse_msg(get_json):
    if get_json['message_type'] == 'group' and get_json['group_id'] in config.groups:
        __mcdr_server.logger.info("Group")
        msg = get_json['message']
        if msg[0] == '#':
            send_qq(get_json['group_id'], pares_group_command(get_json['user_id'], msg[1:]))
    elif get_json['message_type'] == 'private':
        __mcdr_server.logger.info("Private")


def pares_group_command(send_id: int, command: str):
    command = command.split(' ')
    if command[0] == 'bound' and len(command) == 2:
        print(data.keys())
        if send_id in data.keys():
            return f'[CQ:at,qq={send_id}] 您已在{config.server_name}绑定ID: {data[send_id]}, 请联系管理员修改'
        else:
            data[send_id] = command[1]
            save_data(__mcdr_server)
            if config.whitelist_add_with_bound:
                __mcdr_server.execute(f'whitelist add {command[1]}')
            else:
                return f'[CQ:at,qq={send_id}] 已在{config.server_name}成功绑定{config.why_no_whitelist}'
            return f'[CQ:at,qq={send_id}] 已在{config.server_name}成功绑定'
    elif command[0] == 'bound' and len(command) != 2:
        return '错误的格式，请使用 #bound <ID>'
    else:
        return '错误的命令，请使用 #help 获取帮助！'


def send_qq(gid: int, msg: str):
    msg = msg.replace('#', '%23')
    __mcdr_server.logger.info(msg)
    requests.get(
        url='http://{0}:{1}/send_group_msg?group_id={2}&message={3}'.format(config.send_host, config.send_port, gid,
                                                                            msg))


def save_data(server: PluginServerInterface):
    server.save_config_simple({'data': data}, 'data.json')
