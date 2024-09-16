import mongoengine


def global_init():
    mongoengine.register_connection(alias='core', name='ujima_bilingual')