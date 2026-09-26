from django.urls import path
from category.views import CategoryCreateView,CategoryUpdateDeleteApi



urlpatterns = [
    #category
    path('category/', CategoryCreateView.as_view(), name='category-create'),
    path('category/<int:pk>/', CategoryUpdateDeleteApi.as_view(), name='category-update-delete'),


    
]