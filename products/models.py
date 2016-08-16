from django.db import models
from django.core.urlresolvers import reverse
from django.db.models.signals import post_save
from django.utils.safestring import mark_safe
from django.utils.text import slugify

# Create your models here.
class Store(models.Model):
	name = models.CharField(max_length=120)
	slug = models.SlugField(unique=True)
	active = models.BooleanField(default=True)
	
	def __unicode__(self):
		return self.name

	def get_absolute_url(self):
		return reverse("category_detail", kwargs={"slug": self.slug})



class ProductQuerySet(models.query.QuerySet):
	def active(self):
		return self.filter(active=True)

class ProductManager(models.Manager):
	def get_queryset(self):
		return ProductQuerySet(self.model, using=self.db)
 
	def all(self, *args, **kwargs):
		return self.get_queryset().active()

class VariationQuerySet(models.query.QuerySet):
	def listVari(self):
		return self.exclude(title = "Default")

class VariationManager(models.Manager):
	def get_queryset(self):
		return VariationQuerySet(self.model, using=self.db)

	def allVariations(self, *args, **kwargs):
		return self.get_queryset().listVari()

class Product(models.Model):
	title = models.CharField(max_length=120)
	description = models.TextField(blank = True, null=True)
	price = models.DecimalField(decimal_places=2, max_digits=20)
	active = models.BooleanField(default = True)
	categories = models.ManyToManyField("Category", blank=True)
	store = models.ManyToManyField("Store", blank=True)

	objects = ProductManager()

	def __unicode__(self):
		return self.title

	def get_absolute_url(self):
		return reverse("product_detail", kwargs= {"pk": self.pk})

	def get_image_url(self):
		img = self.productimage_set.first()
		if img:
			return img.image.url
		else:
			return img


class Variation(models.Model):
	product = models.ForeignKey(Product)
	title = models.CharField(max_length= 120)
	price = models.DecimalField(decimal_places=2, max_digits=20)
	sale_price = models.DecimalField(decimal_places=2, max_digits=20, null=True, blank=True)
	active = models.BooleanField(default = True)
	inventory = models.IntegerField(null = True, blank= True)

	objects = VariationManager()

	def __unicode__(self):
		return self.title


	def get_price(self):
		if self.sale_price is not None:
			return self.sale_price
		else:
			return self.price

	def get_html_price(self):
		if self.sale_price is not None:
			html_text = "<span class='sale_price'>%s</span> <span class='og-price'>%s</span>" %(self.sale_price, self.price)
		else:
			html_text = "<span class='price'>%s</span>" %(self.price)
		return mark_safe(html_text)

	def get_absolute_url(self):
		return self.product.get_absolute_url()

	def add_to_cart(self):
		return "%s?item=%s&qty=1" %(reverse("cart"), self.id)

	def remove_from_cart(self):
		return "%s?item=%s&qty=1&delete=True" %(reverse("cart"), self.id)

	def get_title(self):
		if self.title == 'Default':
			return self.product.title
		else:
			return "%s - %s" %(self.product.title, self.title)

def product_post_saved_receiver(sender, instance, created, *args, **kwargs):
	product = instance
	variations = product.variation_set.all()
	if variations.count() == 0:
		new_var = Variation()
		new_var.product = product
		new_var.title = "Default"
		new_var.price = product.price
		new_var.save()

post_save.connect(product_post_saved_receiver, sender= Product)

def image_upload_to(instance, filename):
	title = instance.product.title
	slug = slugify(title)
	file_extension = filename.split(".")[1]
	new_filename = "%s.%s" %(instance.id, file_extension)
	return "products/%s/%s" %(slug, new_filename)

class ProductImage(models.Model):
	product = models.ForeignKey(Product)
	image = models.ImageField(upload_to = image_upload_to)

	def __unicode__(self):
		return self.product.title

class Category(models.Model):
	title = models.CharField(max_length=120, unique=True)
	slug = models.SlugField(unique=True)
	description = models.TextField(null=True, blank=True)
	active = models.BooleanField(default=True)
	timestamp = models.DateTimeField(auto_now = True)

	def __unicode__(self):
		return self.title

	def get_absolute_url(self):
		return reverse("category_detail", kwargs={"slug": self.slug})
		
def image_upload_to_featured(instance, filename):
	title = instance.product.title
	slug = slugify(title)
	basename, file_extension = filename.split(".")
	new_filename = "%s-%s.%s" %(slug, instance.id, file_extension)
	return "products/%s/featured/%s" %(slug, new_filename)


def image_upload_to_front(instance, filename):
	title = instance.store.name
	basename, file_extension = filename.split(".")
	new_filename = "%s.%s" %(instance.id, file_extension)
	return "stores/%s" %(new_filename)


class FrontImage(models.Model):
	store = models.ForeignKey(Store)
	image = models.ImageField(upload_to = image_upload_to_front)
	active = models.BooleanField(default=True)

	def __unicode__(self):
		return self.store.name






	