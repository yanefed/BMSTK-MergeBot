import threading

import cherrypy

from bot import config, WebhookServer
from bot.merger_bot import bot

cherrypy.tree.mount(WebhookServer(), '/')

if __name__ == '__main__':
    # конфигурация сервера
    cherrypy.config.update({
        'server.socket_host'    : config.WEBHOOK_HOST,
        'server.socket_port'    : config.WEBHOOK_PORT,
        'server.ssl_module'     : 'builtin',
        'server.ssl_certificate': config.WEBHOOK_SSL_CERT,
        'server.ssl_private_key': config.WEBHOOK_SSL_PRIV,
    })

    # параллельный запуск бота и сервера
    server_thread = threading.Thread(target=cherrypy.quickstart, args=(WebhookServer(),))
    bot_thread = threading.Thread(target=bot.polling)
    server_thread.start()
    bot_thread.start()
