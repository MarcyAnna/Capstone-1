from flask import Flask, redirect, render_template, request, session, g, flash
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, CreateCategory
from models import db, connect_db, User, Recipe, Category, Rating

from secretkey import API_SECRET_KEY

import requests 

API_BASE_URL = "https://api.spoonacular.com/recipes/complexSearch"

apiKey = API_SECRET_KEY

app = Flask(__name__)

app.app_context().push()

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///recipes'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = "1234567890"
toolbar = DebugToolbarExtension(app)

connect_db(app)

@app.route('/')
def homepage():

    if 'curr_user' in session:
        user = User.query.get(session['curr_user'])

    else:
        user = None 

    

    return render_template("homepage.html", user=user)


@app.route('/result')
def show_recipe():

    if 'curr_user' in session:
        user = User.query.get(session['curr_user'])

    else:
        user = None 


    recipe = request.args['recipe']
    diet = request.args['diet']
    res = requests.get(f"{API_BASE_URL}", params={'apiKey': apiKey, 'query': recipe, 'diet': diet, 'instructionsRequired': True, 'number': 1})
    data = res.json()
    session['curr_recipe'] = data
    recipe_title = data["results"][0]["title"]
    recipe_id = data["results"][0]["id"]
    recipe_image = data["results"][0]["image"]
    

    return render_template('homepage.html', recipe_title = recipe_title, recipe_id = recipe_id, recipe_image = recipe_image, user = user)

@app.route('/saverecipe')
def save_recipe():

    if 'curr_user' in session:
        user = User.query.get(session['curr_user'])
        data = session['curr_recipe']
        recipe = Recipe(
            id = data["results"][0]["id"],
            name = data["results"][0]["title"]
        )
        user.recipes.append(recipe)
        db.session.commit()
        session.pop('curr_recipe', None)
        return redirect('/')

    else:
        flash('Please Login To Save Recipe!')
        return render_template('homepage.html')

# User routes

@app.route('/signup', methods=["GET", "POST"])
def signup():
    

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/new.html', form=form)
        
        session['curr_user'] = user.id


        return redirect("/")

    else:
        return render_template('users/new.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
        if user:
            session['curr_user'] = user.id
            return redirect('/')

    return render_template('users/login.html', form=form)

@app.route('/logout')
def logout():

    if 'curr_user' in session:
        del session['curr_user']

    return redirect('/')

@app.route('/user')
def user_page():

    user = User.query.get(session['curr_user'])

    return render_template('users/myrecipes.html', user=user)

@app.route('/addcategory', methods=['GET', 'POST'])
def new_category():

    form = CreateCategory()
    user = User.query.get(session['curr_user'])

    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data,
            )
        user.categories.append(category)
        db.session.commit()
        return redirect('/user')

    return render_template('category.html', form=form, user=user)

    


