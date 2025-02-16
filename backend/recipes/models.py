from django.core.validators import MinValueValidator
from django.db import models

from foodgram.constants import (
    INGREDIENT_NAME_LENGTH,
    MEASUREMENT_UNITS_LENGTH,
    MIN_COOKING_TIME,
    MIN_INGREDIENT_AMOUNT,
    RECIPE_NAME_LENGTH,
    TAG_NAME_LENGTH,
    TAG_SLUG_LENGTH,
)
from users.models import User


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField(
        max_length=INGREDIENT_NAME_LENGTH,
        verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=MEASUREMENT_UNITS_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique__ingredient'
            )
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель тега."""
    name = models.CharField(
        max_length=TAG_NAME_LENGTH,
        unique=True,
        verbose_name='Название тега'
    )
    slug = models.SlugField(
        unique=True,
        max_length=TAG_SLUG_LENGTH,
        verbose_name='Слаг'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=RECIPE_NAME_LENGTH,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение'
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_COOKING_TIME)
        ],
        verbose_name='Время приготовления'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата и время публикации'
    )

    class Meta:
        default_related_name = 'recipes'
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель связи рецепта и ингредиента."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_INGREDIENT_AMOUNT),
        ],
        verbose_name='Количество'
    )

    class Meta:
        default_related_name = 'recipe_ingredients'
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_recipe_ingredient'
            )
        ]
        verbose_name = 'Связь Рецепт/Ингредиент'
        verbose_name_plural = 'Связи Рецепты/Ингридиенты'

    def __str__(self):
        return f'{self.recipe.name} - {self.ingredient.name}'


class RecipeTag(models.Model):
    """Модель связи рецепта и тега."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег'
    )

    class Meta:
        default_related_name = 'recipe_tags'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'tag'],
                name='unique_recipe_tag'
            )
        ]
        verbose_name = 'Связь Рецепт/Тег'
        verbose_name_plural = 'Связи Рецепты/Теги'

    def __str__(self):
        return f'{self.recipe.name} - {self.tag.name}'


class AbstractFavoriteShoppingCart(models.Model):
    """Абстрактная модель для избранногоизбранных рецптов и списка покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='%(app_label)s_%(class)s_unique_user_recipe'
            ),
        ]


class FavoriteRecipe(AbstractFavoriteShoppingCart):
    """Модель избранных рецептов."""

    class Meta(AbstractFavoriteShoppingCart.Meta):
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'favorite_recipes'

    def __str__(self):
        return f'{self.recipe} избранный рецепт у пользователя {self.user}'


class ShoppingCartRecipe(AbstractFavoriteShoppingCart):
    """Модель списка покупок."""

    class Meta(AbstractFavoriteShoppingCart.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'cart_recipes'

    def __str__(self):
        return (f'Рецепт - {self.recipe} '
                f'в списке покупок пользователя {self.user}')
