from django.urls import path
from order.views import AddressCreateView, AddressListView,AddressDetailandDeleteView,OrderCreateAPIView,CheckoutPaymentStatusAPIView,UserOrdersAPIView,UserOrderDetailAPIView
from skinintelligence.views import RutineCreateApiview

urlpatterns = [

    #address urls
    path('addresses/', AddressCreateView.as_view(), name='address-create'),
    path('addresses/list/', AddressListView.as_view(), name='address-list'),
    path('addresses/<int:pk>/', AddressDetailandDeleteView.as_view(), name='address-detail'),


    #order
    path("order/", OrderCreateAPIView.as_view(),name="order-create"),
    path("payment-status/",CheckoutPaymentStatusAPIView.as_view(),name="checkout-payment-status"),
    path("orders/",UserOrdersAPIView.as_view(),name="get-all-order"),
    path("order/<int:pk>/",UserOrderDetailAPIView.as_view(),name="user-order-detail",),


    #skin intelligence
    path("skin-intelligence/",RutineCreateApiview.as_view(),name="skin-intelligence")
    
]