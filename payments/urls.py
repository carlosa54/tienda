from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from .views import PaymentCheckoutView

urlpatterns = [
    url(r'^$', PaymentCheckoutView.as_view(), name='payment'),
]