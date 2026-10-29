from django.urls import path
from order.views import AddressCreateView, AddressListView,AddressDetailandDeleteView,OrderCreateAPIView,CheckoutPaymentStatusAPIView

urlpatterns = [

    #address urls
    path('addresses/', AddressCreateView.as_view(), name='address-create'),
    path('addresses/list/', AddressListView.as_view(), name='address-list'),
    path('addresses/<int:pk>/', AddressDetailandDeleteView.as_view(), name='address-detail'),


    #order
    path("Order/", OrderCreateAPIView.as_view(),name="order-create"),
    path("payment-status/",CheckoutPaymentStatusAPIView.as_view(),name="checkout-payment-status"),
    
]