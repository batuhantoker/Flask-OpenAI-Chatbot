import mongoengine

class Conversation(mongoengine.EmbeddedDocument):
    is_bot = mongoengine.BooleanField(default=True)     # True: Assistant, False: User
    content = mongoengine.StringField(required=True)    # The message content
