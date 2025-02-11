from django.contrib.auth.password_validation import validate_password
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated

from foodgram.constants import PASSWORD_LENGTH
from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeTag,
    ShoppingCartRecipe,
    Tag
)
from users.models import User, Subscription


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя."""

    is_subscribed = serializers.SerializerMethodField(
        method_name='get_is_subscribed'
    )
    avatar = Base64ImageField(allow_null=True, required=False)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, author):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and user.subscription.filter(author=author).exists()
        )


class CreateUserSerializer(serializers.ModelSerializer):
    """Сериализатор регистрации пользователя."""

    password = serializers.CharField(
        min_length=PASSWORD_LENGTH,
        write_only=True
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = super().create(validated_data)
        user.set_password(password)
        user.save()
        return user


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор аватара."""
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance


class SubscriptionSerializer(UserSerializer):
    """Сериализатор подписок."""

    recipes = serializers.SerializerMethodField(method_name='get_recipes')
    recipes_count = serializers.SerializerMethodField(
        method_name='get_recipes_count'
    )

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, author):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = author.recipes.all()
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]
        base64_image_field = Base64ImageField()
        return [
            {
                "id": recipe.id,
                "name": recipe.name,
                "image": base64_image_field.to_representation(recipe.image),
                "cooking_time": recipe.cooking_time
            }
            for recipe in recipes
        ]

    def get_recipes_count(self, author):
        return author.recipes.count()


class CreateSubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор создания подписки."""

    class Meta:
        fields = ('user', 'author')
        model = Subscription

    def validate(self, data):
        user = data['user']
        author = data['author']

        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )

        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого автора.'
            )

        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return SubscriptionSerializer(
            instance.author,
            context={'request': request}
        ).data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeTagSerializer(serializers.ModelSerializer):
    """Сериализатор связи рецепт/тег."""

    id = serializers.IntegerField(source='tag.id')
    name = serializers.CharField(source='tag.name')
    slug = serializers.SlugField(source='tag.slug')

    class Meta:
        model = RecipeTag
        fields = (
            'id',
            'name',
            'slug'
        )


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор связи рецепт/ингредиент."""
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CreateRecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор создания связи рецепт/ингридиент."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def validate_amount(self, value):
        if not value:
            raise serializers.ValidationError(
                'Количество должно быть указано.'
            )
        return value


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта."""

    tags = RecipeTagSerializer(many=True, source='recipe_tags')
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True
    )
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (
            request and request.user.is_authenticated
            and request.user.favorite_recipes.filter(recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (
            request and request.user.is_authenticated
            and request.user.cart_recipes.filter(recipe=obj).exists()
        )


class CreateUpdateRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор создания/обновления рецепта."""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = CreateRecipeIngredientSerializer(
        many=True, source='recipe_ingredients'
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate(self, data):
        """Проверка уникальности тегов, ингредиентов и наличия изображения."""
        tags = data.get('tags', [])
        ingredients = data.get('recipe_ingredients', [])
        image = data.get('image')

        if not image:
            raise serializers.ValidationError('Нет изображения.')
        if not tags:
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один тег.'
            )
        if not ingredients:
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один ингредиент.'
            )
        ingredients_ids = [
            ingredient['ingredient'].id
            for ingredient in ingredients
        ]
        if len(set(ingredients_ids)) != len(ingredients_ids):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальными.'
            )

        if len(set(tags)) != len(tags):
            raise serializers.ValidationError(
                'Теги должны быть уникальными.'
            )

        return data

    def add_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ])

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise NotAuthenticated(
                'Пользователь не аутентифицирован.'
            )
        validated_data['author'] = request.user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.add_ingredients(recipe, ingredients)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('recipe_ingredients', None)

        if tags:
            instance.tags.set(tags)
        if ingredients:
            self.add_ingredients(instance, ingredients)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class AbstractRecipeActionSerializer(serializers.ModelSerializer):
    """Абстрактный сериализатор для добавления рецептов в избранное/корзину."""

    class Meta:
        abstract = True
        fields = ('user', 'recipe')

    def validate(self, data):
        model = self.Meta.model
        if model.objects.filter(**data).exists():
            raise serializers.ValidationError(
                f'Рецепт "{data["recipe"]}" уже добавлен.'
            )
        return data


class FavoriteRecipeSerializer(AbstractRecipeActionSerializer):
    """Сериализатор избранных рецептов."""
    class Meta:
        model = FavoriteRecipe
        fields = ('user', 'recipe')


class ShoppingCartRecipeSerializer(AbstractRecipeActionSerializer):
    """Сериализатор списка покупок."""
    class Meta:
        model = ShoppingCartRecipe
        fields = ('user', 'recipe')
