import requests
import json
import re
import time
from mcdreforged.api.all import *
from typing import List, Dict
from wsgiref.simple_server import make_server

global httpd
__mcdr_server: PluginServerInterface


class Config(Serializable):
    send_host: str = "127.0.0.1"
    send_port: int = 5700
    post_host: str = "0.0.0.0"
    post_port: int = 5701
    groups: List[int] = [00000000, 11111111]
    admins: List[int] = [00000000, 11111111]
    whitelist_add_with_bound: bool = True
    whitelist_remove_with_leave: bool = True
    forwards: Dict[str, bool] = {
        'mc_to_qq': False,
        'qq_to_mc': False
    }
    commands: Dict[str, bool] = {
        'list': True
    }


def on_load(server: PluginServerInterface, prev_module):
    global __mcdr_server
    __mcdr_server = server  # mcdr init
    config = server.load_config_simple(target_class=Config)  # Get Config setting
    cq_listen(config.post_host, config.post_port)


# requests.get(url='http://127.0.0.1:5700/send_group_msg?group_id={0}&message={1}'.format(gid, msg))


def on_unload(server: PluginServerInterface):
    httpd.shutdown()
    __mcdr_server.logger.info("Http server stopping now...")
    time.sleep(0.5)


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
        print(json_dict)

    return ()
