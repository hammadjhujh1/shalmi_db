from django.urls import path
from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import ProductViewSet, CategoryViewSet, SubCategoryViewSet, OrderViewSet, ShippingAddressViewSet, ShipmentTrackingViewSet, NewArrivalsViewSet, UserViewSet, TrendingProductsViewSet, WholesaleProductsViewSet, FeaturedProductsViewSet, DiscountedProductsViewSet, TopSellingProductsViewSet

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


urlpatterns = [
    path('all/', views.home_page, name='home_page'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    

    # Include the router's URLs for the API endpoints
    path('api/', include(router.urls)),

    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('buyer_dashboard/', views.buyer_dashboard, name='buyer_dashboard'),
    path('analytics_dashboard/', views.analytics_dashboard, name='analytics_dashboard'),
    path('seller_analytics/', views.seller_analytics, name='seller_analytics'),
    path('api_integration/', views.api_integration, name='api_integration'),
    path('notifications/', views.notifications, name='notifications'),
    path('contact_us/', views.contact_us, name='contact_us'),
    path('faqs/', views.faqs, name='faqs'),
    path('about_us/', views.about_us, name='about_us'),
    path('privacy_policy/', views.privacy_policy, name='privacy_policy'),
    path('terms_conditions/', views.terms_conditions, name='terms_conditions'),
    path('refund_policy/', views.refund_policy, name='refund_policy'),
    path('shipping_policy/', views.shipping_policy, name='shipping_policy'),
    path('help_centre/', views.help_centre, name='help_centre'),
    path('live_chat_support/', views.live_chat_support, name='live_chat_support'),
    path('discussion_forum/', views.discussion_forum, name='discussion_forum'),
    path('partner_institutions/', views.partner_institutions, name='partner_institutions'),
    path('landing_promotions/', views.landing_promotions, name='landing_promotions'),
    path('loyalty_program/', views.loyalty_program, name='loyalty_program'),
    path('premium_subscription/', views.premium_subscription, name='premium_subscription'),
    path('user_reviews/', views.user_reviews, name='user_reviews'),
    path('affiliate_program/', views.affiliate_program, name='affiliate_program'),
    path('blog/', views.blog, name='blog'),
    path('careers/', views.careers, name='careers'),
    path('payment_gateway/', views.payment_gateway, name='payment_gateway'),
    path('checkout_page/', views.checkout_page, name='checkout_page'),
    path('inventory_management/', views.inventory_management, name='inventory_management'),
    path('order_configuration/', views.order_configuration, name='order_configuration'),
    path('order_tracking/', views.order_tracking, name='order_tracking'),
    path('product_management/', views.product_management, name='product_management'),
    path('products_details/', views.products_details, name='products_details'),
    path('profile_page/', views.profile_page, name='profile_page'),
    path('request_product_sample/', views.request_product_sample, name='request_product_sample'),
    path('search_result_page/', views.search_result_page, name='search_result_page'),
    path('seller_dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('setting_page/', views.setting_page, name='setting_page'),
    path('trending_top_selling_products/', views.trending_top_selling_products, name='trending_top_selling_products'),
    path('upload_product/', views.upload_product, name='upload_product'),
    path('users_management/', views.users_management, name='users_management'),






    path('', views.all_pages, name='all_pages'),
    path('api/get-csrf-token/', views.get_csrf_token, name='get-csrf-token'),
    path('api/signup/', views.signup, name='signup'),
    path('api/upload/', ProductViewSet.as_view({'post': 'create'}), name='product-upload'),
    path('logout/', views.logout_user, name='logout'),
]
