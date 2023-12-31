from flask import Flask, make_response, jsonify, request, session
from flask_migrate import Migrate
from flask_cors import CORS
from models import User, Recipe, Favorite
from config import app, db
from middleware import authorization_required
import bcrypt


@app.get('/')
def hope():
    return {'msg': 'I really hope this works!'}


@app.get('/api')
@authorization_required
def api(current_user):
    return make_response({"user_id": current_user["id"], "msg" : "Access granted."})

##########################
### Routes for Recipes ###
##########################

@app.get('/api/recipes')
def get_recipes():
    all_recipes = Recipe.query.all()
    recipe_list = [recipe.to_dict() for recipe in all_recipes]
    return make_response(recipe_list, 200)

@app.route('/api/recipes', methods=["POST"])
@authorization_required(methods="POST")
def add_recipe(current_user): 
    POST_REQUEST = request.get_json()
    new_recipe = Recipe(
        name=POST_REQUEST['name'],
        image=POST_REQUEST['image'],
        ingredients=POST_REQUEST['ingredients'],
        directions=POST_REQUEST['directions'],
        vegetarian=POST_REQUEST['vegetarian'],
        who_submitted=POST_REQUEST['who_submitted']
    )
    db.session.add(new_recipe)
    db.session.commit()
    return make_response(jsonify(new_recipe.to_dict())), 201

@app.patch("/api/recipes/<int:recipe_id>")
@authorization_required
def edit_recipe(current_user, recipe_id):
    matching_recipe = Recipe.query.filter(Recipe.id == recipe_id).first()
    if not matching_recipe:
        return make_response({"error": f"Recipe ID '{recipe_id}' not found in database."})
    
    payload = request.get_json()

    for attribute in payload:
        setattr(matching_recipe, attribute, payload[attribute])

    db.session.add(matching_recipe)
    db.session.commit()
    return make_response(matching_recipe.to_dict(only=("id", "name")), 200)

@app.route("/api/recipes/<int:recipe_id>", methods=["DELETE"])
@authorization_required(methods="DELETE")
def remove_recipe(current_user, recipe_id):
    matching_recipe = Recipe.query.filter(Recipe.id == recipe_id).first()
    if not matching_recipe:
        return make_response({"error": f"Recipe ID '{recipe_id}' not found in database."})
    
    db.session.delete(matching_recipe)
    db.session.commit()
    return make_response(matching_recipe.to_dict(only=("name",)), 204)

########################
### Routes for Users ###
########################

@app.get("/api/users")
def get_all_users():
    all_users = User.query.all()
    user_list = [user.to_dict() for user in all_users]
    return make_response(user_list)


@app.get('/api/submitted-recipes')
@authorization_required
def get_users_submitted_recipes(current_user):
    all_recipes = Recipe.query.all()
    submitted_recipes = [recipe.to_dict(only=("directions", "id", "image", "ingredients", "likes", "name", "vegetarian")) for recipe in all_recipes if recipe.who_submitted == current_user["id"]]
    return make_response(jsonify(submitted_recipes)), 200

@app.get('/api/favorited-recipes')
@authorization_required
def get_users_favorite_recipes(current_user):
    favorite_recipes = [recipe["recipe"] for recipe in current_user["favorites"]]
    return make_response(favorite_recipes)






######################################
### Routes for User log in and out ###
######################################

@app.post('/api/signup')
def add_user():
    if request.method == "POST":
        # Retrieve POST request as JSONified payload.
        payload = request.get_json()

        # Extract username and password from payload.
        username = payload["username"]
        password = payload["password"]

        # Generate salt for strenghening password encryption.
        # NOTE: Salts add additional random bits to passwords prior to encryption.
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt=salt)

        # Create new user instance using username and hashed password.
        new_user = User(
            username=username,
            password=hashed_password.decode("utf-8")
        )

        if new_user is not None:
            # Add and commit newly created user to database.
            db.session.add(new_user)
            db.session.commit()

            # Save created user ID to server-persistent session storage.
            # NOTE: Sessions are to servers what cookies are to clients.
            # NOTE: Server sessions are NOT THE SAME as database sessions! (`session != db.session`)
            session["user_id"] = new_user.id

            return make_response(new_user.to_dict(only=("id", "username", "created_at")), 201)
        else:
            return make_response({"error": "Invalid username or password. Try again."}, 401)
    else:
        return make_response({"error": f"Invalid request type. (Expected POST; received {request.method}.)"}, 400)

# POST route to authenticate user in database using session-stored credentials.
@app.route("/api/login", methods=["POST"])
def user_login():
    if request.method == "POST":
        # Retrieve POST request as JSONified payload.
        payload = request.get_json()

        # Filter database by username to find matching user to potentially login.
        matching_user = User.query.filter(User.username.like(f"%{payload['username']}%")).first()

        # Check submitted password against hashed password in database for authentication.
        AUTHENTICATION_IS_SUCCESSFUL = bcrypt.checkpw(
            password=payload["password"].encode("utf-8"),
            hashed_password=matching_user.password.encode("utf-8")
        )

        if matching_user is not None and AUTHENTICATION_IS_SUCCESSFUL:
            # Save authenticated user ID to server-persistent session storage.
            # NOTE: Sessions are to servers what cookies are to clients.
            # NOTE: Server sessions are NOT THE SAME as database sessions! (`session != db.session`)
            session["user_id"] = matching_user.id

            return make_response(matching_user.to_dict(only=("id", "username", "created_at")), 200)
        else:
            return make_response({"error": "Invalid username or password. Try again."}, 401)
    else:
        return make_response({"error": f"Invalid request type. (Expected POST; received {request.method}.)"}, 400)

# DELETE route to remove session-stored credentials for logged user.
@app.route("/api/logout", methods=["DELETE"])
def user_logout():
    if request.method == "DELETE":
        # Clear user ID from server-persistent session storage.
        # NOTE: Sessions are to servers what cookies are to clients.
        # NOTE: Server sessions are NOT THE SAME as database sessions! (`session != db.session`)
        session["user_id"] = None

        return make_response({"msg": "User successfully logged out."}, 204)
    else:
        return make_response({"error": f"Invalid request type. (Expected DELETE; received {request.method}.)"}, 400)

######################
### Error Handling ###
######################

@app.errorhandler(404)
def page_not_found(e):
    return make_response({"Error": "Page not found."}, 404)


### App Execution ###

if __name__ == '__main__':
    app.run()