from flask import Blueprint
from flask_restx import Api

from poc.apis.billing import api as billing_namespace

api_v1 = Blueprint("api", __name__)
api = Api(api_v1, title="POC APIs", version="1.0", description="POC APIs for testing purposes")

api.add_namespace(billing_namespace, path="/billing")
