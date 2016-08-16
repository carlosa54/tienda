from django.shortcuts import render
from django.views.generic.list import ListView
from django.views.generic.base import TemplateView
from orders.models import Order
from django_filters import FilterSet, DateFilter
import braintree
from datetime import datetime
from datetime import timedelta
import csv
from collections import OrderedDict
from django.conf import settings
from products.mixins import StaffRequiredMixin

# Create your views here.

class OrderFilter(FilterSet):
	month = DateFilter(name= 'paid_date')
	class Meta:
		model = Order
		fields = [
			'order_total',
			'status'
		]

def order_list(request):
	qs = Order.objects.all()
	f = OrderFilter(request.GET, queryset=qs)
	return render(request, "reports/reports.html", {"object_list": f})

class OrdersAuditView(StaffRequiredMixin,TemplateView):
	template_name = 'reports/date_select.html'

	def get_context_data(self, **kwargs):
		context = super(OrdersAuditView, self).get_context_data(**kwargs)
		start = self.request.GET.get("start")
		end = self.request.GET.get("end")
		context["success"] = False
		if start:
			orders = getSettledOrders(start, end)
			ids = []
			for id in orders:
				ids.append(Order.objects.get(order_id=id))
			context["orders"] = ids
			if not orders:
				context["success"] = True
		return context

def getSettledOrders(start, end):

	braintree.Configuration.configure(braintree.Environment.Sandbox,
      merchant_id=settings.BRAINTREE_MERCHANT_ID,
      public_key=settings.BRAINTREE_PUBLIC,
      private_key=settings.BRAINTREE_PRIVATE)

	#Searches the transactions made from start date to end date
	search_results = braintree.Transaction.search(
	  braintree.TransactionSearch.created_at.between(
	      start,
	    end
	  ),
	  (braintree.TransactionSearch.type == braintree.Transaction.Type.Sale),
	)

	orders = []
	for transaction in search_results.items:
		if transaction.status != 'settled':
			orders.append(transaction.id)
	return orders