from .views import home, checkout,order_confirmation
from django.conf.urls import patterns, include, url

urlpatterns = patterns('',

    url(r'^checkout/$',checkout,name="checkout"),
    url(r'^confirmation/$',order_confirmation,name="confirmation")


)