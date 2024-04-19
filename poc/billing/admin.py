from flask_admin.contrib.mongoengine import ModelView, filters

from poc.billing.models import Order, Product


class OrderByItemFilter(filters.BaseMongoEngineFilter):
    def apply(self, query, value):
        try:
            product = Product.objects.get(name=value)
            return query.filter(items=product)
        except Product.DoesNotExist:
            return query.none()

    def operation(self):
        return "is"


class OrderView(ModelView):
    can_delete = False
    can_view_details = True
    column_exclude_list = ["metadata", "tracking_url"]
    column_searchable_list = ["customer_email"]
    column_filters = [
        "status",
        "customer_email",
        "total_price",
        "tracking_url",
        OrderByItemFilter(column=Order.items, name="Items"),
    ]
    column_editable_list = ["status"]
    page_size = 20
    can_set_page_size = True
