import re
import uuid
from datetime import UTC, datetime

from mongoengine import (
    BooleanField,
    ComplexDateTimeField,
    DateTimeField,
    DecimalField,
    DictField,
    Document,
    EmailField,
    EmbeddedDocument,
    EmbeddedDocumentField,
    FloatField,
    IntField,
    ListField,
    NotUniqueError,
    ReferenceField,
    StringField,
    URLField,
    UUIDField,
    ValidationError,
    signals,
)


class Address(EmbeddedDocument):
    street = StringField(required=True)
    city = StringField(required=True, max_length=50)
    state = StringField(max_length=2)
    zip_code = StringField(required=True, regex=r"\d{5}", min_length=5, max_length=5)

    def __str__(self):
        return self.full_address

    @property
    def full_address(self):
        return f"{self.street}, {self.city}, {self.state} {self.zip_code}"


class Product(Document):
    @staticmethod
    def not_supported_name(name):
        if name == "not_supported_name":
            raise ValidationError("'not_supported_name' is not a valid name")

    name = StringField(required=True, unique=True, max_length=100, validation=not_supported_name)
    description = StringField(max_length=255)
    price = DecimalField(required=True, precision=2, min_value=0)
    quantity = IntField(required=True, min_value=0)
    categories = ListField(StringField(choices=["electronics", "clothing", "toys"]))
    available = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
    last_updated = ComplexDateTimeField(default=datetime.utcnow)

    meta = {"indexes": ["name", "$description", ("price", "-created_at")]}

    def __str__(self):
        return self.name

    def clean(self):
        if self.description == self.name:
            raise ValidationError("Name and Description should not be equal")

    def save(self, **kwargs):
        try:
            return super().save(**kwargs)
        except NotUniqueError as err:
            match = re.search(r"dup key: \{ (.*?):", err.args[0])
            if match:
                field_name = match.group(1)
                raise ValidationError(errors={field_name: ValidationError("Product with this name already exists")})

    @classmethod
    def update_last_updated(cls, sender, document, **kwargs):
        document.last_updated = datetime.now(UTC)


signals.pre_save_post_validation.connect(Product.update_last_updated, sender=Product)


class Order(Document):
    STATUS_CHOICE = (("p", "PENDING"), ("r", "PROCESSING"), ("s", "SHIPPED"), ("d", "DELIVERED"))

    order_id = UUIDField(binary=False, default=uuid.uuid4)
    customer_email = EmailField(required=True)
    shipping_address = EmbeddedDocumentField("Address")
    billing_address = EmbeddedDocumentField("Address")
    items = ListField(ReferenceField("Product"))
    status = StringField(choices=STATUS_CHOICE, required=True, default="p")
    total_price = FloatField(required=True)
    metadata = DictField()
    tracking_url = URLField()

    def __str__(self):
        return self.order_id.__str__()

    @property
    def full_shipping_address(self):
        if not self.shipping_address:
            return None
        return self.shipping_address.full_address

    @property
    def full_billing_address(self):
        if not self.billing_address:
            return self.full_shipping_address
        return self.billing_address.full_address
