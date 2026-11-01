from django.urls import path
from category.views import CategoryCreateView,CategoryUpdateDeleteApi
from product.views import ProductCreateView,ProductUpdateDeleteApi
from order.views import AdminAllOrdersAPIView,AdminOrderDetailUpdateAPIView
from .views import AdminDashboardStatistics,AdminMonthlyRevenueAPIView,AdminLastSevenDaysOrderAPIView,AdminUserListAPIView,AdminUserDeleteAPIView



urlpatterns = [
    #category
    path('category/', CategoryCreateView.as_view(), name='category-create'),
    path('category/<int:pk>/', CategoryUpdateDeleteApi.as_view(), name='category-update-delete'),


    #product
    path('product/',ProductCreateView.as_view(),name='product-create'),
    path('product/<int:pk>/',ProductUpdateDeleteApi.as_view(),name='product-update-delete'),

    #order
    path('order/',AdminAllOrdersAPIView.as_view(),name='all-admin-order'),
    path("order/<int:pk>/",AdminOrderDetailUpdateAPIView.as_view(),name="update-get-order"),

    #dashboard
    path('statistics/', AdminDashboardStatistics.as_view(), name='admin-dashboard-statistics'),
    path('monthly-revenue/', AdminMonthlyRevenueAPIView.as_view(), name='admin-monthly-revenue'),
    path('last-seven-days-orders/', AdminLastSevenDaysOrderAPIView.as_view(), name='admin-last-seven-days-orders'),

    #asmin user management
    path('users/', AdminUserListAPIView.as_view(), name='admin-user-list'),
    path('users/<int:user_id>/', AdminUserDeleteAPIView.as_view(), name='admin-user-delete'),

    
]