from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CustomUser, Product, Category, SubCategory, ShippingAddress, ShipmentTracking, Order, OrderItem, ProductLabel
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from .serializers import (
    CategorySerializer, CategoryCreateSerializer,
    SubCategorySerializer, SubCategoryCreateSerializer,
    ProductSerializer, ProductCreateSerializer,
    ShippingAddressSerializer, ShipmentTrackingSerializer,
    OrderSerializer
)
from .permissions import IsAdminManagerOrReadOnly
import json
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def signup(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        trade_role = request.POST.get('trade-role')

        # Create a new user
        user = CustomUser(email=email, username=email)  # You can customize username as needed
        user.set_password(password)  # Hash the password
        user.role = trade_role  # Assign the trade role
        user.save()  # Save the user to the database

        messages.success(request, "Account created successfully. Please log in.")
        return redirect('login')  # Redirect to the login page

    return render(request, 'signup.html')  # Render the signup template

@csrf_exempt
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



# Product ViewSet
class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateSerializer
        return ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(is_deleted=False)

    def create(self, request, *args, **kwargs):
        # Convert string variations to JSON if needed
        if 'variations' in request.data:
            try:
                if isinstance(request.data['variations'], str):
                    request.data['variations'] = {'variations': request.data['variations']}
            except json.JSONDecodeError:
                return Response(
                    {'error': 'Invalid variations format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
class NewArrivalsViewSet(viewsets.ViewSet):
    """API endpoint that returns products where is_new_arrival is True"""

    def list(self, request):
        new_arrival_labels = ProductLabel.objects.filter(is_new_arrival=True)
        products = [label.products.all() for label in new_arrival_labels]
        products = [product for sublist in products for product in sublist]
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)



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

    def get_queryset(self):
        user = self.request.user
        if user.role in [user.MANAGER, user.ADMIN]:
            return ShipmentTracking.objects.all()
        return ShipmentTracking.objects.filter(order__user=user)

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

    @action(detail=True, methods=['post'])
    def cancel_order(self, request, pk=None):
        order = self.get_object()
        order.status = 'cancelled'
        order.save()
        return Response({'status': 'order cancelled'})