from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from django.conf import settings

class CustomUser(AbstractUser):
    END_USER = 'EU'
    MANAGER = 'MGR'
    ADMIN = 'ADM'

    ROLE_CHOICES = [
        (END_USER, 'Simple User'),
        (MANAGER, 'Manager'),
        (ADMIN, 'Admin'),
    ]

    role = models.CharField(max_length=4, choices=ROLE_CHOICES, default=END_USER)

    # Resolve reverse accessor conflicts
    groups = models.ManyToManyField(
        Group,
        related_name="customuser_groups",  # Updated related name
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups"
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_user_permissions",  # Updated related name
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions"
    )

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class SubCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(Category, related_name="subcategories", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['name', 'category']
        verbose_name_plural = "Sub Categories"

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Product(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived')
    ]

    title = models.CharField(max_length=200, unique=True)
    owner = models.ForeignKey(
        'CustomUser', 
        on_delete=models.CASCADE,
        related_name='products',
        limit_choices_to={'role__in': [CustomUser.MANAGER, CustomUser.ADMIN]}
    )
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    subcategory = models.ForeignKey(SubCategory, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    stock = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    variations = models.JSONField(blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.owner.role not in [CustomUser.MANAGER, CustomUser.ADMIN]:
            raise ValidationError("Only managers and admins can create products.")
        super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

class ProductLabel(models.Model):
    products = models.ManyToManyField(
        Product,
        related_name='labels',
        blank=True
    )
    name = models.CharField(max_length=100)  # To identify the label type
    is_top_selling = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_wholesale = models.BooleanField(default=False)
    is_discounted = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.products.count()} products"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.is_new_arrival = True
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Product Label'
        verbose_name_plural = 'Product Labels'

    @property
    def label_count(self):
        return sum([
            self.is_top_selling,
            self.is_trending,
            self.is_featured,
            self.is_wholesale,
            self.is_discounted,
            self.is_new_arrival
        ])



class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    shipping_address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of purchase
    variation = models.JSONField(null=True, blank=True)  # Store selected variations

    def __str__(self):
        return f"{self.quantity}x {self.product.title} in Order #{self.order.id}"


class ShippingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    street_address = models.CharField(max_length=255)
    apartment = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set all other addresses of this user to non-default
            ShippingAddress.objects.filter(user=self.user).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.city}, {self.country}"


class ShipmentTracking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed Delivery'),
        ('returned', 'Returned')
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='shipment')
    tracking_number = models.CharField(max_length=100, unique=True)
    carrier = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    estimated_delivery = models.DateField(null=True, blank=True)
    actual_delivery = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Shipment {self.tracking_number} for Order #{self.order.id}"


class ShipmentUpdate(models.Model):
    shipment = models.ForeignKey(ShipmentTracking, on_delete=models.CASCADE, related_name='updates')
    status = models.CharField(max_length=20, choices=ShipmentTracking.STATUS_CHOICES)
    location = models.CharField(max_length=255)
    description = models.TextField()
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.shipment.tracking_number} - {self.status} at {self.timestamp}"