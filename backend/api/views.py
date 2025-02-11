import hashlib

from django.core.cache import cache
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse

from django_filters import CharFilter, FilterSet, ModelMultipleChoiceFilter
from django_filters.rest_framework import DjangoFilterBackend

from djoser.views import UserViewSet as DjoserViewSet

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from foodgram.constants import PAGINATION_PER_PAGE
from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCartRecipe,
    Tag,
)
from users.models import Subscription, User

from .serializers import (
    AvatarSerializer,
    CreateSubscriptionSerializer,
    CreateUpdateRecipeSerializer,
    CreateUserSerializer,
    FavoriteRecipeSerializer,
    IngredientSerializer,
    RecipeSerializer,
    ShoppingCartRecipeSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserSerializer,
)


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Пермишен: автор может редактировать, остальные только читать."""

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )


class CustomPagination(PageNumberPagination):
    """Кастомная пагинация."""

    page_size = PAGINATION_PER_PAGE
    page_size_query_param = 'limit'


class IngredientFilter(FilterSet):
    """Фильтр ингредиентов."""
    name = CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    """Фильтр рецептов."""
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )
    is_in_shopping_cart = CharFilter(
        method='filter_user_recipes')
    is_favorited = CharFilter(method='filter_user_recipes')

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


class UserViewSet(DjoserViewSet):
    """ViewSet для работы с пользователями."""
    queryset = User.objects.all()
    serializer_class = CreateUserSerializer
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in {'list', 'retrieve', 'me'}:
            return UserSerializer
        return super().get_serializer_class()

    @action(
        detail=False, methods=['get'], permission_classes=[IsAuthenticated],
        url_path='me', url_name='me'
    )
    def me(self, request):
        return Response(self.get_serializer(request.user).data)

    @action(
        detail=False, methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar', url_name='avatar'
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = AvatarSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(
        detail=False, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path=r'(?P<id>\d+)/subscribe', url_name='subscribe'
    )
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)

        if request.method == 'POST':
            serializer = CreateSubscriptionSerializer(
                data={'user': user.id, 'author': author.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = Subscription.objects.filter(
            user=user,
            author=author
        ).delete()
        if not deleted:
            return Response(
                {"error": f"Подписка на {author.username} отсутствует"},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['get'], permission_classes=[IsAuthenticated],
        url_path='subscriptions', url_name='subscriptions'
    )
    def get_subscriptions(self, request):
        user = request.user
        subscribes = User.objects.filter(subscribers__user=user)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(subscribes, request)

        if page is not None:
            serializer = SubscriptionSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return paginator.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            subscribes,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с тегами."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с рецептами."""
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        return (
            RecipeSerializer if self.request.method
            in permissions.SAFE_METHODS
            else CreateUpdateRecipeSerializer
        )

    @action(
        methods=['GET'],
        url_path='get-link',
        detail=True
    )
    def get_short_link(self, request, pk):
        full_url = request.build_absolute_uri(
            reverse('recipe-detail', args=[pk])
        )
        hash_object = hashlib.md5(full_url.encode())
        short_code = hash_object.hexdigest()[:8]
        cache.set(short_code, full_url, timeout=60 * 60 * 24)
        base_url = request.build_absolute_uri('/s/').rstrip('/')
        short_link = f"{base_url}/{short_code}"
        return Response({"short-link": short_link}, status=status.HTTP_200_OK)

    def _toggle_recipe_relation(self, request, id, model, serializer_class):
        recipe = get_object_or_404(Recipe, id=id)
        user = request.user
        if request.method == 'POST':
            serializer = serializer_class(
                data={'user': user.id, 'recipe': recipe.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            full_data = RecipeSerializer(
                recipe,
                context={'request': request}
            ).data
            short_data = {key: full_data[key] for key in (
                'id',
                'name',
                'image',
                'cooking_time'
            )}
            return Response(short_data, status=status.HTTP_201_CREATED)
        if not model.objects.filter(user=user, recipe=recipe).exists():
            return Response({"error": "Рецепт не найден в списке"},
                            status=status.HTTP_400_BAD_REQUEST
                            )
        model.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=[IsAuthenticated],
            methods=['post', 'delete'], url_path=r'(?P<id>\d+)/favorite',
            url_name='favorite')
    def add_recipe_to_favorite(self, request, id):
        return self._toggle_recipe_relation(
            request,
            id,
            FavoriteRecipe,
            FavoriteRecipeSerializer
        )

    @action(detail=False, permission_classes=[IsAuthenticated],
            methods=['post', 'delete'], url_path=r'(?P<id>\d+)/shopping_cart',
            url_name='shopping_cart')
    def add_recipe_to_shopping_cart(self, request, id):
        return self._toggle_recipe_relation(
            request,
            id,
            ShoppingCartRecipe,
            ShoppingCartRecipeSerializer
        )

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__cart_recipes__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            ingredient_amount=Sum('amount')
        ).order_by('ingredient__name')

        shopping_list = '\n'.join([
            f"{item['ingredient__name']} - {item['ingredient_amount']} "
            f"{item['ingredient__measurement_unit']}"
            for item in ingredients
        ])

        response = HttpResponse(
            f"Список покупок:\n\n{shopping_list}",
            content_type="text/plain"
        )
        response["Content-Disposition"] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response
