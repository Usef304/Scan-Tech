from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField
from wtforms.validators import DataRequired, Optional

class QRUploadForm(FlaskForm):
    file = FileField('QR Code Image', validators=[
        FileRequired(),
        FileAllowed(['png', 'jpg', 'jpeg', 'gif', 'bmp'], 'Images only!')
    ])

class QRDataForm(FlaskForm):
    qr_data = StringField('QR Code Data', validators=[DataRequired()])