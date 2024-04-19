from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.mongoengine import ModelView
from flask_debugtoolbar import DebugToolbarExtension
from flask_mongoengine import MongoEngine
from flask_mongoengine.panels import mongo_command_logger
from pymongo import monitoring

from poc.apis import api_v1
from poc.billing.admin import OrderView
from poc.billing.models import Order, Product


def create_app(config=None):
    app = Flask(__name__)
    app.debug = True
    app.config.from_mapping(SECRET_KEY="dev")
    app.config["FLASK_ADMIN_SWATCH"] = "paper"
    app.config["DEBUG_TB_PANELS"] = (
        "flask_debugtoolbar.panels.versions.VersionDebugPanel",
        "flask_debugtoolbar.panels.timer.TimerDebugPanel",
        "flask_debugtoolbar.panels.headers.HeaderDebugPanel",
        "flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel",
        "flask_debugtoolbar.panels.config_vars.ConfigVarsDebugPanel",
        "flask_debugtoolbar.panels.template.TemplateDebugPanel",
        "flask_mongoengine.panels.MongoDebugPanel",
        "flask_debugtoolbar.panels.logger.LoggingPanel",
        "flask_debugtoolbar.panels.route_list.RouteListDebugPanel",
        "flask_debugtoolbar.panels.profiler.ProfilerDebugPanel",
    )

    admin = Admin(app, name="poc", template_mode="bootstrap3")
    admin.add_view(ModelView(Product))
    admin.add_view(OrderView(Order))

    app.register_blueprint(api_v1, url_prefix="/api/v1")

    DebugToolbarExtension(app)
    monitoring.register(mongo_command_logger)

    if not (config and config["TESTING"]):
        app.config["MONGODB_SETTINGS"] = {
            "db": "poc",
            "host": "mongodb",
            "port": 27017,
            "alias": "default",
        }
        db = MongoEngine()
        db.init_app(app)

    return app
