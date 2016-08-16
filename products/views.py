from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.db.models import Q
from .models import Product, Variation, Category, Store
from .forms import VariationInventoryForm, VariationInventoryFormSet
from .mixins import StaffRequiredMixin
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, filters
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.reverse import reverse as api_reverse
from .serializers import CategorySerializer, ProductSerializer, ProductDetailSerializer
from .pagination import ProductPagination
from .filters import ProductFilter
# Create your views here.

#API CBVS


class APIHomeView(APIView):
	def get(self, request, format=None):
		data = {
			"auth": {
				"login_url":  api_reverse("auth_login_api", request=request),
				"refresh_url":  api_reverse("refresh_token_api", request=request), 
				"user_checkout":  api_reverse("user_checkout_api", request=request), 
			},
			"address": {
				"url": api_reverse("user_address_list_api", request=request),
				"create":   api_reverse("user_address_create_api", request=request),
			},
			"checkout": {
				"cart": api_reverse("cart_api", request=request),
				"checkout": api_reverse("checkout_api", request=request),
				"finalize": api_reverse("checkout_finalize_api", request=request),
			},
			"products": {
				"count": Product.objects.all().count(),
				"url": api_reverse("products_api", request=request)
			},
			"categories": {
				"count": Category.objects.all().count(),
				"url": api_reverse("categories_api", request=request)
			},
			"orders": {
				"url": api_reverse("orders_api", request=request),
			}
		}
		return Response(data)


class CategoryListAPIView(generics.ListAPIView):
	queryset = Category.objects.all()
	serializer_class = CategorySerializer

class CategoryRetrieveAPIView(generics.RetrieveAPIView):
	permission_classes = [IsAuthenticated]
	queryset = Category.objects.all()
	serializer_class = CategorySerializer

class ProductListAPIView(generics.ListAPIView):
	queryset = Product.objects.all()
	serializer_class = ProductSerializer
	filter_backends = [filters.SearchFilter, filters.OrderingFilter, filters.DjangoFilterBackend]
	search_fields = ["title","description"]
	ordering_fields = ["title", "id"]
	filter_class = ProductFilter
	# pagination_class = ProductPagination

class ProductRetrieveAPIView(generics.RetrieveAPIView):
	queryset = Product.objects.all()
	serializer_class = ProductDetailSerializer




#CBVS

class StoreDetailView(DetailView):
	model = Store
	
class CategoryListView(ListView):
	model = Category
	template_name = "products/product_list.html"

class CategoryDetailView(DetailView):
	model = Category
	
class ProductDetailView(DetailView):
	model = Product

class VariationListView(StaffRequiredMixin, ListView):
	model = Variation

	def get_context_data(self, *args, **kwargs):
		context = super(VariationListView,self).get_context_data(*args, **kwargs)
		context["formset"] = VariationInventoryFormSet(queryset= self.get_queryset())
		return context

	def get_queryset(self, *args, **kwargs):
		product_pk = self.kwargs.get("pk")
		if product_pk:
			product = get_object_or_404(Product, pk=product_pk)
			queryset= Variation.objects.filter(product= product)
		return queryset

	def post(self,request, *args, **kwargs):
		formset = VariationInventoryFormSet(request.POST, request.FILES)
		print request.POST
		if formset.is_valid():
			formset.save(commit=False)
			for form in formset:
				new_item = form.save(commit=False)
				if new_item.title:
					product_pk = self.kwargs.get("pk")
					product = get_object_or_404(Product, pk=product_pk)
					new_item.product = product
					new_item.save()
			messages.success(request, "Inventory has been updated.")
			return redirect("products")
		raise Http404

class ProductListView(ListView):
	model = Product

	def get_context_data(self, *args, **kwargs):
		context = super(ProductListView,self).get_context_data(*args, **kwargs)
		context["query"] = self.request.GET.get("q")
		return context

	def get_queryset(self, *args, **kwargs):
		qs = super(ProductListView, self).get_queryset(*args, **kwargs)
		query = self.request.GET.get("q")
		if query:
			qs = self.model.objects.filter(
				Q(title__icontains=query) | Q(description__icontains= query))
		return qs


