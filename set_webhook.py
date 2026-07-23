import sys
import requests
import config

def set_webhook(url: str):
    """Sets the Telegram webhook URL."""
    api_url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/setWebhook"
    response = requests.post(api_url, data={"url": url})
    print("Set Webhook Response:", response.json())

def get_webhook_info():
    """Gets current Telegram webhook status."""
    api_url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getWebhookInfo"
    response = requests.get(api_url)
    print("Webhook Info:", response.json())

def delete_webhook():
    """Deletes current Webhook to revert back to local polling mode."""
    api_url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/deleteWebhook"
    response = requests.post(api_url)
    print("Delete Webhook Response:", response.json())

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "info":
            get_webhook_info()
        elif arg == "delete":
            delete_webhook()
        else:
            set_webhook(arg)
    else:
        print("Usage:")
        print("  python set_webhook.py https://your-app.vercel.app  (Set Webhook)")
        print("  python set_webhook.py info                       (Check Status)")
        print("  python set_webhook.py delete                     (Delete Webhook for local polling)")
