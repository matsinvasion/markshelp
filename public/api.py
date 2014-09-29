from tastypie.resources import ModelResource,ALL,ALL_WITH_RELATIONS
from items.models import Item
from orders.models import OrderList, Order
from tastypie import fields
from tastypie.authorization import Authorization, DjangoAuthorization
from django.contrib.auth.models import User
from django.core import urlresolvers
from django.http import HttpResponseRedirect
import datetime
from tastypie.exceptions import BadRequest
from django.db import IntegrityError
from tastypie_extras.exceptions import CustomBadRequest
from django.contrib.auth.hashers import make_password
from tastypie.authentication import ApiKeyAuthentication
from django.db import models
from registration.models import RegistrationProfile
from registration import signals
from django.contrib.sites.models import Site, RequestSite



#Our resources

class UserResource(ModelResource):
  """GET and UPDATE User"""
  class Meta:
    queryset = User.objects.all()
    resource_name = "user"
    authorization = Authorization()
    excludes = ['is_active','is_staff','is_superuser','date_joined','last_login']
    always_return_data =True
    filtering={
              'username':ALL,
              'id':ALL,
    }


  #django-registration does the registering | consistency
  @staticmethod
  def user_registration(username,email,password,site):
    #use static method since we don't need an instance
    #without it we get a type error.
    new_user = RegistrationProfile.objects.create_inactive_user(username,email,password,site)

    return new_user


  #customize input
#  def hydrate(self,bundle):

#    return bundle

  def obj_create(self,bundle,**kwargs):
    #create inactive user and send email
    #have Django registration do this for us
    raw_password,email,username = bundle.data["password"],bundle.data["email"],bundle.data["username"]
    if Site._meta.installed:
      site = Site.objects.get_current()
    else:
      site = RequestSite(bundle.request)
    new_user=self.user_registration(username,email,raw_password,site)
    signals.user_registered.send(sender=self.__class__,
                                        user=new_user,
                                        request=bundle.request)
    return bundle



  #return response with current user object
  #used by to create lists with angularjs
  def authorized_read_list(self,object_list,bundle):
    current_user = object_list.filter(id=bundle.request.user.id)
    return current_user
#curl -v -X POST -d '{"email":"gwen@gmail.com","username":"gwen","password":"model"}' -H "Content-Type:application/json" http://127.0.0.1:8000/api/v1/user/



#curl -v -X POST -d '{"email":"gwen@gmail.com","username":"gwen","password":"model"}' -H "Content-Type:application/json" http://127.0.0.1:8000/api/v1/user/



class OrderResource(ModelResource):
  #since tastypie has no way to render relationships,use UserResource

  created_by =fields.ToOneField(UserResource,'created_by',null=True,blank=True)
  modified_by = fields.ToOneField(UserResource,'modified_by',null=True,blank=True)

  class Meta:
    queryset = Order.objects.all()
    resource_name = 'order'
    authorization =Authorization()
    always_return_data = True
    #we can do some filtering on this resource



class OrderListResource(ModelResource):
  #since tastypie has no way to render relationships,use UserResource
  #we need a User field so we can be able to query the lists created by a user
  user = fields.ToOneField(UserResource,'user',null=True,blank=True,full=True)
  item = fields.ToManyField('public.api.ItemResource','item_set',full=True,null=True,blank=True)
  order = fields.ToOneField(OrderResource,'order',null=True,blank=True,full=True)
  created_by = fields.ToOneField(UserResource,'created_by',null=True,blank=True)
  modified_by = fields.ToOneField(UserResource,'modified_by',null=True,blank=True)
  class Meta:
    queryset = OrderList.objects.all().order_by('-created_on')
    resource_name ="orderlist"
    authorization = Authorization()
    always_return_data = True
    filtering={
              'user':ALL_WITH_RELATIONS,
              'is_active':ALL,
    }
    limit =0

  #avail a created list to session
  #operations after this assume
  #user will keep editing this list
  def dehydrate(self,bundle):
    bundle.request.session["current_list_title"] = bundle.data["title"]
    #always returns a bundle
    return bundle


class ItemResource(ModelResource):
  #define these fields on resource,
  #cannot make request without them since, tastypie doesnot know them beforehand
  orderlist = fields.ToOneField(OrderListResource,'orderlist',null=True,blank=True)
  created_by = fields.ToOneField(UserResource,'created_by',null=True,blank=True)
  modified_by = fields.ToOneField(UserResource,'modified_by',null=True,blank=True)

  class Meta:
    queryset = Item.objects.all()
    resource_name = 'list_item'
    authorization = Authorization()
    always_return_data = True

  def dehydrate(self,bundle):
    bundle.request.session["item_stamp"] = bundle.data["item_stamp"]
    return bundle