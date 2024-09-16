from data_classes.users import User
import datetime

def create_account(user_id: str) -> User:
    user = User()
    user.user_id = user_id
    user.timer_is_running = False   # Is only true after login
    
    user.save() # This will actually update Mongo db. (Mongo follows lazy execution)

    return user


def find_account_by_user_id(user_id: str) -> User:
    user = User.objects(user_id=user_id).first()
    return user


def start_timer_by_User(existing_user: User) -> datetime.datetime:
    start_time = datetime.datetime.now(datetime.timezone.utc)
    existing_user.start_time = start_time
    existing_user.timer_is_running = True

    existing_user.save()
    
    return start_time


