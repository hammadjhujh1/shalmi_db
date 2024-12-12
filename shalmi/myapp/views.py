from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CustomUser, Product, Category, SubCategory, ShippingAddress, ShipmentTracking, Order, OrderItem, ProductLabel, Cart, CartItem
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from .serializers import (
    CategorySerializer, CategoryCreateSerializer,
    SubCategorySerializer, SubCategoryCreateSerializer,
    ProductSerializer, ProductCreateSerializer,
    ShippingAddressSerializer, ShipmentTrackingSerializer,
    OrderSerializer, UserSerializer, UserCreateSerializer, UserUpdateSerializer, ProductLabelSerializer,
    CartSerializer, CartItemSerializer,
    ShipmentUpdateSerializer
)
from .permissions import IsAdminManagerOrReadOnly, IsAdminUser
import json
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from django.core.files.storage import default_storage
import os
from .utils import validate_file_type, validate_file_size
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from rest_framework import generics
from rest_framework.exceptions import NotFound
from django.core.exceptions import ObjectDoesNotExist

# @ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({
        'csrfToken': request.META.get('CSRF_COOKIE'),
        'status': 'success'
    })

# @ensure_csrf_cookie
def signup(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')

            if not email or not password:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Email and password are required'
                }, status=400)

            # Check if user already exists
            if CustomUser.objects.filter(email=email).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Email already registered'
                }, status=400)

            # Create new user
            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                username=email  # Using email as username
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Account created successfully'
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid request data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)

# @csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return JsonResponse({
                    'status': 'error',
                    'message': "Username and password are required"
                }, status=400)

            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                auth_login(request, user)
                
                # Generate token
                refresh = RefreshToken.for_user(user)
                tokens = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
                
                return JsonResponse({
                    'status': 'success',
                    'message': f"Welcome {user.username}",
                    'tokens': tokens,
                    'user': {
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                    }
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': "Invalid credentials. Please try again."
                }, status=401)

        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': "Invalid JSON data"
            }, status=400)

    return JsonResponse({
        'status': 'error',
        'message': "Method not allowed"
    }, status=405)

