from django_filters import (
    FilterSet,
    ModelMultipleChoiceFilter,
)
from django_filters.rest_framework import BooleanFilter
from rest_framework.filters import SearchFilter

from recipes.models import (
    Recipe,
    ShoppingCartRecipe,
    Tag,
)


class IngredientFilter(SearchFilter):
    """Фильтр ингредиентов."""
    search_param = 'name'


class RecipeFilter(FilterSet):
    """Фильтр рецептов."""
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )
    is_in_shopping_cart = BooleanFilter(
        method='filter_user_recipes')
    is_favorited = BooleanFilter(method='filter_user_recipes')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_user_recipes(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous:
            return queryset.none()
        filter_mapping = {
            "is_favorited": "favorite_recipes__user",
            "is_in_shopping_cart": "id__in"
        }
        if name == "is_in_shopping_cart":
            related_recipes = ShoppingCartRecipe.objects.filter(
                user=user
            ).values_list('recipe', flat=True)
            return (
                queryset.filter(id__in=related_recipes) if value
                else queryset
            )
        return (
            queryset.filter(**{filter_mapping[name]: user}) if value
            else queryset
        )
