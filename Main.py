import telebot
from telebot import types
import json
import Database

TOKEN = 'TOKEN'
bot = telebot.TeleBot(TOKEN)

user_roles_file = 'UserWhitelist.json'

def process_user_disintegration(message):
    try:
        user_id_to_delete = int(message.text)
        if get_user_status(user_id_to_delete):
            delete_user_role(user_id_to_delete)
            bot.send_message(message.chat.id, "User deleted successfully.")
        else:
            bot.send_message(message.chat.id, "User does not exist.")
    except ValueError:
        bot.send_message(message.chat.id, "Invalid user ID. Please send a valid user ID.")
def load_user_roles():
    try:
        with open(user_roles_file, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_user_roles(roles):
    with open(user_roles_file, 'w') as file:
        json.dump(roles, file, indent=4)

def add_user_role(user_id, status):
    roles = load_user_roles()
    for role in roles:
        if role['user_id'] == user_id:
            role['status'] = status
            break
    else:
        roles.append({"user_id": user_id, "status": status})
    save_user_roles(roles)

def get_user_status(user_id):
    roles = load_user_roles()
    for role in roles:
        if role['user_id'] == user_id:
            return role['status']
    return None

def delete_user_role(user_id):
    roles = load_user_roles()
    roles = [role for role in roles if role['user_id'] != user_id]
    save_user_roles(roles)


@bot.message_handler(commands=['add'])
def command_add(message):
    user_id = message.from_user.id
    if get_user_status(user_id) == "Admin":
        msg = bot.send_message(message.chat.id, "Send the user ID of the new user:")
        bot.register_next_step_handler(msg, process_user_addition, user_id)  # Pass the admin's user ID for verification
    else:
        bot.send_message(message.chat.id, "You do not have permission to add users.")

def process_user_addition(message, admin_user_id):
    if message.from_user.id != admin_user_id:
        bot.send_message(message.chat.id, "You are not authorized to perform this action.")
        return

    try:
        user_id = int(message.text)
        markup = types.InlineKeyboardMarkup(row_width=3)
        buttons = [
            types.InlineKeyboardButton("Admin", callback_data=f"admin_{user_id}_{admin_user_id}"),
            types.InlineKeyboardButton("Moderator", callback_data=f"mod_{user_id}_{admin_user_id}"),
            types.InlineKeyboardButton("Reader", callback_data=f"reader_{user_id}_{admin_user_id}")
        ]
        markup.add(*buttons)
        bot.send_message(message.chat.id, "Select the role for the new user:", reply_markup=markup)
    except ValueError:
        bot.send_message(message.chat.id, "Invalid user ID. Please send a valid user ID.")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):

    parts = call.data.split("_")
    callback_action = parts[0]

    if callback_action in ["admin", "mod", "reader"]:
        if len(parts) != 3:
            bot.answer_callback_query(call.id, "Invalid callback data format for role assignment.", show_alert=True)
            return
        _, user_id, admin_user_id = parts
        user_id = int(user_id)
        admin_user_id = int(admin_user_id)

        if call.from_user.id != admin_user_id:
            bot.answer_callback_query(call.id, "You do not have permission to perform this action.", show_alert=True)
            return


        add_user_role(user_id, callback_action.capitalize())
        bot.answer_callback_query(call.id, f"User added as {callback_action.capitalize()}.")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.edit_message_text(f"{callback_action.capitalize()} added successfully.", chat_id=call.message.chat.id, message_id=call.message.message_id)

    elif call.data.startswith("next_"):
        if call.from_user.id == int(parts[2]):
            start_index = parts[1]
            send_paginated_data(call.message, int(start_index), call.from_user.id)
            bot.delete_message(call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "You do not have permission to perform this action.", show_alert=True)
            return
    elif callback_action in "read":
        if call.from_user.id != int(parts[2]):
            bot.answer_callback_query(call.id, "You do not have permission to perform this action.", show_alert=True)
            return

        bot.answer_callback_query(call.id, f"{parts[1]}", show_alert=True)


@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Welcome to the Database Usage Showcase!")

