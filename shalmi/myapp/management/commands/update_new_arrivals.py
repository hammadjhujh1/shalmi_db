from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from myapp.models import ProductLabel

class Command(BaseCommand):
    help = 'Updates new arrival status for products older than 30 days'

    def handle(self, *args, **kwargs):
        # Get date 30 days ago
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Get labels for products created more than 30 days ago
        old_new_arrival_labels = ProductLabel.objects.filter(
            is_new_arrival=True,
            created_at__lt=thirty_days_ago
        )
        
        # Update the labels
        count = old_new_arrival_labels.update(is_new_arrival=False)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {count} products\' new arrival status')
        ) 