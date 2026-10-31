from django.urls import path
from category.views import CategoryCreateView,CategoryUpdateDeleteApi
from product.views import ProductCreateView,ProductUpdateDeleteApi
from order.views import AdminAllOrdersAPIView,AdminOrderDetailUpdateAPIView



urlpatterns = [
    #category
    path('category/', CategoryCreateView.as_view(), name='category-create'),
    path('category/<int:pk>/', CategoryUpdateDeleteApi.as_view(), name='category-update-delete'),


    #product
    path('product/',ProductCreateView.as_view(),name='product-create'),
    path('product/<int:pk>/',ProductUpdateDeleteApi.as_view(),name='product-update-delete'),

    #order
    path('order/',AdminAllOrdersAPIView.as_view(),name='all-admin-order'),
    path("order/<int:pk>/",AdminOrderDetailUpdateAPIView.as_view(),name="update-get-order")


    
]