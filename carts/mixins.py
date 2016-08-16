import ast
import base64
from rest_framework import status
from .models import Cart, CartItem, Variation
from django.shortcuts import render, get_object_or_404, redirect



class TokenMixin(object):

	def create_token(self, data_dict):
		if type(data_dict) == type(dict()):
			token = base64.b64encode(str(data_dict))
			self.token = token
			return token
		else:
			raise ValueError("Creating a token must be a dictionary.")

	def parse_token(self, token):
		if token is None:
			return {}
		try:
			token_decoded = base64.b64decode(token)
			token_dict = ast.literal_eval(token_decoded)
			return token_dict
		except:
			return {}

class CartTokenMixin(TokenMixin,object):
	token_param = "cart_token"
	token = None
	def get_cart_from_token(self):
		request = self.request
		response_status = status.HTTP_200_OK
		cart_token = request.GET.get(self.token_param)
		message = "This require a valid cart and cart token."
		cart_token_data = self.parse_token(cart_token)
		cart_id = cart_token_data.get("cart_id")

		try:
			cart = Cart.objects.get(id=int(cart_id))
		except:
			cart = None
		if cart == None:
			data = {
				"message": message,
				"success": False
			}
			response_status = status.HTTP_400_BAD_REQUEST
		else:
			self.token = cart_token
			data = {
				"cart": cart.id,
				"success": True
			}
		return data, cart, response_status

class CartUpdateAPIMixin(object):
	def update_cart(self, *args, **kwargs):
		request = self.request
		cart = self.cart
		if cart:
			delete_item = request.GET.get("delete", False)
			item_id = request.GET.get("item")
			fromcart = request.GET.get("fromcart")
			item_added = False
			if item_id:
				print item_id
				item_instance = get_object_or_404(Variation, id=item_id)
				qty = request.GET.get("qty",1)
				try:
					if int(qty) < 1:
						delete_item = True
				except:
					raise Http404
				cart_item, created = CartItem.objects.get_or_create(cart=cart, item=item_instance)
				if created:
					flash_message = "Successfully added to the cart"
					item_added = True
					cart_item.quantity = int(qty)
					cart_item.save()
				if delete_item:
					flash_message = "Item removed successfully."
					cart_item.delete()
				else:
					if not created:
						if fromcart:
							cart_item.quantity = int(qty)
							cart_item.save()
						else:
							cart_item.quantity += int(qty)
							cart_item.save()
						flash_message = "Quantity has been updated successfully."