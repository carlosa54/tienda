import braintree
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin, DetailView
from django.contrib.auth.forms import AuthenticationForm
from django.views.generic.edit import FormMixin
from django.views.generic.list import ListView
from django.contrib import messages
from django.core.mail import EmailMessage
from django.core.serializers.json import DjangoJSONEncoder
import decimal
import json

# Create your views here.
from products.models import Variation
from .models import Cart, CartItem
from orders.models import UserCheckout, Order, UserAddress
from orders.mixins import CartOrderMixin, LoginRequiredMixin

from orders.forms import GuestCheckoutForm
from carts.mixins import TokenMixin, CartUpdateAPIMixin, CartTokenMixin

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, filters
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.reverse import reverse as api_reverse
from rest_framework import status
from .serializers import CartItemSerializer, CheckoutSerializer
from orders.serializers import OrderSerializer, FinalizeOrderSerializer
import base64
import ast

class CheckoutFinalizeAPIView(TokenMixin,APIView):
	def get(self, request, format=None):
		order_token = request.GET.get('order_token')
		response = { }
		if order_token:
			checkout_id = self.parse_token(order_token).get("user_checkout_id")
			if checkout_id:
				checkout = UserCheckout.objects.get(id=user_checkout_id)
				client_token = checkout.get_client_token()
				response["client_token"] = client_token
			return Response(response)
		else:
			response["message"] = "This method is not allowed"
			return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)

	def post(self, request, format=None):
		data = request.data
		response = { }
		serializer = FinalizeOrderSerializer(data=data)
		if serializer.is_valid(raise_exception=True):
			request_data = serializer.data
			order_id = request_data.get("order_id")
			order = Order.objects.get(id=order_id)
			if not order.is_complete:
				order_total = order.order_total
				nonce = request_data.get("payment_method_nonce")
				if nonce:
					result = braintree.Transaction.sale({
					    "amount": order_total,
					    "payment_method_nonce": nonce,
					    "billing": {
						    "postal_code": "%s" %(order.billing_address.zipcode),
						    
						 },
					    "options": {
					        "submit_for_settlement": True
					    }
					})
					success = result.is_success
					if success:
						#result.transaction.id to order
						order.mark_completed(order_id=result.transaction.id)
						order.cart.is_complete()
						response["message"] = "Your order has been completed."
						response["final_order_id"] = order.order_id
						response["success"] = True
						#Sends email to client
						email = EmailMessage('Receipt of your Order', 'We have received your payment', to=[order.user.email])
						email.send()
					else:
						#messages.success(request, "There was a problem with your order.")
						messages.success(request, "%s" %(result.message))
						response["message"] = result.message
						response["success"] = False
			else:
				response["message"] = "Order has already been completed."
				response["success"] = False

		return Response(response)
	
class CheckoutAPIView(TokenMixin,APIView):

	def post(self, request, format=None):
		data = request.data
		serializer = CheckoutSerializer(data=data)
		if serializer.is_valid(raise_exception=True):
			data = serializer.data
			user_checkout_id = data.get("user_checkout_id")
			cart_id = data.get("cart_id")
			billing_address = data.get("billing_address")
			shipping_address = data.get("shipping_address")

			user_checkout = UserCheckout.objects.get(id=user_checkout_id)
			cart_obj = Cart.objects.get(id=cart_id)
			b_a = UserAddress.objects.get(id=billing_address)
			s_a = UserAddress.objects.get(id=shipping_address)
			order, created = Order.get_or_create(cart=cart_obj, user=user_checkout)
			if not order.is_complete:
				order.shipping_address = s_a
				order.billing_address = b_a
				order.save()
				order_data = {
					"order_id": order.id,
					"user_checkout_id": user_checkout_id
				}
				order_token = self.create_token(order_data)
		response = {
			"order_token": order_token
		}
		return Response(response)

	# def get(self, request, format=None):
	# 	data, cart_obj, response_status = self.get_cart_from_token()

	# 	user_checkout_id = request.GET.get("checkout_id")
	# 	try:
	# 		user_checkout = UserCheckout.objects.get(id=int(user_checkout_id))
	# 	except:
	# 		user_checkout = None

	# 	if user_checkout == None:
	# 		data = {
	# 			"message": "A user is required to continue."
	# 			}
	# 		response_status = status.HTTP_400_BAD_REQUEST
	# 		return Response(data, status=response_status)

	# 	if cart_obj:
	# 		if cart_obj.items.count() == 0:
	# 			data = {
	# 				"message": "Your cart is empty"
	# 			}
	# 			response_status = status.HTTP_400_BAD_REQUEST
	# 		else:
	# 			order, created = Order.objects.get_or_create(cart=cart_obj)
	# 			if not order.user:
	# 				order.user = user_checkout
	# 			order.save()
	# 			if order.is_complete:
	# 				order.cart.is_complete()
	# 				data = {
	# 				"message": "This order has been completed."
	# 				}
	# 				return Response(data)
	# 			data = OrderSerializer(order).data
	# 	return Response(data, status=response_status)

