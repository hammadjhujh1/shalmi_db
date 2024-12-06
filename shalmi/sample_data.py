from myapp.models import Category, SubCategory, Product, CustomUser, ProductLabel
from django.core.files import File
from decimal import Decimal

def create_sample_data():
    # Create a seller user
    seller, created = CustomUser.objects.get_or_create(
        username="seller2",
        email="seller2@example.com",
        defaults={
            'role': CustomUser.SELLER,
            'is_active': True
        }
    )
    if created:
        seller.set_password("password123")
        seller.save()

    # Create Categories
    categories_data = [
        {
            "name": "Books",
            "description": "Books for all interests and age groups",
            "subcategories": [
                {"name": "Fiction", "description": "Novels and fictional books"},
                {"name": "Non-Fiction", "description": "Biographies, history, and more"},
                {"name": "Children's Books", "description": "Books for kids"}
            ]
        },
        {
            "name": "Sports",
            "description": "Sports equipment and gear",
            "subcategories": [
                {"name": "Football", "description": "Football accessories and gear"},
                {"name": "Cycling", "description": "Bikes and cycling accessories"},
                {"name": "Fitness", "description": "Gym and workout equipment"}
            ]
        },
        {
            "name": "Toys & Games",
            "description": "Toys and games for all ages",
            "subcategories": [
                {"name": "Action Figures", "description": "Collectible action figures"},
                {"name": "Board Games", "description": "Strategy and family games"},
                {"name": "Outdoor Toys", "description": "Toys for outdoor activities"}
            ]
        }
    ]

    # Create categories and subcategories
    for cat_data in categories_data:
        category, _ = Category.objects.get_or_create(
            name=cat_data["name"],
            defaults={
                "description": cat_data["description"]
            }
        )
        
        # Create subcategories for this category
        for subcat_data in cat_data["subcategories"]:
            SubCategory.objects.get_or_create(
                name=subcat_data["name"],
                category=category,
                defaults={
                    "description": subcat_data["description"]
                }
            )

    # Create sample products
    products_data = [
        {
            "title": "The Great Gatsby",
            "category": "Books",
            "subcategory": "Fiction",
            "description": "A classic novel by F. Scott Fitzgerald",
            "price": Decimal("12.99"),
            "stock": 150,
            "status": "published"
        },
        {
            "title": "The Catcher in the Rye",
            "category": "Books",
            "subcategory": "Fiction",
            "description": "A novel by J.D. Salinger",
            "price": Decimal("10.99"),
            "stock": 200,
            "status": "published"
        },
        {
            "title": "Football Cleats",
            "category": "Sports",
            "subcategory": "Football",
            "description": "Durable football cleats for players",
            "price": Decimal("69.99"),
            "stock": 50,
            "status": "published"
        },
        {
            "title": "Mountain Bike",
            "category": "Sports",
            "subcategory": "Cycling",
            "description": "Sturdy mountain bike for off-road cycling",
            "price": Decimal("499.99"),
            "stock": 30,
            "status": "published"
        },
        {
            "title": "Outdoor Adventure Set",
            "category": "Toys & Games",
            "subcategory": "Outdoor Toys",
            "description": "Outdoor set for fun and adventure",
            "price": Decimal("29.99"),
            "stock": 75,
            "status": "published"
        }
    ]

    # Create products
    for prod_data in products_data:
        category = Category.objects.get(name=prod_data["category"])
        subcategory = SubCategory.objects.get(
            name=prod_data["subcategory"],
            category=category
        )
        
        product, created = Product.objects.get_or_create(
            title=prod_data["title"],
            defaults={
                "owner": seller,
                "category": category,
                "subcategory": subcategory,
                "description": prod_data["description"],
                "price": prod_data["price"],
                "stock": prod_data["stock"],
                "status": prod_data["status"]
            }
        )

    print("Sample data created successfully!")

# Run the function
if __name__ == "__main__":
    create_sample_data()
