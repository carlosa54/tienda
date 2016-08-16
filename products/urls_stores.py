from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from .views import CategoryListView, CategoryDetailView, StoreDetailView

urlpatterns = [
    #url(r'^$', CategoryListView.as_view(), name='categories'),
    url(r'^(?P<slug>[\w-]+)$', StoreDetailView.as_view(), name='store_detail'),

]