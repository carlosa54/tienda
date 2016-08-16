from rest_framework import serializers
from products.models import Variation
from .models import CartItem
from .mixins import TokenMixin
from carts.models import Cart
from orders.models import UserAddress

class CheckoutSerializer(TokenMixin,serializers.Serializer):
	checkout_token = serializers.CharField()
	user_checkout_id = serializers.IntegerField(required=False)
	billing_address = serializers.IntegerField()
	shipping_address = serializers.IntegerField()
	cart_token = serializers.CharField()
	cart_id = serializers.IntegerField(required=False)

	def validate(self, data):
		checkout_token = data.get("checkout_token")
		billing_address = data.get("billing_address")
		shipping_address = data.get("shipping_address")
		cart_token = data.get("cart_token")


		cart_token_data = self.parse_token(cart_token)
		cart_id = cart_token_data.get("cart_id")
		print cart_token_data

		checkout_data = self.parse_token(checkout_data)
		user_checkout_id = checkout_data.get("cart_id")
		print checkout_data

		try:
			user_checkout = UserCheckout.objects.get(id=int(user_checkout_id))
			data["user_checkout_id"] = user_checkout.id
		except:
			raise serializers.ValidationError("This is not a valid user")

		try:
			cart_obj = Cart.objects.get(id=cart_id)
			data["cart_id"] = cart_obj.id
		except:
			raise serializers.ValidationError("This is not a valid user")

		try:
			billing_obj = UserAddress.objects.get(user=user_checkout, id=int(billing_address))

		except:
			raise serializers.ValidationError("This is not a valid address for this user")

		try:
			shipping_obj = UserAddress.objects.get(user=user_checkout, id=int(shipping_address))
		except:
			raise serializers.ValidationError("This is not a valid address for this user")

		return data

	def validate_checkout_token(self, value):
		if type(value) == type(str()):
			return value
		else:
			raise serializers.ValidationError("This is not a valid token")


class CartVariationSerializer(serializers.ModelSerializer):
	product = serializers.SerializerMethodField()
	class Meta:
		model = Variation
		fields = [
			"id",
			"title",
			"price",
			"product",
		]
	def get_product(self, obj):
		return obj.product.title

class CartItemSerializer(serializers.ModelSerializer):
	# item = CartVariationSerializer(read_only=True)
	item = serializers.SerializerMethodField()
	item_title = serializers.SerializerMethodField()
	product = serializers.SerializerMethodField()
	price = serializers.SerializerMethodField()
	class Meta:
		model = CartItem
		fields = [
			"item",
			"item_title",
			"price",
			"product",
			"quantity",
			"line_item_total"
		]
	def get_item(self, obj):
		return obj.item.id

	def get_item_title(self, obj):
		return "%s %s" %(obj.item.product.title, obj.item.title)

	def get_product(self, obj):
		return obj.item.product.id

	def get_price(self, obj):
		return obj.item.price
