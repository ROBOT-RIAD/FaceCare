from django.db import models
from category.models import Category
import random
import string

# Create your models here.


class Product(models.Model):
    category = models.ForeignKey(Category,on_delete=models.CASCADE,related_name="products")


    title = models.CharField(max_length=400)
    sub_title = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    key_ingredients = models.TextField(blank=True, null=True)


    size = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    discount = models.DecimalField(max_digits=5,decimal_places=2,default=0)


    stock = models.PositiveIntegerField(default=0)
    reserved_stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)


    skin_type = models.CharField(max_length=300,blank=True,null=True)
    key_benefits = models.TextField(blank=True,null=True)
    how_to_use = models.TextField(blank=True,null=True)


    image = models.URLField(max_length=1000,blank=True,null=True)
    cloudinary_public_id = models.CharField(max_length=500,unique=True,blank=True,null=True)


    sku = models.CharField(max_length=100,unique=True)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_sku(self):
        prefix = (self.category.name[:2] if self.category.name else "PR").upper()

        random_number = ''.join(random.choices(string.digits, k=8))

        return f"{prefix}{random_number}"

    def save(self, *args, **kwargs):
        if not self.sku:
            sku = self.generate_sku()

            # ensure uniqueness
            while Product.objects.filter(sku=sku).exists():
                sku = self.generate_sku()

            self.sku = sku

        super().save(*args, **kwargs)


    def __str__(self):
        return self.title

