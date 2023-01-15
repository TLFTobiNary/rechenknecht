import os
import base64
from flask import Flask, render_template
from random import randint

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='qGOVlYSDasdfasdasdasd  PoaW',
        DATABASE=os.path.join(app.instance_path, 'db.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass


    import db
    db.init_app(app)


    import auth
    app.register_blueprint(auth.bp)


    import rechenknecht 
    app.register_blueprint(rechenknecht.bp)
    app.add_url_rule("/", endpoint='index')


    @app.errorhandler(404)
    def errorhandler404(error):
        return render_template('404.html', title="404"), 404

    return app

app = create_app()
