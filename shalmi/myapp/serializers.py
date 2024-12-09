from rest_framework import serializers
from .models import Product, Category, SubCategory, Order, OrderItem, ShippingAddress, ShipmentTracking, ShipmentUpdate, CustomUser, ProductLabel, Cart, CartItem
from decimal import Decimal
import decimal

# Fix CategorySerializer
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'is_active', 'created_at', 'updated_at']

# Fix CategoryCreateSerializer
class CategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'is_active']
        read_only_fields = ['id']

# Fix SubCategorySerializer
class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'category', 'is_active', 'created_at', 'updated_at']

# Fix SubCategoryCreateSerializer
class SubCategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'category', 'is_active']
        read_only_fields = ['id']

    def validate_category(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Cannot add subcategory to inactive category")
        return value
# Product Create Serializer
# Fix ProductCreateSerializer
class ProductCreateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=True)
    price = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        min_value=Decimal('0.00'),
        coerce_to_string=False
    )
    stock = serializers.IntegerField(min_value=0)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    subcategory = serializers.PrimaryKeyRelatedField(
        queryset=SubCategory.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Product
        fields = [
            'id', 
            'title', 
            'category', 
            'subcategory', 
            'stock', 
            'price', 
            'variations',
            'image',
            'status'
        ]
        read_only_fields = ['id', 'owner', 'slug']

    def validate(self, data):
        user = self.context['request'].user
        if user.role not in [CustomUser.MANAGER, CustomUser.ADMIN]:
            raise serializers.ValidationError(
                "Only managers and admins can create products."
            )

        # Convert price to Decimal if it's a string
        if 'price' in data and isinstance(data['price'], str):
            try:
                data['price'] = Decimal(data['price'])
            except (TypeError, ValueError, decimal.InvalidOperation):
                raise serializers.ValidationError({
                    'price': 'Invalid price format. Must be a valid decimal number.'
                })

        # Convert stock to integer if it's a string
        if 'stock' in data and isinstance(data['stock'], str):
            try:
                data['stock'] = int(data['stock'])
            except (TypeError, ValueError):
                raise serializers.ValidationError({
                    'stock': 'Invalid stock format. Must be a valid integer.'
                })

        # Validate category and subcategory relationship
        if 'category' in data and 'subcategory' in data and data['subcategory']:
            if data['subcategory'].category != data['category']:
                raise serializers.ValidationError({
                    'subcategory': 'Selected subcategory does not belong to the selected category'
                })

        return data

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

class ProductLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductLabel
        fields = [
            'is_new_arrival',
            'is_trending',
            'is_featured',
            'is_wholesale',
            'is_discounted',
            'is_top_selling'
        ]
        
# Product Serializer
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    subcategory = SubCategorySerializer()
    owner = serializers.StringRelatedField()
    labels = ProductLabelSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 
            'title', 
            'slug',
            'owner',
            'category', 
            'subcategory', 
            'stock', 
            'price', 
            'variations',
            'image',
            'status',
            'created_at',
            'updated_at',
            'labels'
        ]



class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price', 'variation']
        read_only_fields = ['price']

class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'shipping_address', 'items']
        read_only_fields = ['id', 'status', 'total_amount']

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must contain at least one item")
        return value

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        total_amount = 0

        # Create order
        order = Order.objects.create(
            user=self.context['request'].user,
            total_amount=0,  # Temporary value
            **validated_data
        )

        # Create order items
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            
            # Validate stock
            if product.stock < quantity:
                raise serializers.ValidationError(f"Not enough stock for {product.title}")
            
            # Create order item
            OrderItem.objects.create(
                order=order,
                price=product.price,
                **item_data
            )
            
            # Update product stock
            product.stock -= quantity
            product.save()
            
            # Calculate total
            total_amount += product.price * quantity

        # Update order total
        order.total_amount = total_amount
        order.save()

        return order

class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = [
            'id', 'full_name', 'phone_number', 
            'address_line1', 'address_line2', 
            'city', 'state', 'postal_code', 
            'country', 'is_default'
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            # Required fields
            'full_name': {'required': True},
            'phone_number': {'required': True},
            'address_line1': {'required': True},
            # Optional fields
            'address_line2': {'required': False},
            'city': {'required': False},
            'state': {'required': False},
            'postal_code': {'required': False},
            'country': {'required': False},
            'is_default': {'required': False}
        }

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class ShipmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentUpdate
        fields = ['id', 'status', 'location', 'description', 'timestamp']
        read_only_fields = ['id']

class ShipmentTrackingSerializer(serializers.ModelSerializer):
    updates = ShipmentUpdateSerializer(many=True, read_only=True)
    
    class Meta:
        model = ShipmentTracking
        fields = [
            'id', 'tracking_number', 'carrier', 'status',
            'estimated_delivery', 'actual_delivery', 'updates'
        ]
        read_only_fields = ['id']

# Update OrderSerializer to include shipping information
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField()
    shipment = ShipmentTrackingSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'total_amount', 'status',
            'shipping_address', 'items', 'shipment',
            'created_at', 'updated_at'
        ]

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']
        read_only_fields = ['id']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'role']
        read_only_fields = ['id']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'role']

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    subtotal = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_id', 'quantity', 
            'variation', 'subtotal', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        return value


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price', 'total_items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


