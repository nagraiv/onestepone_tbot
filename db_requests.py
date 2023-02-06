import pymysql
import contextlib

from config import host, login, password, db_name


@contextlib.contextmanager
def mysql():
    connection = pymysql.connect(
            host=host,
            user=login,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
    cursor = connection.cursor()
    try:
        yield cursor
    finally:
        connection.commit()
        cursor.close()
        connection.close()


def get_user(user_id):
    with mysql() as cursor:
        find_user = f"SELECT * FROM `users` WHERE ID_user = {user_id};"
        cursor.execute(find_user)
        user = cursor.fetchone()
        return user


def insert_user(user, ref, status):
    with mysql() as cursor:
        insert_query = "INSERT INTO `users` (ID_user, ID_sponsor, status, first_name, last_name, username) VALUES ({id}, {ref}, {status}, '{fn}', '{ln}', '{un}');".format(id=user["id"], ref=ref, status=status, fn=user["first_name"], ln=user["last_name"], un=user["username"])
        cursor.execute(insert_query)
        return True


def delete_user(user_id):
    with mysql() as cursor:
        delete_query = f"DELETE FROM `users` WHERE ID_user = {user_id};"
        cursor.execute(delete_query)
        return True


def update_info(user_id, field, info):
    with mysql() as cursor:
        update_query = f"UPDATE `users` SET `{field}` = '{info}' WHERE ID_user = {user_id};"
        cursor.execute(update_query)
        return True


def change_status(user_id, new_status):
    with mysql() as cursor:
        update_query = f"UPDATE `users` SET status = {new_status} WHERE ID_user = {user_id};"
        cursor.execute(update_query)
        return True


def get_text(column):
    with mysql() as cursor:
        text_query = f"SELECT {column} FROM `base`"
        cursor.execute(text_query)
        text = cursor.fetchone()
        return text[column]


def count_child(user_id):
    with mysql() as cursor:
        count_query = f"SELECT COUNT(*) `ID_user` FROM `users` WHERE `ID_sponsor`={user_id};"
        cursor.execute(count_query)
        count = cursor.fetchone()
        return count["ID_user"]


def get_childs(user_id):
    with mysql() as cursor:
        new_query = f"SELECT `ID_user` FROM `users` WHERE `ID_sponsor`={user_id} and `status` IN (1,3) ORDER BY `register_date`;"
        cursor.execute(new_query)
        result = cursor.fetchall()
        childs = []
        for item in result:
            childs.append(item["ID_user"])
        return childs


def get_active_childs(user_id):
    with mysql() as cursor:
        new_query = f"SELECT `ID_user` FROM `users` WHERE `ID_sponsor`={user_id} and `status`=1 ORDER BY `register_date`;"
        cursor.execute(new_query)
        result = cursor.fetchall()
        childs = []
        for item in result:
            childs.append(item["ID_user"])
        return childs


def last_action(user_id):
    with mysql() as cursor:
        update_query = f"UPDATE `users` SET last_action = now() WHERE ID_user = {user_id};"
        cursor.execute(update_query)
        return True


def get_all_id():
    with mysql() as cursor:
        new_query = f"SELECT `ID_user` FROM `users` WHERE `status` IN (0,1,2,3);"
        cursor.execute(new_query)
        result = cursor.fetchall()
        all_users = []
        for item in result:
            if item["ID_user"] > 100000:
                all_users.append(item["ID_user"])
        return all_users
