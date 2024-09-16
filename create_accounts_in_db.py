import services.data_service as svc
import data_classes.mongo_setup as mongo_setup

user_ids = ['12345', '67890', '11122', '33344'] 

# Connect with DB
mongo_setup.global_init()

for user_id in user_ids:
    existing_user = svc.find_account_by_user_id(user_id)
    if existing_user:
        print(user_id, "Already exists, skipping.")
    else:
        svc.create_account(user_id)

