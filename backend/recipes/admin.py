from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeTag,
    ShoppingCartRecipe,
    Tag
)


class BaseFavoriteShoppingAdmin(admin.ModelAdmin):
    """Базовый класс для избранных рецептов и списка покупок."""
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user', 'recipe')
    list_filter = ('user', 'recipe')


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(BaseFavoriteShoppingAdmin):
    """Админка избранных рецептов."""


@admin.register(ShoppingCartRecipe)
class ShoppingCartRecipeAdmin(BaseFavoriteShoppingAdmin):
    """Админка списка покупок."""


class IngredientsInline(admin.TabularInline):
    """Инлайн построчного представления ингредиентов в админке рецептов."""
    model = RecipeIngredient
    extra = 1
    min_num = 1


class TegsInline(admin.TabularInline):
    """Инлайн построчного представления тегов в админке рецептов."""
    model = RecipeTag
    extra = 1
    min_num = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """"Админка тегов."""
    search_fields = ('name', 'slug')
    list_display = ('id', 'name', 'slug')
    list_display_links = ('name', 'slug')
    list_filter = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка ингредиентов."""
    search_fields = ('name', 'measurement_unit')
    list_display = ('id', 'name', 'measurement_unit')
    list_display_links = ('name', 'measurement_unit')
    list_filter = ('name', 'measurement_unit')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка рецептов."""
    search_fields = ('name', )
    list_display = (
        'id',
        'name',
        'get_author',
        'get_image',
        'get_text',
        'get_ingredients',
        'get_tags',
        'pub_date',
        'cooking_time',
        'get_favorite_count',
    )
    list_filter = ('name', 'tags',)
    filter_horizontal = ('tags',)
    inlines = (IngredientsInline, TegsInline)

    @admin.display(description='Автор')
    def get_author(self, obj):
        return obj.author.username

    @admin.display(description='Изображение')
    def get_image(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="80" height="60" '
                f'style="object-fit: cover; border-radius: 4px;">'
            )
        return '—'

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        return ', '.join(
            ingredient.name for ingredient in obj.ingredients.all()
        )

    @admin.display(description='Теги')
    def get_tags(self, obj):
        return ', '.join(tag.name for tag in obj.tags.all())

    @admin.display(description='Текст')
    def get_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    @admin.display(
        description='Количество добавлений в избранное'
    )
    def get_favorite_count(self, object):
        return object.favorite_recipes.count()


admin.site.empty_value_display = 'Не задано'
