import requests
import json
from mcdreforged.api.all import *
from mcdreforged.api.types import PluginServerInterface
from wsgiref.simple_server import make_server
import re


global httpd


def on_load(server, prev):
    cq_listen(True)
# requests.get(url='http://127.0.0.1:5700/send_group_msg?group_id={0}&message={1}'.format(gid, msg))


def on_unload(server):
    httpd.shutdown()
    print("Bye")


@new_thread('QQListen')
def cq_listen(start):
    global httpd
    port = 5701
    httpd = make_server("0.0.0.0", port, application)
    print("serving http on port {0}...".format(str(port)))
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
