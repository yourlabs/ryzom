from todos.models import Tasks


class Methods():

    def insert_task(params):
        if 'about' in params:
            t = Tasks(about=params['about'])
            t.save()
            return True
        return False

    def remove_task(params):
        if 'id' in params:
            t = Tasks.objects.get(id=params['id'])
            if t:
                t.delete()
                return True
        return False
