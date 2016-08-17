from django.contrib import admin
from .models import UserCheckout, UserAddress, Order
# Register your models here.

from django.contrib.contenttypes.models import ContentType

class ContentTypeAdmin(admin.ModelAdmin):
	list_display = ['name', 'app_label']
	fieldsets = (
	('', {
		'classes': ('',),
		'fields': ('name', 'app_label')
	}),
	)

admin.site.register(ContentType, ContentTypeAdmin)

admin.site.register(UserCheckout)

admin.site.register(UserAddress)

admin.site.register(Order)




