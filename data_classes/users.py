import datetime
import mongoengine
from data_classes.conversation import Conversation


class User(mongoengine.Document):
    user_id = mongoengine.StringField(required=True)
    email_id = mongoengine.StringField(required=True)

    timer_is_running = mongoengine.BooleanField(default=False)
    # TODO Maybe Add logic to handle pausing the timer too.
    # TODO Maybe Add end time and try to handle it.
    start_time = mongoengine.DateTimeField(default=datetime.datetime.now)

    conversation_history = mongoengine.EmbeddedDocumentListField(Conversation)
    
    # New field for survey responses
    survey_responses = mongoengine.DictField()
    
    pre_survey_responses = mongoengine.DictField()  # New field for pre-survey
    
    survey_completed = mongoengine.BooleanField(default=False)


    meta = {
        'db_alias': 'core',
        'collection': 'users'
    }