# @csrf_exempt
@require_http_methods(["POST"])
def logout_user(request):
    try:
        logout(request)
        return JsonResponse({
            'status': 'success',
            'message': 'Successfully logged out'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

# Product ViewSet
class ProductViewSet(viewsets.ModelViewSet):
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateSerializer
        return ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(is_deleted=False)
        
        # Get filter parameters from request
        category_id = self.request.query_params.get('category_id')
        subcategory_id = self.request.query_params.get('subcategory_id')
        status = self.request.query_params.get('status')
        search = self.request.query_params.get('search')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        # Apply filters
        if category_id:
            queryset = queryset.filter(category_id=category_id)
            
        if subcategory_id:
            queryset = queryset.filter(subcategory_id=subcategory_id)
            
        if status:
            queryset = queryset.filter(status=status)
            
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
            
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
            
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(slug__icontains=search) |
                Q(category__name__icontains=search) |
                Q(subcategory__name__icontains=search)
            ).distinct()
        
        # Default ordering
        return queryset.order_by('-created_at')

    def create(self, request, *args, **kwargs):
        print("Content-Type:", request.content_type)
        print("Request data:", request.data)
        
        try:
            # Create product with initial data
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                print("Validation errors:", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Save the product
            try:
                product = serializer.save(owner=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                print("Save error:", str(e))
                return Response(
                    {'error': f'Error saving product: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            print("Error:", str(e))
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Handle image replacement
        image = request.FILES.get('image')
        if image:
            # Delete old image if it exists
            if instance.image:
                try:
                    default_storage.delete(instance.image.path)
                except Exception:
                    pass  # Handle case where file is missing
            
            # Save new image
            filename = default_storage.get_available_name(image.name)
            file_path = default_storage.save(f'products/{filename}', image)
            request.data['image'] = file_path

        # Get or create label for the product
        label = instance.labels.first()
        if not label:
            label = ProductLabel.objects.create(product=instance)

        # Update label fields from request data
        for field in ['is_new_arrival', 'is_trending', 'is_featured', 
                     'is_wholesale', 'is_discounted', 'is_top_selling']:
            if field in request.data:
                setattr(label, field, request.data[field])
        
        label.save()

        # Update the product using the serializer
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(ProductSerializer(instance).data)

    @action(detail=True, methods=['patch'])
    def update_labels(self, request, pk=None):
        """Update product labels"""
        product = self.get_object()
        label = product.labels.first()  # Assuming one label per product
        
        if not label:
            return Response(
                {"error": "No label found for this product"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Update label fields from request data
        for field in ['is_new_arrival', 'is_trending', 'is_featured', 
                     'is_wholesale', 'is_discounted', 'is_top_selling']:
            if field in request.data:
                setattr(label, field, request.data[field])
        
        label.save()
        return Response(ProductSerializer(product).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Delete associated image file
        if instance.image:
            try:
                default_storage.delete(instance.image.path)
            except Exception:
                pass  # Handle case where file is missing
        
        return super().destroy(request, *args, **kwargs)

# Category ViewSet
class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminManagerOrReadOnly]
    
    def get_queryset(self):
        # For list view, show only active categories to non-admin users
        if self.action == 'list' and not (
            self.request.user.is_authenticated and 
            self.request.user.role in [self.request.user.ADMIN, self.request.user.MANAGER]
        ):
            return Category.objects.filter(is_active=True)
        return Category.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CategoryCreateSerializer
        return CategorySerializer

# SubCategory ViewSet
class SubCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminManagerOrReadOnly]
    
    def get_queryset(self):
        queryset = SubCategory.objects.all()
        
        # Filter by category if provided
        category_id = self.request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # For list view, show only active subcategories to non-admin users
        if self.action == 'list' and not (
            self.request.user.is_authenticated and 
            self.request.user.role in [self.request.user.ADMIN, self.request.user.MANAGER]
        ):
            queryset = queryset.filter(is_active=True, category__is_active=True)
            
        return queryset

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SubCategoryCreateSerializer
        return SubCategorySerializer

# New NewArrivalsViewSet
class NewArrivalsViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that returns new arrival products"""
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # Base queryset with default ordering by created_at
        queryset = Product.objects.filter(
            labels__is_new_arrival=True,
            is_deleted=False,
            status='published'
        ).distinct().order_by('-created_at')

        # Get sort parameter from request
        sort_by = self.request.query_params.get('sort')
        
        # Only apply different sorting if explicitly requested
        if sort_by == 'most_sold':
            queryset = queryset.annotate(
                total_sold=Count('orderitem')
            ).order_by('-total_sold')
        elif sort_by == 'price':
            queryset = queryset.order_by('price')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        
        return queryset

class TrendingProductsViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that returns trending products"""
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Product.objects.filter(
            labels__is_trending=True,
            is_deleted=False,
            status='published'
        ).distinct().order_by('-created_at')

class WholesaleProductsViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that returns wholesale products"""
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Product.objects.filter(
            labels__is_wholesale=True,
            is_deleted=False,
            status='published'
        ).distinct().order_by('-created_at')

class FeaturedProductsViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that returns featured products"""
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Product.objects.filter(
            labels__is_featured=True,
            is_deleted=False,
            status='published'
        ).distinct().order_by('-created_at')

class DiscountedProductsViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that returns discounted products"""
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Product.objects.filter(
            labels__is_discounted=True,
            is_deleted=False,
            status='published'
        ).distinct().order_by('-created_at')

class TopSellingProductsViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that returns top selling products"""
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Product.objects.filter(
            labels__is_top_selling=True,
            is_deleted=False,
            status='published'
        ).distinct().order_by('-created_at')

def home_page(request):
    return render(request, 'home_page.html')

def admin_dashboard(request):
    return render(request, 'admin_index.html')

def buyer_dashboard(request):
    return render(request, 'Buyer_dashboard.html')

def analytics_dashboard(request):
    return render(request, 'analytics_dashboard.html')

def seller_analytics(request):
    return render(request, '22_seller_analytics.html')

def api_integration(request):
    return render(request, '23_api_integration.html')

def notifications(request):
    return render(request, '24_notifications.html')

def contact_us(request):
    return render(request, '25_contact_us.html')

def faqs(request):
    return render(request, '26_faqs.html')

def about_us(request):
    return render(request, '27_about_us.html')

def privacy_policy(request):
    return render(request, '28_privacy_policy.html')

def terms_conditions(request):
    return render(request, '29_terms_and_conditions.html')

def refund_policy(request):
    return render(request, '30_refund_policy.html')

def shipping_policy(request):
    return render(request, '31_shipping_policy.html')

def help_centre(request):
    return render(request, '32_help_centre.html')

def live_chat_support(request):
    return render(request, '33_live_chat_support.html')

def discussion_forum(request):
    return render(request, '34_discussion_forum.html')

def partner_institutions(request):
    return render(request, '35_partner_institutions.html')

def landing_promotions(request):
    return render(request, '36_landing_page_promotions.html')

def loyalty_program(request):
    return render(request, '37_loyality_program.html')

def premium_subscription(request):
    return render(request, '38_premium_subscription.html')

def user_reviews(request):
    return render(request, '39_user_reviews.html')

def affiliate_program(request):
    return render(request, '40_affiliate_program.html')

def blog(request):
    return render(request, '41_blog.html')

def careers(request):
    return render(request, '42_careers.html')

def payment_gateway(request):
    return render(request, 'payment_gateway.html')

def checkout_page(request):
    return render(request, 'checkout_page.html')

def inventory_management(request):
    return render(request, 'inventory_management.html')

def order_configuration(request):
    return render(request, 'order_configuration.html')

def order_tracking(request):
    return render(request, 'order_tracking.html')

def product_management(request):
    return render(request, 'product_management.html')

def products_details(request):
    return render(request, 'products_detailsPage.html')

def profile_page(request):
    return render(request, 'profile_pageseller_buyer).html')

def request_product_sample(request):
    return render(request, 'requestProd_sample.html')

def search_result_page(request):
    return render(request, 'search_resultpage.html')

def seller_dashboard(request):
    return render(request, 'seller_dashboard.html')

def setting_page(request):
    return render(request, 'setting_page.html')


def trending_top_selling_products(request):
    return render(request, 'trending_topsellingProds.html')

def upload_product(request):
    return render(request, 'upload_product.html')

def users_management(request):
    return render(request, 'users_management.html')




def all_pages(request):
    return render(request, 'all_pages.html')

class ShippingAddressViewSet(viewsets.ModelViewSet):
    serializer_class = ShippingAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ShippingAddress.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        address = self.get_object()
        address.is_default = True
        address.save()
        return Response({'status': 'default address set'})

class ShipmentTrackingViewSet(viewsets.ModelViewSet):
    serializer_class = ShipmentTrackingSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'tracking_number'

    def get_queryset(self):
        user = self.request.user
        if user.role in [user.MANAGER, user.ADMIN]:
            return ShipmentTracking.objects.all()
        return ShipmentTracking.objects.filter(order__user=user)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            
            # Check permissions
            if not request.user.role in [request.user.MANAGER, request.user.ADMIN]:
                if instance.order.user != request.user:
                    return Response(
                        {'error': 'You do not have permission to view this tracking information'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            # Return tracking information
            return Response({
                'tracking_number': instance.tracking_number,
                'order_id': instance.order.id,
                'status': instance.status,
                'carrier': instance.carrier,
                'estimated_delivery': instance.estimated_delivery,
                'actual_delivery': instance.actual_delivery,
                'last_updated': instance.updated_at,
                'order_details': {
                    'total_amount': instance.order.total_amount,
                    'order_date': instance.order.created_at,
                    'shipping_address': instance.order.shipping_address,
                }
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def track_order(self, request):
        """Alternative method to track order using query parameters"""
        tracking_number = request.query_params.get('tracking_number')
        order_id = request.query_params.get('order_id')

        try:
            if tracking_number:
                instance = ShipmentTracking.objects.get(tracking_number=tracking_number)
            elif order_id:
                instance = ShipmentTracking.objects.get(order_id=order_id)
            else:
                return Response(
                    {'error': 'Please provide either tracking_number or order_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check permissions
            if not request.user.role in [request.user.MANAGER, request.user.ADMIN]:
                if instance.order.user != request.user:
                    return Response(
                        {'error': 'You do not have permission to view this tracking information'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            # Return tracking information
            return Response({
                'tracking_number': instance.tracking_number,
                'order_id': instance.order.id,
                'status': instance.status,
                'carrier': instance.carrier,
                'estimated_delivery': instance.estimated_delivery,
                'actual_delivery': instance.actual_delivery,
                'last_updated': instance.updated_at,
                'order_details': {
                    'total_amount': instance.order.total_amount,
                    'order_date': instance.order.created_at,
                    'shipping_address': instance.order.shipping_address,
                }
            })

        except ShipmentTracking.DoesNotExist:
            raise NotFound(detail="Tracking information not found")

    @action(detail=True, methods=['post'])
    def add_update(self, request, pk=None):
        shipment = self.get_object()
        serializer = ShipmentUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(shipment=shipment)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def mark_delivered(self, request, pk=None):
        shipment = self.get_object()
        shipment.status = 'delivered'
        shipment.actual_delivery = timezone.now()
        shipment.save()
        
        # Update order status
        shipment.order.status = 'delivered'
        shipment.order.save()
        
        return Response({'status': 'marked as delivered'})

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role in [user.MANAGER, user.ADMIN]:
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['POST'], url_path='place-order')
    def place_order(self, request):
        """Place a new order using cart items and shipping address"""
        try:
            # Get shipping address
            shipping_address_id = request.data.get('shipping_address_id')
            if not shipping_address_id:
                return Response(
                    {'error': 'Shipping address is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify shipping address belongs to user
            try:
                shipping_address = ShippingAddress.objects.get(
                    id=shipping_address_id,
                    user=request.user
                )
            except ShippingAddress.DoesNotExist:
                return Response(
                    {'error': 'Invalid shipping address'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get user's cart
            cart = Cart.objects.filter(user=request.user).first()
            if not cart or not cart.items.exists():
                return Response(
                    {'error': 'Cart is empty'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create order
            order = Order.objects.create(
                user=request.user,
                shipping_address=shipping_address.address_line1,  # Use the address string
                status='pending',
                total_amount=0  # Will be calculated below
            )

            total_amount = 0
            # Create order items from cart items
            for cart_item in cart.items.all():
                # Verify stock availability
                if cart_item.quantity > cart_item.product.stock:
                    order.delete()  # Rollback order creation
                    return Response(
                        {
                            'error': f'Not enough stock for {cart_item.product.title}',
                            'available': cart_item.product.stock
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Calculate item total
                item_total = cart_item.quantity * cart_item.product.price
                
                # Create order item without total field
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                    variation=cart_item.variation
                )

                # Update product stock
                cart_item.product.stock -= cart_item.quantity
                cart_item.product.save()

                total_amount += item_total

            # Update order total
            order.total_amount = total_amount
            order.save()

            # Create shipment tracking with a generated tracking number
            tracking_number = f"TRACK-{order.id}-{timezone.now().strftime('%Y%m%d')}"
            ShipmentTracking.objects.create(
                order=order,
                tracking_number=tracking_number,
                carrier="Default Carrier",  # You can modify this as needed
                status='pending'
            )

            # Clear the cart
            cart.items.all().delete()

            return Response({
                'status': 'success',
                'message': 'Order placed successfully',
                'order_id': order.id,
                'tracking_number': tracking_number,
                'total_amount': total_amount
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def cancel_order(self, request, pk=None):
        order = self.get_object()
        order.status = 'cancelled'
        order.save()
        return Response({'status': 'order cancelled'})

    @action(detail=False, methods=['post'], url_path='create')
    def create_order(self, request):
        try:
            # Validate required fields
            shipping_address = request.data.get('shipping_address')
            items = request.data.get('items')
            
            if not shipping_address or not items:
                return Response({
                    'error': 'Shipping address and items are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create the order
            order = Order.objects.create(
                user=request.user,
                shipping_address=shipping_address,
                status='pending',
                total_amount=0
            )

            total_amount = 0
            # Create order items
            for item in items:
                product = Product.objects.get(id=item['product_id'])
                quantity = item.get('quantity', 1)
                
                # Verify stock
                if product.stock < quantity:
                    order.delete()
                    return Response({
                        'error': f'Not enough stock for {product.title}',
                        'available': product.stock
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price,
                    variation=item.get('variation', '')
                )

                # Update product stock
                product.stock -= quantity
                product.save()

                # Update total amount
                total_amount += quantity * product.price

            # Update order total
            order.total_amount = total_amount
            order.save()

            # Create shipment tracking
            tracking_number = f"TRACK-{order.id}-{timezone.now().strftime('%Y%m%d')}"
            ShipmentTracking.objects.create(
                order=order,
                tracking_number=tracking_number,
                carrier="Default Carrier",
                status='pending'
            )

            return Response({
                'status': 'success',
                'message': 'Order created successfully',
                'order_id': order.id,
                'tracking_number': tracking_number,
                'total_amount': total_amount
            }, status=status.HTTP_201_CREATED)

        except Product.DoesNotExist:
            return Response({
                'error': 'Product not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for user management
    Provides CRUD operations: Create, Read, Update, Delete
    """
    queryset = CustomUser.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filter queryset based on user role:
        - Admin/Manager can see all users
        - Regular users can only see their own profile
        """
        user = self.request.user
        if user.role in [CustomUser.ADMIN, CustomUser.MANAGER]:
            return CustomUser.objects.all()
        return CustomUser.objects.filter(id=user.id)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get current user's profile
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """
        Update current user's profile
        """
        user = request.user
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete user account
        """
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({"detail": "User account has been deactivated."}, 
                      status=status.HTTP_204_NO_CONTENT)

class ProductDetailView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        # Debug print
        print(f"Requested slug: {self.kwargs.get('slug')}")
        
        queryset = Product.objects.filter(is_deleted=False)
        
        # If user is admin/manager, show all non-deleted products
        if self.request.user.is_authenticated and self.request.user.role in ['admin', 'manager']:
            return queryset
            
        # For regular users, only show published products
        return queryset.filter(status='published')

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    @action(detail=False, methods=['POST'])
    def add(self, request):
        try:
            product_id = request.data.get('product_id')
            quantity = int(request.data.get('quantity', 1))
            variation = request.data.get('variation')
            
            # Validate product
            try:
                product = Product.objects.get(id=product_id, is_deleted=False, status='published')
            except Product.DoesNotExist:
                return Response(
                    {'error': 'Product not found or unavailable'}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check stock
            if product.stock < quantity:
                return Response(
                    {'error': 'Not enough stock available'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get or create cart
            cart, _ = Cart.objects.get_or_create(user=request.user)
            
            # Get or create cart item
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                variation=variation,
                defaults={'quantity': quantity}
            )

            # If item already existed, update quantity
            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            serializer = CartItemSerializer(cart_item)
            return Response({
                'status': 'success',
                'message': 'Item added to cart',
                'cart_item': serializer.data
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['DELETE'])
    def clear(self, request):
        """Clear all items from cart"""
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart.items.all().delete()
            return Response({'status': 'Cart cleared'})
        return Response({'status': 'Cart is already empty'})

    @action(detail=True, methods=['PATCH'], url_path='items/(?P<item_id>[^/.]+)')
    def update_item(self, request, item_id=None, pk=None):
        """Update quantity of specific cart item"""
        try:
            cart_item = CartItem.objects.get(
                cart__user=request.user,
                id=item_id
            )
            
            quantity = request.data.get('quantity', cart_item.quantity)
            
            if quantity <= 0:
                cart_item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
                
            if quantity > cart_item.product.stock:
                return Response(
                    {'error': 'Not enough stock available'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            cart_item.quantity = quantity
            cart_item.save()
            
            serializer = CartItemSerializer(cart_item)
            return Response(serializer.data)
            
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['DELETE'], url_path='items/(?P<item_id>[^/.]+)')
    def delete_item(self, request, item_id=None, pk=None):
        """Delete specific item from cart"""
        try:
            cart_item = CartItem.objects.get(
                cart__user=request.user,
                id=item_id
            )
            cart_item.delete()
            return Response(
                {'status': 'Item removed from cart'},
                status=status.HTTP_204_NO_CONTENT
            )
            
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND
            )