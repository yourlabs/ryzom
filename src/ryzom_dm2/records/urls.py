from django.urls import path

from . import views

app_name = 'records'
urlpatterns = [
    path('', views.RecordIndex.as_view(), name='index'),
    # ex: /records/5/
    path('<int:pk>/', views.RecordDetail.as_view(), name='detail'),
    path('<int:pk>/update', views.RecordUpdate.as_view(), name='update'),
    path('create', views.RecordCreate.as_view(), name='create'),
    path('<int:pk>/delete', views.RecordDelete.as_view(), name='delete'),
]
