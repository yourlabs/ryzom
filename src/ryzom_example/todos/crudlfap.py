from crudlfap import shortcuts as crudlfap

from .models import Task


class TaskMixin:
    allowed_groups = 'any'

    def get_exclude(self):
        req = getattr(self, 'request', None)
        if (req is None
            or
                req and not self.request.user.is_staff):
            return ['user']
        return super().get_exclude()


class TaskCreateView(TaskMixin, crudlfap.CreateView):
    def form_valid(self):
        self.form.instance.user = self.request.user
        return super().form_valid()


class TaskRouter(crudlfap.Router):
    fields = '__all__'
    material_icon = 'view_list'
    model = Task

    views = [
        crudlfap.DeleteView.clone(TaskMixin),
        crudlfap.UpdateView.clone(TaskMixin),
        TaskCreateView,
        crudlfap.DetailView.clone(
            authenticate=False,
        ),
        crudlfap.ListView.clone(
            authenticate=False,
            filter_fields=['user'],
            search_fields=['user__username', 'about'],
        ),
    ]

    def get_queryset(self, view):
        user = view.request.user

        if user.is_staff or user.is_superuser:
            return self.model.objects.all()
        elif not user.is_authenticated:
            return self.model.objects.none()

        return self.model.objects.filter(user=user)


TaskRouter().register()
