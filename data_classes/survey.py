import mongoengine
import datetime

class SurveyResponse(mongoengine.Document):
    user_id = mongoengine.StringField(required=True)
    responses = mongoengine.DictField(required=True)
    timestamp = mongoengine.DateTimeField(default=datetime.datetime.now)

    meta = {
        'db_alias': 'core',
        'collection': 'survey_responses'
    }
