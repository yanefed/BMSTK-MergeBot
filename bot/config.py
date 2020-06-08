from bot import merger_bot

WEBHOOK_HOST = merger_bot.webhook_host
WEBHOOK_PORT = merger_bot.webhook_port

WEBHOOK_SSL_CERT = './SSL/webhook_cert.pem'  # Путь к сертификату
WEBHOOK_SSL_PRIV = './SSL/webhook_pkey.pem'  # Путь к приватному ключу

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % merger_bot.telegram_token