class CartAPIView(CartTokenMixin, CartUpdateAPIMixin, APIView):
	cart = None
	token_param = "token"
	def get_cart(self):
		data, cart_obj, response_status = self.get_cart_from_token()
		if cart_obj == None or not cart_obj.active:
			cart = Cart()
			cart.tax_percentage = 0.115
			if self.request.user.is_authenticated():
				cart.user = self.request.user
			cart.save()
			data = {
				"cart_id": cart.id
			}
			self.create_token(data)
			cart_obj = cart
		return cart_obj

	def get(self, request, format=None):
		cart = self.get_cart()
		self.cart = cart
		self.update_cart()
		items = CartItemSerializer(cart.cartitem_set.all(), many=True)
		data = {
			"cart": cart.id,
			"total": cart.total,
			"subtotal": cart.subtotal,
			"items": items.data,
			"token": self.token,
			"count": cart.items.count()
		}
		return Response(data)



if settings.DEBUG:
	braintree.Configuration.configure(braintree.Environment.Sandbox,
      merchant_id=settings.BRAINTREE_MERCHANT_ID,
      public_key=settings.BRAINTREE_PUBLIC,
      private_key=settings.BRAINTREE_PRIVATE)

class ItemCountView(View):
	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			cart_id = self.request.session.get("cart_id")
			if cart_id == None:
				count = 0
			else:
				cart = Cart.objects.get(id=cart_id)
				count = cart.items.count()
			request.session["cart_item_count"] = count
			return JsonResponse({"count": count})
		else:
			raise Http404

class CartTotalView(View):
	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			cart_id = self.request.session.get("cart_id")
			print cart_id
			if cart_id == None:
				total = str(0)
			else:
				cart = Cart.objects.get(id= cart_id)
				total = cart.subtotal
			total = json.dumps(total, cls=DecimalEncoder)
			request.session["cart_total"] = total
			
			print total
			return JsonResponse({"total":total})
		else:
			raise Http404

#Class for encoding a decimal to work with json
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return format(float(o), ".2f")
        return super(DecimalEncoder, self).default(o)

class CartView(SingleObjectMixin, View):
	model = Cart
	template_name = "carts/view.html"

	

	def get_object(self, *args, **kwargs):
		self.request.session.set_expiry(0)
		cart_id = self.request.session.get("cart_id")
		if cart_id == None:
			cart = Cart()
			cart.subtotal = 0
			cart.save()
			cart_id = cart.id
			self.request.session["cart_id"] = cart_id
		cart = Cart.objects.get(id=cart_id)
		if self.request.user.is_authenticated():
			cart.user = self.request.user
			cart.save()
		return cart

	def get(self, request, *args, **kwargs):
		cart = self.get_object()
		delete_item = request.GET.get("delete", False)
		item_id = request.GET.get("item")
		fromcart = request.GET.get("fromcart")
		store = request.GET.get("store")
		item_added = False
		if item_id:
			item_instance = get_object_or_404(Variation, id=item_id)
			qty = request.GET.get("qty",1)
			print qty
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
			if not request.is_ajax():
				return HttpResponseRedirect(reverse("cart"))		
		if request.is_ajax():
			try:
				total = cart_item.line_item_total
			except:
				total = None
			try:
				subtotal = cart_item.cart.subtotal
			except:
				subtotal = None

			try:
				cart_total = cart_item.cart.total
			except:
				cart_total = None

			try:
				tax_total = cart_item.cart.tax_total
			except:
				tax_total = None

			try:
				total_items = cart_item.cart.items.count()
			except:
				total_items = 0

			data = {
				"deleted": delete_item, 
				"item_added": item_added,
				"line_total": total,
				"subtotal": subtotal,
				"cart_total": cart_total,
				"tax_total": tax_total,
				"flash_message": flash_message,
				"total_items": total_items
			}
			return JsonResponse(data) 
		context = {
			"object": self.get_object(),
			"store": store
		}
		template = self.template_name
		return render(request,template,context)

