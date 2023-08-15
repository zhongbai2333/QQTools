from typing import List, Dict

from mcdreforged.api.utils.serializer import Serializable

global help_info, admin_help_info, help_private_info, admin_help_private_info, bound_help


class AdminCommands(Serializable):
    to_mcdr: str = "tomcdr"
    to_minecraft: str = "togame"
    whitelist: str = "whitelist"


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
    admin_commands: dict = AdminCommands()
