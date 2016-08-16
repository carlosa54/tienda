from rest_framework import serializers
from .models import UserAddress, Order
from carts.mixins import TokenMixin

class FinalizeOrderSerializer(serializers.Serializer):
	order_token = serializers.CharField()
	order_id = serializers.IntegerField(required=False)
	user_checkout_id = serializers.IntegerField(required=False)
	payment_method_nonce = serializers.CharField()

	def validate(self, data):
		order_token = data.get("order_token")
		order_data = self.parse_token(order_token)
		order_id = order_data.get("order_id")
		user_checkout_id = order_data.get("user_checkout_id")

		payment_method_nonce = data.get("payment_method_nonce")

		try:
			order_obj = Order.objects.get(id=order_id, user__id=user_checkout_id)
			data["order_id"] = order_id
			data["user_checkout_id"] = user_checkout_id
		except:
			raise serializers.ValidationError("This is not a valid order for this user.")

		if payment_method_nonce == None:
			raise serializers.ValidationError("This is not a valid nonce.")

		return data


class OrderDetailSerializer(serializers.ModelSerializer):
	url = serializers.HyperlinkedIdentityField(view_name="order_detail_api")
	subtotal = serializers.SerializerMethodField()
	class Meta:
		model = Order
		fields = [
			"order_id",
			"user",
			"shipping_address",
			"billing_address",
			"shipping_total_price",
			"subtotal",
			"order_total"
		]
	def get_subtotal(self, obj):
		return obj.cart.subtotal

class OrderSerializer(serializers.ModelSerializer):
	subtotal = serializers.SerializerMethodField()
	user_id = serializers.SerializerMethodField()
	class Meta:
		model = Order
		fields = [
			"id",
			"user",
			"shipping_address",
			"billing_address",
			"shipping_total_price",
			"subtotal",
			"order_id",
			"order_total",
			"user_id"
		]
	def get_subtotal(self, obj):
		return obj.cart.subtotal
	def get_user_id(self, obj):
		return obj.user.user.id

class UserAddressSerializer(serializers.ModelSerializer):
	class Meta:
		model = UserAddress
		fields = [
			"user",
			"type",
			"street",
			"city",
			"zipcode",
		]