@bot.message_handler(commands=['check', 'status'])
def handle_check(message):
    user_id = message.from_user.id
    bot.send_message(message.chat.id, f"{user_id} is {get_user_status(user_id)}")

@bot.message_handler(commands=['delete'])
def handle_delete(message):
    user_id = message.from_user.id
    if get_user_status(user_id) in ["Admin"]:
        msg = bot.send_message(message.chat.id, "Send the user ID of the user to delete:")
        bot.register_next_step_handler(msg, process_user_disintegration)
    else:
        bot.send_message(message.chat.id, "You do not have permission to delete users.")


@bot.message_handler(commands=['db_read'])
def handle_DBread(message):
    user_id = message.from_user.id
    send_paginated_data(message, 0, user_id)


def send_paginated_data(message, start_index, user_id):
    db = Database.Database()

    if get_user_status(user_id) in ["Admin", "Mod", "Reader"]:
        db_list = [x for x in db.selectAll()]
        temp_dif = len(db_list) - start_index
        markup = types.InlineKeyboardMarkup(row_width=temp_dif)
        print(start_index, len(db_list), temp_dif)

        users = db_list[start_index: (start_index + 5) if temp_dif >= 5 else (len(db_list))]
        print(users)
        if start_index < len(db_list):
            for user in users:
                markup.add(types.InlineKeyboardButton(str(user[0]), callback_data=f"read_{user}_{user_id}"))
                print(1)

            if start_index + 1 < len(db_list):
                markup.add(types.InlineKeyboardButton("Next", callback_data=f"next_{start_index + len(users)}_{user_id}"))
                print(1)

            bot.send_message(message.chat.id, "Big rofl guys:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "No more entries in the database.")

        db.closeConnection()
    else:
        bot.send_message(message.chat.id, "You do not have permission to check the database.")
        db.closeConnection()




def add_to_DB(message, user_id):
    db = Database.Database()
    if message.from_user.id == user_id:
        try:
            string = [x.strip() for x in message.text.split(',')]
            db.insertRecord(string[0], string[1], string[2], string[3])
            bot.send_message(message.chat.id, "New person added successfully!")
        except ValueError:
            bot.send_message(message.chat.id, "leave me alone")
    else:
        bot.send_message(message.chat.id, "You do not have permission to  database.")
        db.closeConnection()
    db.closeConnection()

def del_from_DB(message, user_id):
    db = Database.Database()
    if message.from_user.id == user_id:
        try:
            if db.deleteStudentField(message.text):
                bot.send_message(message.chat.id, "Successfully deleted!")
            else:
                bot.send_message(message.chat.id, "Deletion ERROR!")
        except ValueError:
            bot.send_message(message.chat.id, "leave me alone")
    else:
        bot.send_message(message.chat.id, "You do not have permission to  database.")
        db.closeConnection()
    db.closeConnection()

def change_on_DB(message, user_id):
    db = Database.Database()
    if message.from_user.id == user_id:
        try:
            string = [x.strip() for x in message.text.split(',')]
            name_change = db.updateStudentField(string[0], "name", string[1])
            age_change = db.updateStudentField(string[0], "age", string[2])
            major_change = db.updateStudentField(string[0], "major", string[3])
            bot.send_message(message.chat.id, f"Name changed: {name_change}\nAge changed: {age_change}\nMajor changed: {major_change}")
        except ValueError:
            bot.send_message(message.chat.id, "leave me alone")
    else:
        bot.send_message(message.chat.id, "You do not have permission to  database.")
        db.closeConnection()
    db.closeConnection()
@bot.message_handler(commands=['db_remove'])
def handle_DBremove(message):
    user_id = message.from_user.id
    if get_user_status(user_id) in ["Admin","Mod"]:
        #Id name age major
        msg = bot.send_message(message.chat.id, "Type the ID of student that you want to remove from the database: ")
        bot.register_next_step_handler(msg, del_from_DB, user_id)
    else:
        bot.send_message(message.chat.id, "You do not have permission to check database.")

@bot.message_handler(commands=['db_change'])
def handle_DBchange(message):
    user_id = message.from_user.id
    if get_user_status(user_id) in ["Admin", "Mod"]:
        # Id name age major
        msg = bot.send_message(message.chat.id, "Type the ID, Name, Age and Major separated by commas: ")
        bot.register_next_step_handler(msg, change_on_DB, user_id)
    else:
        bot.send_message(message.chat.id, "You do not have permission to check database.")


@bot.message_handler(commands=['db_insert'])
def handle_DBinsert(message):
    user_id = message.from_user.id
    if get_user_status(user_id) in ["Admin","Mod"]:
        msg = bot.send_message(message.chat.id, "Type the ID, Name, Age and Major separated by commas:")
        bot.register_next_step_handler(msg, add_to_DB, user_id)
    else:
        bot.send_message(message.chat.id, "You do not have permission to check database.")

if __name__ == '__main__':
    bot.polling(none_stop=True)


###################################################################
# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣤⣤⣤⣤⣤⣶⣦⣤⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀                                #
# ⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⡿⠛⠉⠙⠛⠛⠛⠛⠻⢿⣿⣷⣤⡀⠀⠀⠀⠀                                #⠀⠀⠀⠀⠀                               #
# ⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⠋⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⠈⢻⣿⣿⡄⠀⠀⠀⠀                                #⠀⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⣸⣿⡏⠀⠀⠀⣠⣶⣾⣿⣿⣿⠿⠿⠿⢿⣿⣿⣿⣄⠀⠀⠀⠀                              #⠀⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⣿⣿⠁⠀⠀⢰⣿⣿⣯⠁⠀⠀⠀⠀⠀⠀⠀⠈⠙⢿⣷⡄                                 #⠀
# ⠀⠀⣀⣤⣴⣶⣶⣿⡟⠀⠀⠀⢸⣿⣿⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣷⠀        FURRIES ARE THE BEST ! #
# ⠀⢰⣿⡟⠋⠉⣹⣿⡇⠀⠀⠀⠘⣿⣿⣿⣿⣷⣦⣤⣤⣤⣶⣶⣶⣶⣿⣿⣿⠀ ____/                       #
# ⠀⢸⣿⡇⠀⠀⣿⣿⡇⠀⠀⠀⠀⠹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠃⠀                             #
# ⠀⣸⣿⡇⠀⠀⣿⣿⡇⠀⠀⠀⠀⠀⠉⠻⠿⣿⣿⣿⣿⡿⠿⠿⠛⢻⣿⡇⠀⠀ ⠀⠀⠀⠀                          #
# ⠀⣿⣿⠁⠀⠀⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣧⠀⠀ ⠀⠀⠀⠀                            #
# ⠀⣿⣿⠀⠀⠀⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⠀⠀ @MilterD1                       #
# ⠀⣿⣿⠀⠀⠀⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⠀⠀ @AmadeoMartell / @SPOTIFY_NOW   #
# ⠀⢿⣿⡆⠀⠀⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⡇⠀⠀                                #
# ⠀⠸⣿⣧⡀⠀⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⠃⠀⠀                                #
# ⠀⠀⠛⢿⣿⣿⣿⣿⣇⠀⠀⠀⠀⠀⣰⣿⣿⣷⣶⣶⣶⣶⠶⢠⣿⣿⠀⠀⠀                              #
# ⠀⠀⠀⠀⠀⠀⠀⣿⣿⠀⠀⠀⠀⠀⣿⣿⡇⠀⣽⣿⡏⠁⠀⠀⢸⣿⡇⠀⠀⠀                                #
# ⠀⠀⠀⠀⠀⠀⠀⣿⣿⠀⠀⠀⠀⠀⣿⣿⡇⠀⢹⣿⡆⠀⠀⠀⣸⣿⠇⠀⠀⠀                                 #
# ⠀⠀⠀⠀⠀⠀⠀⢿⣿⣦⣄⣀⣠⣴⣿⣿⠁⠀⠈⠻⣿⣿⣿⣿⡿⠏⠀⠀⠀⠀                               #
# ⠀⠀⠀⠀⠀⠀⠀⠈⠛⠻⠿⠿⠿⠿⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀                                 #
####################################################################