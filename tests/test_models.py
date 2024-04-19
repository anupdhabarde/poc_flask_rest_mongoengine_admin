import mongomock
import pytest
from mongoengine import NotUniqueError, ValidationError

from poc.billing.models import Address, Order, Product


class TestProduct:

    def test_name_custom_validation(self):
        """
        GIVEN:  A product with a name that is not supported (custom validation)
        WHEN:   The product is validated
        THEN:   A ValidationError is raised with a message indicating the name is not valid
        """
        product = Product(name="not_supported_name", price=1, quantity=1, categories=["electronics"])
        with pytest.raises(ValidationError) as excinfo:
            product.validate()
        assert excinfo.value.to_dict() == {"name": "not_supported_name is not a valid name"}

    def test_name_unique_constraint(self):
        """
        GIVEN:  A product with a name that already exists in the database
        WHEN:   The product is saved
        THEN:   A NotUniqueError is raised
        """
        Product(name="test", price=1, quantity=1, categories=["electronics"]).save()
        product = Product(name="test", price=1, quantity=1, categories=["electronics"])
        with pytest.raises(NotUniqueError):
            product.save()

    def test_description_max_length_validation(self):
        """
        GIVEN:  A product with a description that exceeds the maximum length
        WHEN:   The product is validated
        THEN:   A ValidationError is raised with a message indicating the description is too long
        """
        product = Product(name="test", description="a" * 256, price=1, quantity=1, categories=["electronics"])
        with pytest.raises(ValidationError) as excinfo:
            product.validate()
        assert excinfo.value.to_dict() == {"description": "String value is too long"}

    def test_quantity_min_value_validation(self):
        """
        GIVEN:  A product with a quantity less than the minimum allowed value
        WHEN:   The product is validated
        THEN:   A ValidationError is raised with a message indicating the quantity is too small
        """
        with pytest.raises(ValidationError) as excinfo:
            Product(
                name="Test Product",
                description="Test Description",
                price=10.00,
                quantity=-1,
                categories=["electronics"],
            ).validate()
        assert excinfo.value.to_dict() == {"quantity": "Integer value is too small"}

    def test_category_invalid_choice(self):
        """
        GIVEN:  A product with a category that is not a valid choice
        WHEN:   The product is validated
        THEN:   A ValidationError is raised with a message indicating the category is not valid
        """
        with pytest.raises(ValidationError) as excinfo:
            Product(name="Test Product", price=10.00, quantity=1, categories=["invalid"]).validate()
        assert excinfo.value.to_dict() == {
            "categories": {0: "Value must be one of ['electronics', 'clothing', 'toys']"}
        }

    def test_clean_method(self):
        """
        GIVEN:  A product with a name and description that are equal
        WHEN:   The product is validated
        THEN:   A ValidationError is raised with a message indicating the name and description should not be equal
        """
        with pytest.raises(ValidationError) as excinfo:
            Product(
                name="Test Product", description="Test Product", price=10.00, quantity=1, categories=["electronics"]
            ).validate()
        assert excinfo.value.to_dict() == {"__all__": "Name and Description should not be equal"}

    def test_last_updated_pre_save_signal(self):
        """
        GIVEN:  A product that has been saved
        WHEN:   The product is updated and saved again
        THEN:   The last_updated field of the product is updated to a later time
        """
        product = Product(name="Test Product", price=10.00, quantity=1, categories=["electronics"])
        product.save()
        assert product.last_updated is not None
        old_last_updated = product.last_updated
        product.price = 20.00
        product.save()
        assert product.last_updated != old_last_updated
        assert product.last_updated > old_last_updated

    def test_successful_creation(self):
        """
        GIVEN:  A valid product
        WHEN:   The product is saved
        THEN:   The product is successfully saved and can be found in the database
        """
        product = Product(name="Test Product", price=10.00, quantity=1, categories=["electronics"])
        product.save()
        assert product.id is not None
        assert product in Product.objects.all()


class TestOrder:

    def test_customer_email_validate_email(self):
        """
        GIVEN:  An order with an invalid customer email address
        WHEN:   The order is validated
        THEN:   A ValidationError is raised with a message indicating the email address is not valid
        """
        with pytest.raises(ValidationError) as excinfo:
            Order(customer_email="invalid_email", total_price=23).validate()
        assert excinfo.value.to_dict() == {"customer_email": "Invalid email address: invalid_email"}

    def test_total_price_float_validation(self):
        with pytest.raises(ValidationError) as excifno:
            Order(customer_email="a@b.com", total_price="not a number").validate()
        assert excifno.value.to_dict() == {"total_price": "FloatField only accepts float and integer values"}

    def test_shipping_address(self):
        # Create an Address instance
        address = Address(street="123 Main St", city="Anytown", state="CA", zip_code="12345")

        # Create an Order instance with the Address instance as the shipping_address
        order = Order(customer_email="test@example.com", total_price=123, shipping_address=address).save()

        # Assert that the shipping_address is an embedded document and not a separate document
        assert isinstance(order.shipping_address, Address)
        assert order.shipping_address.street == "123 Main St"
        assert order.shipping_address.city == "Anytown"
        assert order.shipping_address.state == "CA"
        assert order.shipping_address.zip_code == "12345"

        # Assert that there is no Address collection in the database
        assert "address" not in mongomock.MongoClient().db.list_collection_names()
