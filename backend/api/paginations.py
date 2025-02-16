from rest_framework.pagination import PageNumberPagination

from foodgram.constants import PAGINATION_PER_PAGE


class LimitPagination(PageNumberPagination):
    """Кастомная пагинация."""

    page_size = PAGINATION_PER_PAGE
    page_size_query_param = 'limit'
