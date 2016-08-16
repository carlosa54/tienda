from django.shortcuts import render
from django.views.generic.list import ListView
from orders.models import Order
from django_filters import FilterSet
from django.views.generic.base import View
from django.views.generic import TemplateView

# Create your views here.

class OrderFilter(FilterSet):
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

class DashboardView(TemplateView):
	template_name = 'dashboard/dashboard.html'