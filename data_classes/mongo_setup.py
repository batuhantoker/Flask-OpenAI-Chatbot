import mongoengine
import json

def global_init():

    with open('config.json') as f:
        config = json.load(f)

    # Access API key using the config dictionary
    mongo_db_url = config['mongo-db-url']

    mongoengine.register_connection(alias='core', host=mongo_db_url)