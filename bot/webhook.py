import logging

import gitlab
from telebot import types

from bot.merger_bot import bot, decoder
import telebot


class Webhook:
    def __init__(self, raw_json):
        self.assignees_array = raw_json['assignees']  # находим всем юзеров, заасаненных к мержреквесту
        self.project_name = raw_json['project']['name']  # название проекта
        self.project_id = raw_json['project']['id']  # id проекта
        self.source_branch = raw_json['object_attributes']['source_branch']  # ветка, которую сливаем
        self.target_branch = raw_json['object_attributes']['target_branch']  # ветка, в которую сливаем
        self.author_name = raw_json['user']['name']  # имя автора merge request
        self.merge_request_url = raw_json['object_attributes']['url']  # адрес страницы merge request
        self.mg_title = raw_json['object_attributes']['title']  # заголовок мерд реквеста

    def get_repo_compare(self, private_key):
        # авторизуемся для каждого юзера по последнему токену
        gl = gitlab.Gitlab('https://git.iu7.bmstu.ru/', private_token=decoder(private_key['token'][-1]))
        # ['token'][-1]
        project = gl.projects.get(self.project_id)  # находим проект
        return project.repository_compare(self.target_branch, self.source_branch)

    def send_open(self, receiver, file):
        diff = "```" + str(file['diff']).replace("```", "\`\`\`") + "```"
        message = "Пользователь {0} отправил Вам " \
                  "запрос на слитие веток {1} и {2} " \
                  "в проекте {3}\n".format(self.author_name,
                                           self.target_branch,
                                           self.source_branch,
                                           self.project_name).replace("_", "\_")
        try:
            bot.send_message(chat_id=decoder(receiver['id']), text=message + diff,
                             parse_mode="markdown")
        except telebot.apihelper.ApiException:
            logging.error("The chat was not founded. It looks like a trouble with db :c")

    def send_reopen(self, receiver):
        message = "В проекте \"{0}\" пользователем {1} " \
                  "был переоткрыт merge request {2)".format(self.project_name,
                                                            self.author_name,
                                                            self.mg_title)
        try:
            bot.send_message(chat_id=decoder(receiver['id']), text=message)
        except telebot.apihelper.ApiException:
            logging.error("The chat was not founded. It looks like a trouble with db :c")

    def send_update(self, receiver):
        message = "В Merge Request {0} произошло новое событие.".format(self.mg_title)
        bot.send_message(chat_id=decoder(receiver['id']), text=message)

    def send_close(self, receiver):
        message = "Merge request {0} был закрыт.".format(self.mg_title)
        try:
            bot.send_message(chat_id=decoder(receiver['id']), text=message)
        except telebot.apihelper.ApiException:
            logging.error("The chat was not founded. It looks like a trouble with db :c")

    def send_new(self, receiver):
        message = "В Merge Request {0} произошло новое событие.".format(self.mg_title)
        try:
            bot.send_message(chat_id=decoder(receiver['id']), text=message)
        except telebot.apihelper.ApiException:
            logging.error("The chat was not founded. It looks like a trouble with db :c")

    def send_undefined(self, receiver):
        message = "В репозитории {0} произошло неопознанное событие".format(self.project_name)
        try:
            bot.send_message(chat_id=decoder(receiver['id']), text=message)
        except telebot.apihelper.ApiException:
            logging.error("The chat was not founded. It looks like a trouble with db :c")

    def send_others(self, receiver, result):
        message = "А так же еще изменения в {0} файлах".format(len(result['diffs']) - 1)
        try:
            bot.send_message(chat_id=decoder(receiver['id']), text=message)
        except telebot.apihelper.ApiException:
            logging.error("The chat was not founded. It looks like a trouble with db :c")

    def send_button(self, receiver):
        inline_item1 = types.InlineKeyboardButton('Merge Request', url=self.merge_request_url)
        inline_bt1 = types.InlineKeyboardMarkup()
        inline_bt1.add(inline_item1)
        try:
            bot.send_message(chat_id=decoder(receiver['id']),
                             text="Более подробную информацию о мерж реквесте можно узнать, "
                                  "перейдя по ссылке.",
                             reply_markup=inline_bt1)
        except telebot.apihelper.ApiException:
            logging.error("The chat was not founded. It looks like a trouble with db :c")
