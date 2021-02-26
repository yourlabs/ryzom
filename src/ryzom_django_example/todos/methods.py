from django.apps import apps
from django.contrib.auth.models import User

from ryzom.methods import Methods

# Avoid importing models during django_setup().
AppModel = apps.get_model('todos.Task')


def create_user(user, params):
    username = params.get('username', None)
    password = params.get('username', None)
    email = params.get('username', None)

    if username and password and email:
        user, created = User.objects.get_or_create(
                username=username, email=email)
        if created:
            user.set_password(password)
            user.save()
            return user.id
        else:
            return {
                'type': 'Error',
                'params': {
                    'name': 'Forbidden',
                    'message': 'User already exists in Database'
                }
            }
    else:
        return {
            'type': 'Error',
            'params': {
                'name': 'Bad request',
                'message': 'You must provide a unique username, \
                        a valid email address and a password'
            }
        }


def insert_task(user, params):
    if 'about' in params:
        user = user if user.id else None
        t = AppModel(user=user, about=params['about'])
        t.save()
        return True
    return False


def remove_task(user, params):
    if 'id' in params:
        t = AppModel.objects.get(id=params['id'])
        if t:
            t.delete()
            return True
    return False


Methods.add({
    'create_user': create_user,
    'insert_task': insert_task,
    'remove_task': remove_task
})
