import flask_wtf
import wtforms


class DeviceUnderTestForm(flask_wtf.FlaskForm):
    dev_eui = wtforms.StringField("DevEUI", default="0004a30b001adbe5", validators=[wtforms.validators.DataRequired()])
    app_key = wtforms.StringField("AppKey", default="2b7e151628aed2a6abf7158809cf4f3c", validators=[wtforms.validators.DataRequired()])
    dev_addr = wtforms.StringField("DevAddr", default="26011cf1", validators=[wtforms.validators.DataRequired()])
    submit = wtforms.SubmitField('Set ABP config')
