from django.apps import AppConfig
import os


class MyappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "myapp"

    def ready(self):
        import myapp.signals  # Import signals here
        media_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'media')
        products_dir = os.path.join(media_root, 'products')
        
        os.makedirs(media_root, exist_ok=True)
        os.makedirs(products_dir, exist_ok=True)
