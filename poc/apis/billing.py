from flask import request
from flask_restx import Namespace, Resource, abort, fields
from marshmallow import EXCLUDE, Schema, ValidationError
from marshmallow import fields as m_fields
from marshmallow import post_dump
from marshmallow_mongoengine import ModelSchema
from mongoengine import SaveConditionError
from mongoengine import ValidationError as MEValidationError

from poc.billing.models import Order, Product

api = Namespace("billing", description="Billing operations")

AddressOutModel = api.model(
    "AddressOutModel",
    {
        "street": fields.String,
        "city": fields.String,
        "state": fields.String,
        "zip_code": fields.String,
    },
)

OrderOutModel = api.model(
    "OrderOutModel",
    {
        "id": fields.String,
        "order_id": fields.String(description="Order ID"),
        "items": fields.List(fields.String),
        "customer_email": fields.String(description="Customer Email"),
        "status": fields.String(attribute=lambda obj: obj.get_status_display()),
        "total_price": fields.Float,
        "tracking_url": fields.String,
        "shipping_address": fields.String,
        "billing_address": fields.Nested(AddressOutModel),
        "extra_field": fields.String(default="Anup Dhabarde"),
    },
)


@api.route("/order")
class OrderCollectionResource(Resource):
    @api.marshal_list_with(OrderOutModel, skip_none=True)
    def get(self):
        return list(Order.objects.all())


class ProductSchema(ModelSchema):
    class Meta:
        model = Product
        unknown = EXCLUDE
        dump_only = ("created_at", "id")

    @post_dump
    def modify_price(self, data, **kwargs):
        data["price"] = float(data["price"])
        return data


class ProductFilterSchema(Schema):
    name = m_fields.Str()
    available = m_fields.Bool()

    class Meta:
        unknown = EXCLUDE


@api.route("/products")
class ProductCollectionResource(Resource):
    def __get_queryset(self):
        return Product.objects.filter(**ProductFilterSchema().load(request.args))

    def get(self):
        products = self.__get_queryset()
        schema = ProductSchema(many=True)
        return schema.dump(products)

    def post(self):
        schema = ProductSchema()
        try:
            new_product = schema.load(request.json)
            new_product.save()
        except ValidationError as err:
            return err.messages, 400
        except MEValidationError as err:
            errors = {field: [message] for field, message in err.to_dict().items()}
            return errors, 400

        return schema.dump(new_product), 201

    def delete(self):
        return "Not Implemented", 204


@api.route("/products/<string:product_id>")
class ProductResource(Resource):
    def __get_object(self, product_id):
        try:
            return Product.objects.get(id=product_id)
        except (Product.DoesNotExist, MEValidationError):
            abort(404)

    def get(self, product_id):
        product = self.__get_object(product_id)
        return ProductSchema().dump(product)

    def patch(self, product_id):
        product = self.__get_object(product_id)

        schema = ProductSchema()
        try:
            updated_product = schema.update(product, request.json)
            updated_product.save(save_condition={"id": product.id})
        except ValidationError as err:
            return err.messages, 400
        except MEValidationError as err:
            errors = {field: [message] for field, message in err.to_dict().items()}
            return errors, 400
        except SaveConditionError:
            abort(404)

        return schema.dump(updated_product), 200

    def put(self, product_id):
        return self.patch(product_id)

    def delete(self, product_id):
        product = self.__get_object(product_id)
        product.delete()

        return "", 204
