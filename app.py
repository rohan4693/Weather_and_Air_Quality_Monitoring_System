from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import requests
import io
import matplotlib
matplotlib.use('Agg')  # Use the Agg backend for matplotlib
import matplotlib.pyplot as plt
import base64
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, SubmitField
from wtforms.validators import DataRequired
import pandas as pd
import plotly.express as px
from forms import CarbonFootprintForm
from dotenv import load_dotenv
import os


# Load environment variables from .env file
load_dotenv()



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
app.secret_key = '123'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Get the API key from environment variables
api_key = os.getenv('API_KEY')
api_news = os.getenv('API_NEWS')
aqi_key = os.getenv('AQI_KEY')



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    city = db.Column(db.String(100))

    def __init__(self, email, password, name, city):
        self.name = name
        self.city = city
        self.email = email
        self.password = password

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('posts', lazy=True))

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    post = db.relationship('Post', backref=db.backref('likes', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('likes', lazy=True))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    post = db.relationship('Post', backref=db.backref('comments', lazy=True))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('comments', lazy=True))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        city = request.form['city']

        new_user = User(name=name, email=email, password=password, city=city)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template("register.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('welcome'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/api/weather', methods=['GET'])
def api_weather():
    city = request.args.get('city', 'mumbai')
    weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    weather_response = requests.get(weather_url)
    weather_data = weather_response.json()

    aqi_url = f"https://api.waqi.info/feed/{city}/?token={aqi_key}"
    aqi_response = requests.get(aqi_url)
    aqi_data = aqi_response.json()

    if weather_response.status_code == 200 and aqi_response.status_code == 200:
        return jsonify({
            'weather': weather_data,
            'aqi': aqi_data
        })
    else:
        return jsonify({'error': 'Failed to fetch data'}), 500

@app.route('/welcome', methods=["GET", "POST"])
@login_required
def welcome():

    #Fetching news
    city = request.args.get('city', 'mumbai')
    url_news = f"https://newsdata.io/api/1/latest?apikey={api_news}&q={city}"
    response2 = requests.get(url_news)
    data2 = response2.json()
    articles = data2['results']
    #print(data2)


    city = request.args.get('city', 'mumbai')
    weather_response = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric")
    weather_data = weather_response.json()

    aqi_response = requests.get(f"https://api.waqi.info/feed/{city}/?token={aqi_key}")
    aqi_data = aqi_response.json()

    try:
        temperature = weather_data['main']['temp']
        feels_like = weather_data['main']['feels_like']
        humidity = weather_data['main']['humidity']
        wind_speed = weather_data['wind']['speed']
        visibility = weather_data['visibility']
        pressure = weather_data['main']['pressure']
        sunrise = weather_data['sys']['sunrise']
        sunset = weather_data['sys']['sunset']
        description = weather_data['weather'][0]['description']
    except KeyError as e:
        print(f"Error fetching weather data: {e}")
        temperature = "N/A"
        feels_like = "N/A"
        humidity = "N/A"
        wind_speed = "N/A"
        visibility = "N/A"
        pressure = "N/A"
        sunrise = "N/A"
        sunset = "N/A"
        description = "Data unavailable"

    try:
        aqi = aqi_data['data']['aqi']
        if aqi <= 50:
            aqi_status = "Good"
        elif aqi <= 100:
            aqi_status = "Moderate"
        elif aqi <= 150:
            aqi_status = "Unhealthy for Sensitive Groups"
        elif aqi <= 200:
            aqi_status = "Unhealthy"
        elif aqi <= 300:
            aqi_status = "Very Unhealthy"
        else:
            aqi_status = "Hazardous"
    except KeyError as e:
        print(f"Error fetching AQI data: {e}")
        aqi = "N/A"
        aqi_status = "N/A"

    plot_url1, plot_url2 = generate_plots(temperature, feels_like, humidity, pressure, wind_speed)

    return render_template('welcome.html', temperature=temperature, humidity=humidity, description=description, feels_like=feels_like, wind_speed=wind_speed, visibility=visibility, pressure=pressure, sunrise=sunrise, sunset=sunset, city=city, plot_url1=plot_url1, plot_url2=plot_url2, aqi=aqi, aqi_status=aqi_status, articles = articles)

@app.route('/community', methods=["GET", "POST"])
@login_required
def community():
    if request.method == "POST":
        title = request.form['title']
        content = request.form['content']
        new_post = Post(title=title, content=content, author_id=current_user.id)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('community'))

    posts = Post.query.all()
    return render_template('community.html', posts=posts)

