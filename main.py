# <-----import statements----->
import requests
from flask import Flask, redirect, render_template, request, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from passcode import API_KEY, SECRET_KEY

MOVIE_API_BASE_URL = 'https://api.themoviedb.org/3/search/movie?api_key='
MOVIE_API_IMAGE_URL = "https://image.tmdb.org/t/p/w500/"
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///good-movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.app_context().push()


# Creating a WTForm for editing a movie rating and review
class RateMovieForm(FlaskForm):
    new_rating = StringField('Your new rating out of 10',
                             validators=[DataRequired()])
    new_review = StringField('Your review for the movie',
                             validators=[DataRequired()])
    done_button = SubmitField('Done')


# Creating a WTForm for searching a movie in API data
class SearchMovie(FlaskForm):
    new_title = StringField('Movie Name', validators=[DataRequired()])
    search_button = SubmitField('Search')


# Creating a WTForm for adding a new movie to the list
class AddMovie(FlaskForm):
    add_rating = StringField('Your rating', validators=[DataRequired()])
    add_review = StringField('Your review', validators=[DataRequired()])
    add_button = SubmitField('Add')


# Creating a database
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, unique=True)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(600), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    review = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f"<Movie {self.title}>"


db.create_all()


# <-----All Flask Routes----->
@app.route("/")
def home():
    all_movies = Movie.query.all()

    movie_ratings = [movie.rating for movie in all_movies]
    movie_ratings.sort(reverse=True)
    sorted_movies = []
    for rating in movie_ratings:
        for movie in all_movies:
            if movie.rating == rating and movie not in sorted_movies:
                sorted_movies.append(movie)
                break
    print(sorted_movies)

    return render_template("index.html", movie_list=sorted_movies)


@app.route('/edit/<int:edit_id>', methods=['GET', 'POST'])
def edit(edit_id):
    form = RateMovieForm()
    if form.validate_on_submit():
        movie_to_update = Movie.query.get(edit_id)
        movie_to_update.rating = form.new_rating.data
        movie_to_update.review = form.new_review.data
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('edit.html', edit_form=form, movie_to_edit=Movie.query.get(edit_id))


@app.route('/delete/<int:delete_id>', methods=['GET', 'POST'])
def delete(delete_id):
    deleting_movie = Movie.query.get(delete_id)
    db.session.delete(deleting_movie)
    db.session.commit()

    return redirect(url_for('home'))


@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchMovie()

    if form.validate_on_submit():
        global data
        movie_title = form.new_title.data
        response = requests.get(
            f"{MOVIE_API_BASE_URL}{API_KEY}&query={movie_title}")
        data = response.json()
        return render_template('select.html', movies_data=data['results'])

    return render_template('search.html', search_form=form)


@app.route('/auto_add/<int:add_id>', methods=['GET', 'POST'])
def auto_add(add_id):
    global data
    form = AddMovie()

    if form.validate_on_submit():
        for movie in data['results']:
            if movie['id'] == add_id:
                adding_movie = Movie(
                    title=movie['original_title'],
                    year=movie['release_date'][:4],
                    description=movie['overview'],
                    rating=form.add_rating.data,
                    review=form.add_review.data,
                    img_url=f"{MOVIE_API_IMAGE_URL}{movie['poster_path']}",
                )
                db.session.add(adding_movie)
                db.session.commit()

        return redirect(url_for('home'))

    return render_template('add.html', add_form=form)


if __name__ == "__main__":
    app.run(debug=True)
