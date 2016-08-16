from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination

class ProductPagination(LimitOffsetPagination):
	default_limit = 10
	max_limit = 500
	limit_query_param = "limit"
	offset_query_param = "offset"