@app.route('/post/<int:post_id>', methods=["GET", "POST"])
@login_required
def post(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == "POST":
        if 'like' in request.form:
            existing_like = Like.query.filter_by(post_id=post.id, user_id=current_user.id).first()
            if existing_like:
                db.session.delete(existing_like)
            else:
                new_like = Like(post_id=post.id, user_id=current_user.id)
                db.session.add(new_like)
            db.session.commit()
        else:
            content = request.form['content']
            new_comment = Comment(content=content, post_id=post.id, author_id=current_user.id)
            db.session.add(new_comment)
            db.session.commit()
        return redirect(url_for('post', post_id=post.id))

    return render_template('post.html', post=post)



def generate_plots(temperature, feels_like, humidity, pressure, wind_speed):
    labels = ['Temperature', 'Feels Like']
    values = [temperature, feels_like]

    plt.bar(labels, values)
    plt.ylabel('Temperature (Celsius)')
    plt.title('Temperature vs. Feels Like')

    img1 = io.BytesIO()
    plt.savefig(img1, format='png')
    img1.seek(0)
    plot_url1 = base64.b64encode(img1.getvalue()).decode('utf8')

    plt.clf()  # Clear the current figure

    labels = ['Humidity', 'Pressure', 'Wind Speed']
    values = [humidity, pressure, wind_speed]

    plt.plot(labels, values, marker='o')
    plt.xlabel('Parameter')
    plt.ylabel('Value')
    plt.title('Weather Parameters')

    img2 = io.BytesIO()
    plt.savefig(img2, format='png')
    img2.seek(0)
    plot_url2 = base64.b64encode(img2.getvalue()).decode('utf8')

    return plot_url1, plot_url2

@app.route('/carbon_calculator', methods=['GET', 'POST'])
@login_required
def carbon_calculator():
    form = CarbonFootprintForm()
    if form.validate_on_submit():
        # Calculate carbon footprint
        transport_emission = form.distance.data * 0.21  # Example factor
        electricity_emission = (form.curr_usage.data - form.prev_usage.data) * 0.5  # Example factor
        waste_emission = (form.dry_waste.data * 0.1) + (form.wet_waste.data * 0.05)  # Example factors
        
        total_emission = transport_emission + electricity_emission + waste_emission
        
        # Save data to DataFrame
        data = {
            'Name': [form.name.data],
            'City': [form.city.data],
            'Transport Emission': [transport_emission],
            'Electricity Emission': [electricity_emission],
            'Waste Emission': [waste_emission],
            'Total Emission': [total_emission]
        }
        df = pd.DataFrame(data)
        df.to_csv('carbon_footprint.csv', mode='a', header=not os.path.isfile('carbon_footprint.csv'), index=False)
        
        return render_template('results.html', total_emission=total_emission)
    
    return render_template('carbon_calculator.html', form=form)

@app.route('/visualization')
@login_required
def visualization():
    df = pd.read_csv('carbon_footprint.csv', names=['Date', 'Name', 'City', 'Transport Emission', 'Electricity Emission', 'Waste Emission', 'Total Emission'])
    fig_bar = px.bar(df, x='Name', y='Total Emission', title='Carbon Emission by User')
    fig_line = px.line(df, x='Date', y='Total Emission', title='Carbon Emission History')
    graph_bar = fig_bar.to_html(full_html=False)
    graph_line = fig_line.to_html(full_html=False)
    return render_template('visualization.html', graph_bar=graph_bar, graph_line=graph_line)

@app.route('/leaderboard')
@login_required
def leaderboard():
    df = pd.read_csv('carbon_footprint.csv', names=['Name', 'City', 'Transport Emission', 'Electricity Emission', 'Waste Emission', 'Total Emission'])
    df = df.sort_values(by='Total Emission')
    return render_template('leaderboard.html', tables=[df.to_html(classes='data')], titles=df.columns.values)

if __name__ == '__main__':
    app.run(debug=True)