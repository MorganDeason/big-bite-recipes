from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.ext.associationproxy import association_proxy
from config import db 

# db = SQLAlchemy()

class Recipe(db.Model, SerializerMixin):
    __tablename__ ='recipes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    image = db.Column(db.String)
    ingredients = db.Column(db.String, nullable=False)
    directions = db.Column(db.String, nullable=False)
    vegetarian = db.Column(db.Boolean, nullable=False)
    who_submitted = db.Column(db.Integer)
    likes = db.Column(db.Integer, default=0)

    # Create a relationship between recipe and favorite
    favorites = db.relationship("Favorite", back_populates="recipe")

    # Creates an association proxy from the recipe-favorite relationship
    users = association_proxy("favorites", "user")

    # Creates serialization rules to avoid cascading
    serialize_rules = ("-favorites.recipe",)

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def is_administrator(self):
        return self.is_admin
    # Create a relationship between user and favorite
    favorites = db.relationship("Favorite", back_populates="user")

    # Create an association proxy from the user-favorite relationship
    recipes = association_proxy("favorites","recipe")

    # Create serialization rules to avoid cascading
    serialize_rules = ("-favorites.user",)


class Favorite(db.Model, SerializerMixin):
    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Relationship between favorite row and recipe row
    recipe = db.relationship("Recipe", back_populates="favorites")

    # Relationship between favorite row and user row
    user = db.relationship("User", back_populates="favorites")

    # Create serialization rules to avoid cascading
    serialize_rules = ("-recipe.favorites", "-user.favorites")