class CheckoutView(CartOrderMixin, FormMixin, DetailView):
	model = Cart
	template_name = "carts/checkout_view.html"
	form_class = GuestCheckoutForm

	def get_object(self, *args, **kwargs):
		cart = self.get_cart()
		if cart == None:
			return None
		return cart

	def get_context_data(self, *args, **kwargs):
		context = super(CheckoutView, self).get_context_data(*args, **kwargs)
		user_can_continue = False
		user_check_id = self.request.session.get("user_checkout_id")
		if self.request.user.is_authenticated():
			user_can_continue = True
			user_checkout, created = UserCheckout.objects.get_or_create(email=self.request.user.email)
			user_checkout.user = self.request.user
			user_checkout.save()
			context["client_token"] = user_checkout.get_client_token()
			self.request.session["user_checkout_id"] = user_checkout.id
		elif not self.request.user.is_authenticated() and user_check_id == None:
			context["login_form"] = AuthenticationForm()
			context["next_url"] = self.request.build_absolute_uri()
		else:
			pass

		if user_check_id != None:
			user_can_continue = True
			if not self.request.user.is_authenticated(): #GUEST USER
				user_checkout_2 = UserCheckout.objects.get(id=user_check_id)
				context["client_token"] = user_checkout_2.get_client_token()
		
		#if self.get_cart() is not None:
		context["order"] = self.get_order()
		context["user_can_continue"] = user_can_continue
		context["form"] = self.get_form()
		return context

	def post(self, request, *args, **kwargs):
		self.object = self.get_object()
		form = self.get_form()
		if form.is_valid():
			email = form.cleaned_data.get("email")
			user_checkout, created = UserCheckout.objects.get_or_create(email=email)
			request.session["user_checkout_id"] = user_checkout.id
			return self.form_valid(form)
		else:
			return self.form_invalid(form)

	def get_success_url(self):
		return reverse("checkout")


	def get(self, request, *args, **kwargs):
		get_data = super(CheckoutView, self).get(request, *args, **kwargs)
		cart = self.get_object()
		if cart == None:
			return redirect("cart")
		new_order = self.get_order()
		user_checkout_id = request.session.get("user_checkout_id")
		if user_checkout_id != None:
			user_checkout = UserCheckout.objects.get(id=user_checkout_id)
			if new_order.billing_address == None or new_order.shipping_address == None:
			 	return redirect("order_address")
			new_order.user = user_checkout
			new_order.save()
		return get_data




class CheckoutFinalView(CartOrderMixin, View):
	def post(self, request, *args, **kwargs):
		order = self.get_order()
		order_total = order.order_total
		nonce = request.POST.get("payment_method_nonce")
		if nonce:
			result = braintree.Transaction.sale({
			    "amount": order_total,
			    "payment_method_nonce": nonce,
			    "billing": {
				    "postal_code": "%s" %(order.billing_address.zipcode),
				    
				 },
			    "options": {
			        "submit_for_settlement": True
			    }
			})
			if result.is_success:
				#result.transaction.id to order
				order.mark_completed(order_id=result.transaction.id)
				messages.success(request, "Thank you for your order.")
				#Sends email to client
				email = EmailMessage('Receipt of your Order', 'We have received your payment', to=[order.user.email])
				email.send()
				del request.session["cart_id"]
				del request.session["order_id"]
				del request.session["cart_total"]
			else:
				#messages.success(request, "There was a problem with your order.")
				messages.success(request, "%s" %(result.message))
				return redirect("checkout")

		return redirect("order_detail", pk=order.pk)

	def get(self, request, *args, **kwargs):
		return redirect("checkout")


class OrderDetail(DetailView):
	model = Order

	def dispatch(self, request, *args, **kwargs):
		try:
			user_check_id = self.request.session.get("user_checkout_id")
			user_checkout = UserCheckout.objects.get(id=user_check_id)
		except UserCheckout.DoesNotExist:
			user_checkout = UserCheckout.objects.get(user=request.user)
		except:
			user_checkout = None

		obj = self.get_object()
		if obj.user == user_checkout and user_checkout is not None:
			return super(OrderDetail, self).dispatch(request, *args, **kwargs)
		else:
			raise Http404




class OrderList(LoginRequiredMixin, ListView):
	queryset = Order.objects.all()

	def get_queryset(self):
		user_check_id = self.request.user.id
		user_checkout = UserCheckout.objects.get(user=user_check_id)
		return super(OrderList, self).get_queryset().filter(user=user_checkout)

