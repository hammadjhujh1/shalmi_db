from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product, ProductLabel

@receiver(post_save, sender=Product)
def create_product_labels(sender, instance, created, **kwargs):
    """Create a ProductLabel instance with all flags for a new product"""
    if created:
        # Create a single label instance with all flags
        label = ProductLabel.objects.create(
            name=f"Labels for {instance.title}",
            is_new_arrival=True,      # True by default for new products
            is_trending=False,        # All other flags start as False
            is_featured=False,
            is_wholesale=False,
            is_discounted=False,
            is_top_selling=False
        )
        # Add the product to this label
        label.products.add(instance) 