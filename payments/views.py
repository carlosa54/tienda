from django.shortcuts import render, redirect
from django.views.generic import TemplateView
import paypalrestsdk
from orders.models import Order
from orders.mixins import CartOrderMixin
import json
from django.contrib import messages
# Create your views here.

class PaymentCheckoutView(CartOrderMixin, TemplateView):

	template_name = 'payments/pay.html'
	def get(self, request, *args, **kwargs):

		if request.GET.get('paymentId'):
			payment = paypalrestsdk.Payment.find(request.GET.get('paymentId'))

			if payment.execute({"payer_id": request.GET.get('PayerID')}):
				print("Payment execute successfully")
			else:
				print(payment.error)
		print 'GET'
		context = {
			"test": "dummy"
		}
		template = self.template_name
		return render(request,template,context)

	def post(self, request, *args, **kwargs):
		print 'hello im in PayPal payment'
		order_id = request.POST.get("order_id")
		order = Order.objects.get(id=order_id)
		template = self.template_name
		items = {"items": [] }
		for item in order.cart.cartitem_set.all():
			items["items"].append(
				{
					"quantity": item.quantity,
					"name": item.item.get_title(),
					"price": str(item.item.price),
					"currency": "USD",
					"description": item.item.product.description,
				})
		
		payment = paypalrestsdk.Payment({
				"intent": "sale",
				"redirect_urls": 
				{
						"return_url": "http://127.0.0.1:8000/checkout",
   						"cancel_url": "http://127.0.0.1:8000"
  					},
  				"payer":
					  {
					    "payment_method": "paypal"
					  },
				"transactions": [
					  {
					    "amount":
					    {
					      "total": str(order.order_total) ,
					      "currency": "USD",
					      "details":
					      {
					        "subtotal": str(order.cart.subtotal),
					        "shipping": str(order.shipping_total_price),
					      }
					    },
					    "item_list": items,
					    #"description": "The payment transaction description.",
					    "invoice_number": str(order.id),
					  }]
			})
		if payment.create():
			for link in payment.links:
				if link.method == "REDIRECT":
					redirect_url = str(link.href)
					print("Redirect for approval: %s" % (redirect_url))
			order.mark_completed()
			messages.success(request, "Thank you for your order.")
			del request.session["cart_id"]
			del request.session["order_id"]
			del request.session["cart_total"]
			return redirect(redirect_url)
  			print("Payment created successfully")
		else:
  			print(payment.error)

		context = {
			"test": "dummy"
		}
		return render(request, template, context)
