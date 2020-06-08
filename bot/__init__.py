import cherrypy
import gitlab
import telebot
from telebot import types

from bot import config
from bot.merger_bot import bot, db, decoder, encoder, key


class WebhookServer(object):
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def index(self):
        # raw_body = cherrypy.request.body.read()
        raw_json = cherrypy.request.json  # получаем вебхук
        if raw_json['object_kind'] == 'merge_request':  # если вебхук вызван мержреквестом
            print(raw_json)

            # Парсинг вебхука ########################################################################
            assignees_array = raw_json['assignees']  # находим всем юзеров, заасаненных к мержреквесту
            project_name = raw_json['project']['name']  # название проекта
            project_id = raw_json['project']['id']  # id проекта
            source_branch = raw_json['object_attributes']['source_branch']  # ветка, которую сливаем
            target_branch = raw_json['object_attributes']['target_branch']  # ветка, в которую сливаем
            author_name = raw_json['user']['name']  # имя автора merge request
            merge_request_url = raw_json['object_attributes']['url']  # адрес страницы merge request
            mg_title = raw_json['object_attributes']['title']  # заголовок мерд реквеста
            try:
                action = raw_json['object_attributes']['action']  # действие
            except KeyError:
                action = None
            result = None
            ##########################################################################################

            for i in assignees_array:  # для каждого пользователя
                private_key = db.token.find_one(
                    {'idGitLab': encoder(i['username'])})  # достаем ключ авторизации пользователя
                if private_key is None:
                    print("Warning! No user was found to a merge request!")
                else:
                    # авторизуемся для каждого юзера по последнему токену
                    gl = gitlab.Gitlab('https://git.iu7.bmstu.ru/',
                                       private_token=decoder(private_key['token'][-1]))  # ['token'][-1]
                    project = gl.projects.get(project_id)  # находим проект
                    if action is not None:
                        result = project.repository_compare(target_branch, source_branch)
                    for receiver in db.token.find({'idGitLab': encoder(i['username'])}):
                        if action is not None and result:
                            # для каждого телеграм аккаунта, прикрепленного к этому юзеру
                            for j, file in enumerate(result['diffs']):
                                if action == 'open' or action == 'merged':
                                    diff = "```" + str(file['diff']).replace("```", "\`\`\`") + "```"
                                    message = "Пользователь {0} отправил Вам " \
                                              "запрос на слитие веток {1} и {2} " \
                                              "в проекте {3}\n".format(author_name,
                                                                       target_branch,
                                                                       source_branch,
                                                                       project_name).replace("_", "\_")
                                    try:
                                        bot.send_message(chat_id=decoder(receiver['id']), text=message + diff,
                                                         parse_mode="markdown")
                                    except telebot.apihelper.ApiException:
                                        print("The chat was not founded. It looks like a trouble with db :c")

                                if action == 'reopen' and j < 1:
                                    message = "В проекте \"{0}\" пользователем {1} " \
                                              "был переоткрыт merge request {2)".format(project_name,
                                                                                        author_name,
                                                                                        mg_title)
                                    try:
                                        bot.send_message(chat_id=decoder(receiver['id']), text=message)
                                    except telebot.apihelper.ApiException:
                                        print("The chat was not founded. It looks like a trouble with db :c")

                                if action == 'update' and j < 1:
                                    message = "В Merge Request {0} произошло новое событие.".format(mg_title)
                                    bot.send_message(chat_id=decoder(receiver['id']), text=message)

                                if action == 'close' and j < 1:
                                    message = "Merge request {0} был закрыт.".format(mg_title)
                                    try:
                                        bot.send_message(chat_id=decoder(receiver['id']), text=message)
                                    except telebot.apihelper.ApiException:
                                        print("The chat was not founded. It looks like a trouble with db :c")

                                if action == 'none' and j < 1:
                                    message = "В Merge Request {0} произошло новое событие.".format(mg_title)
                                    try:
                                        bot.send_message(chat_id=decoder(receiver['id']), text=message)
                                    except telebot.apihelper.ApiException:
                                        print("The chat was not founded. It looks like a trouble with db :c")

                                if (action == 'update' or action == 'close') and j >= 1 and len(
                                        result['diffs']) - 1 != 0:
                                    message = "А так же еще изменения в {0} файлах".format(len(result['diffs']) - 1)
                                    try:
                                        bot.send_message(chat_id=decoder(receiver['id']), text=message)
                                    except telebot.apihelper.ApiException:
                                        print("The chat was not founded. It looks like a trouble with db :c")
                                    break  # прерываем вывод сообщений, чтобы не засорять чат
                        else:
                            message = "В репозитории {0} произошло неопознанное событие".format(project_name)
                            try:
                                bot.send_message(chat_id=decoder(receiver['id']), text=message)
                            except telebot.apihelper.ApiException:
                                print("The chat was not founded. It looks like a trouble with db :c")

                        # отсылаем кнопочку со ссылкой на merge request
                        inline_item1 = types.InlineKeyboardButton('Merge Request', url=merge_request_url)
                        inline_bt1 = types.InlineKeyboardMarkup()
                        inline_bt1.add(inline_item1)
                        try:
                            bot.send_message(chat_id=decoder(receiver['id']),
                                             text="Более подробную информацию о мерж реквесте можно узнать, "
                                                  "перейдя по ссылке.",
                                             reply_markup=inline_bt1)
                        except telebot.apihelper.ApiException:
                            print("The chat was not founded. It looks like a trouble with db :c")
