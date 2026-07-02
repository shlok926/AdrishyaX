from flask import Blueprint

def register_blueprints(app):
    from app.api.views import views_bp
    # we will add encode, decode, batch, etc. here as we refactor
    app.register_blueprint(views_bp)
