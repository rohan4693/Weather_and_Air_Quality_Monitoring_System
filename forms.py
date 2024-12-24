from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, SubmitField
from wtforms.validators import DataRequired

class CarbonFootprintForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    
    # Transportation
    distance = FloatField('Distance (km)', validators=[DataRequired()])
    transport_mode = SelectField('Mode of Transport', choices=[('car', 'Car'), ('bus', 'Bus'), ('train', 'Train'), ('bike', 'Bike')], validators=[DataRequired()])
    
    # Electricity
    prev_usage = FloatField('Previous Month Usage (kWh)', validators=[DataRequired()])
    curr_usage = FloatField('Current Usage (kWh)', validators=[DataRequired()])
    
    # Waste
    dry_waste = FloatField('Dry Waste (kg)', validators=[DataRequired()])
    wet_waste = FloatField('Wet Waste (kg)', validators=[DataRequired()])
    
    submit = SubmitField('Calculate')