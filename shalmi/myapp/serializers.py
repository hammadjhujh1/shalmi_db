from rest_framework import serializers
from .models import Product, Category, SubCategory, Order, OrderItem, ShippingAddress, ShipmentTracking, ShipmentUpdate, CustomUser, ProductLabel

# Add these basic serializers first
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'slug', 'is_active']

class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'description', 'slug', 'category', 'is_active']

# Product Create Serializer
class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 
            'title', 
            'description',
            'category', 
            'subcategory', 
            'stock', 
            'price', 
            'variations',
            'image',
            'status'
        ]
        read_only_fields = ['id', 'owner', 'slug']

    def validate_subcategory(self, value):
        """
        Validate that subcategory belongs to the selected category
        """
        category_id = self.initial_data.get('category')
        if value and category_id and value.category_id != int(category_id):
            raise serializers.ValidationError(
                "Selected subcategory does not belong to the selected category"
            )
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        if user.role not in [user.SELLER, user.BOTH, user.MANAGER, user.ADMIN]:
            raise serializers.ValidationError("You don't have permission to create products")
        validated_data['owner'] = user
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
            'description',
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

# Add these serializers for category creation/update

class CategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'is_active']
        read_only_fields = ['id', 'slug']

class SubCategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'description', 'category', 'is_active']
        read_only_fields = ['id', 'slug']

    def validate_category(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Cannot add subcategory to inactive category")
        return value

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
            'id', 'full_name', 'phone_number', 'street_address', 
            'apartment', 'city', 'state', 'postal_code', 'country',
            'is_default'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
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


