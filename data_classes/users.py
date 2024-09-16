import datetime
import mongoengine
from data_classes.conversation import Conversation


class User(mongoengine.Document):
    user_id = mongoengine.StringField(required=True)

    timer_is_running = mongoengine.BooleanField(default=False)
    # TODO Maybe Add logic to handle pausing the timer too.
    start_time = mongoengine.DateTimeField(default=datetime.datetime.now)

    # conversation_history = mongoengine.EmbeddedDocumentListField(Conversation)


    meta = {
        'db_alias': 'core',
        'collection': 'users'
    }
