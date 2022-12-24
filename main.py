import pymysql
import contextlib

from config import host, login, password, db_name

from aiogram import Bot, Dispatcher, executor, types

from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

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
        insert_query = "INSERT INTO `users` (ID_user, ID_sponsor, status, first_name, last_name, username) VALUES ({id}, {ref}, {status}, '{fn}', '{ln}', '{un}');".format(id=user["id"], ref=ref, status=status, fn = user["first_name"], ln = user["last_name"], un = user["username"])
        cursor.execute(insert_query)
        return True

def delete_user(user_id):
    with mysql() as cursor:
        delete_query = f"DELETE FROM `users` WHERE ID_user = {user_id};"
        cursor.execute(delete_query)
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

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    command = message.text.split()
    current_user = get_user(message.from_user.id)
    if current_user == None or current_user["status"] == 4: # пользователь ещё не зарегистрирован
        if len(command) < 2:  # проверка наличия реферальной ссылки
            if current_user == None:
                insert_user(message.from_user, 0, 4)
            await message.answer("Я работаю только с теми, кто пришёл по реферальной ссылке.\n" + get_text("NOT_WELCOME"))
        else:
            sponsor = get_user(command[1])
            if sponsor != None and sponsor["status"] != 4:  # спонсор прошел регистрацию
                if current_user != None:
                    delete_user(message.from_user.id)
                insert_user(message.from_user, command[1], 3)
                text = "Приветствую, {}!\nВы здесь по приглашению {}.\n".format(message.from_user.first_name, sponsor["first_name"])
                text += get_text("WELCOME")
                await message.answer(text)
            else:
                if current_user == None:
                    insert_user(message.from_user, 0, 4)
                await message.answer("Некорректная реферальная ссылка.\n" + get_text("NOT_WELCOME"))
    elif current_user["status"] == 0:  # пользователь есть в базе, но ранее приостановил участие
        await message.answer(f"Привет, {current_user['first_name']}!\nВозобновить работу бота?")
    elif current_user["status"] == 1:  # пользователь есть в базе и активен
        await message.answer(f"Привет, {current_user['first_name']}!\nКак дела?")
    elif current_user["status"] == 2:  # пользователь был заблокирован по жалобе
        await message.answer(f"Ваш контакт заблокирован из-за жалоб участников.")
    elif current_user["status"] == 3:  # пользователь есть в базе, но не познакомился со спонсорами
        await message.answer(f"Привет, {current_user['first_name']}!\nГотовы познакомиться со спонсорами?")
    else:
        await message.answer(f"Произошла ошибка. Воспользуйтесь сервисом позднее.")


@dp.message_handler(commands=['meet'])
async def meet_sponsor(message: types.Message):
    depth = get_text("depth")
    current_user = get_user(message.from_user.id)
    n = 0
    while n < depth:
        if current_user["ID_sponsor"] == 0:
            break
        current_user = get_user(current_user["ID_sponsor"])
        if current_user["status"] == 1:
            await message.answer("@" + current_user["username"] + "\n" + current_user["description"])
            n += 1
    change_status(message.from_user.id, 1) #    когда пользователь познакомился со спонсорами, его статус позволяет заполнить информацию о себе

@dp.message_handler()
async def echo(message: types.Message):
   await message.answer(message.text)

if __name__ == '__main__':
    # with mysql() as cursor:
    #     cursor.execute("SELECT * FROM `base`")
    #     base = cursor.fetchone()
    #     print(base)
#    print(get_text("INFO_BOT"))

#    print(get_user(22222))

    executor.start_polling(dp, skip_updates=True)