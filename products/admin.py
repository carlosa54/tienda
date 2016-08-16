from django.contrib import admin
from .models import Product, Variation, ProductImage, Category, Store, FrontImage
# Register your models here.


class ProductImageInline(admin.TabularInline):
	model = ProductImage
	extra = 0
	max_num = 10
	min_num = 1

class VariationInline(admin.TabularInline):
	model = Variation
	extra = 0
	max_num = 10

class ProductAdmin(admin.ModelAdmin):
	list_display = ['__unicode__', 'price']
	inlines = [
		ProductImageInline,
		VariationInline,
	]
	class Meta:
		model = Product

admin.site.register(Store)
admin.site.register(Product, ProductAdmin)
admin.site.register(Variation)
admin.site.register(ProductImage)
admin.site.register(Category)
admin.site.register(FrontImage)