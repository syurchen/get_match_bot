#!/usr/bin/env python
# -*- coding: utf-8 -*-

# MySQL
from __future__ import print_function
import pymysql

_db_host = "***";
_db_name = "***";
_db_user = "***";
_db_pass = "***";

mysql = pymysql.connect(host = _db_host, port = 3306, user = _db_user, passwd= _db_pass, db=_db_name)
_db = mysql.cursor()


# Imports for Telegram
from telegram.ext import Updater, CommandHandler
import logging
import sys

# Imports for Dota
from dotamatch.history import MatchHistory
from dotamatch.players import ResolveVanityUrl, id_to_32

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
job_queue = None

# DotA globals
steam_api_key = "***"
dota_history = MatchHistory(steam_api_key)
dota_storage = {}

# Message handler funcs
def help(bot, update):
    bot.sendMessage(update.message.chat_id, text='Hello. This bot gives game stats on request. It supports DotA2 so far. Start with /dota_register')

def dota_register(bot, update, args):
    global dota_history, steam_api_key, _db
    try:
        steam_id = args[0]
        vanity_id = ResolveVanityUrl(steam_api_key).id(steam_id)
        if (vanity_id):
            add_db_user(_db, "telegram_id='%s'" % update.message.from_user.id, "steam_id='%s'" % vanity_id)
            bot.sendMessage(update.message.chat_id, text='You have been registed. Try /dota_LM')
        else:
            bot.sendMessage(update.message.chat_id, text='This steam ID doesn\'t seem valid')

    except (IndexError, ValueError):
        bot.sendMessage(update.message.chat_id, text='This command needs your steam ID after space you can obtain it like this http://dl2.joxi.net/drive/2016/07/13/0013/2351/911663/63/e2a5d4a5b9.png')
        return False

def dota_LM(bot, update):
    global dota_history, _db
    try:
        user = get_db_user(_db, "telegram_id='%s'" % update.message.from_user.id)
        last_match = dota_history.matches(account_id = user['steam_id'], matches_requested = 1)
        bot.sendMessage(update.message.chat_id, text = 'http://www.dotabuff.com/matches/' + str(last_match[0].match_id))
    except:
        bot.sendMessage(update.message.chat_id, text = "Something went wrong. Did you /dota_register ?")

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

# Database functions
def get_db_user(db, *args):
# Note that values should be in single quotes
    query = ' and '.join(args)

    db.execute("show columns from match_bot_users")
    columns = db.fetchall()
    db.execute("select * from match_bot_users where %s order by id desc limit 1" % query)
    values = db.fetchone()
    result = {}
    for column, value in zip(columns, values):
        result[column[0]] = value
    return result

def add_db_user(db, *args):
    columns = []
    values = []
    for arg in args:
        temp = arg.split('=')
        columns.append(temp[0])
        values.append(temp[1])
    values = ','.join(values)
    columns = ','.join(columns)
    db.execute("insert into match_bot_users (%s) values (%s)" % (columns, values))

def main():
    global job_queue, _to_display, _db

    updater = Updater(***)
    job_queue = updater.job_queue

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # On different commands - answer in Telegram
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("dota_LM", dota_LM))
    dp.add_handler(CommandHandler("dota_register", dota_register, pass_args=True))

    # Log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
