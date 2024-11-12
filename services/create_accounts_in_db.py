import services.data_service as svc

user_ids = ['12345', '67890', '11122', '33344', '55678', '99001', '23456', '78901', '34567', '89012', '56789', '10123', '67812', '91234', '0', '1']

def run_create_accounts():
    for user_id in user_ids:
        # Check if it already exists in the DB then skip
        existing_user = svc.find_account_by_user_id(user_id)
        if existing_user:
            # print(user_id, "Already exists, skipping.")
            continue
        else:
            svc.create_account(user_id)