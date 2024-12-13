from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import ProductViewSet, CategoryViewSet, SubCategoryViewSet, OrderViewSet, ShippingAddressViewSet, ShipmentTrackingViewSet, NewArrivalsViewSet, UserViewSet, TrendingProductsViewSet, WholesaleProductsViewSet, FeaturedProductsViewSet, DiscountedProductsViewSet, TopSellingProductsViewSet, ProductDetailView, CartViewSet

# Initialize the router and register the viewsets
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'subcategories', SubCategoryViewSet, basename='subcategory')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'shipping-addresses', ShippingAddressViewSet, basename='shipping-address')
router.register(r'shipments', ShipmentTrackingViewSet, basename='shipment')
router.register(r'new-arrivals', NewArrivalsViewSet, basename='new-arrivals')
router.register(r'users', UserViewSet, basename='user')
router.register(r'trending', TrendingProductsViewSet, basename='trending')
router.register(r'wholesale', WholesaleProductsViewSet, basename='wholesale')
router.register(r'featured', FeaturedProductsViewSet, basename='featured')
router.register(r'discounted', DiscountedProductsViewSet, basename='discounted')
router.register(r'top-selling', TopSellingProductsViewSet, basename='top-selling')
router.register(r'cart', CartViewSet, basename='cart')


urlpatterns = [
        # Product detail route must come BEFORE router.urls
    path('', include(router.urls)),
    path('products/<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    path('get-csrf-token/', views.get_csrf_token, name='get-csrf-token'),
    path('signup/', views.signup, name='signup'),    
    # Auth routes
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_user, name='logout')
]
