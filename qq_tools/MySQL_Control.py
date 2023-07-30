try:  # 试图导入mysql处理
    import mysql.connector
except ImportError:
    mysql = None


def connect_and_query_db(your_table_name: str, db_config):
    if not mysql:
        return None
    try:
        # 创建连接
        conn = mysql.connector.connect(**db_config)
        # 创建游标对象
        cursor = conn.cursor()
        # 示例查询
        query = f"SELECT * FROM {your_table_name};"
        cursor.execute(query)
        # 获取查询结果
        result = cursor.fetchall()
        # 关闭游标和连接
        cursor.close()
        conn.close()
        return result

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None


def create_table_if_not_exists(table_name: str, table_type: str, db_config):
    if not mysql:
        return None
    try:
        # 创建连接
        conn = mysql.connector.connect(**db_config)
        # 创建游标对象
        cursor = conn.cursor()
        # 查询是否存在指定表格
        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        result = cursor.fetchall()
        # 如果表格不存在，则创建新表格
        if len(result) == 0:
            create_table_query = f"""
                CREATE TABLE {table_name} ({table_type})
            """
            cursor.execute(create_table_query)
            print(f"Table '{table_name}' created successfully.")
        # 关闭游标和连接
        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"Error: {err}")
