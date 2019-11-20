from flask import Flask

app = Flask(__name__)
app.config['DEBUG'] = True

from server.routes.routes import routes
app.register_blueprint(routes)
