import firebase_admin
from firebase_admin import credentials, messaging
from config_helper import get_config

CONFIG = get_config()["ANDROID_APP_CONFIG"]

class NotificationService:

    TOKEN = CONFIG["NOTIFICATION_TOKEN"]

    def __init__(self):
        cred = credentials.Certificate(CONFIG["FIREBASE_CREDENTIALS_CERTIFICATE"])
        firebase_admin.initialize_app(cred)

    def send_notification(self, title, body):
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            token=self.TOKEN
        )

        # Send a message to the device corresponding to the provided
        # registration token.
        response = messaging.send(message)
        # Response is a message ID string.
        print('Notification sent')
