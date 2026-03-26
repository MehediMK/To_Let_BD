from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('property/<int:pk>/', views.property_detail, name='property_detail'),
    path('search/', views.search, name='search'),
    path('signup/', views.signup_view, name='signup'),
    path('signin/', views.signin_view, name='signin'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('list-property/', views.list_property_view, name='list_property'),
    path('my-properties/', views.my_properties_view, name='my_properties'),
    path('edit-property/<int:pk>/', views.edit_property_view, name='edit_property'),
    path('delete-property/<int:pk>/', views.delete_property_view, name='delete_property'),
    path('add-image/<int:pk>/', views.add_property_image, name='add_property_image'),
    path('delete-image/<int:pk>/', views.delete_property_image, name='delete_property_image'),
    path('favorite/<int:pk>/', views.toggle_favorite, name='toggle_favorite'),
    path('favorites/', views.favorites_view, name='favorites'),
    path('dashboard/', views.dashboard_home, name='dashboard'),
    path('inquiry/<int:pk>/', views.submit_inquiry, name='submit_inquiry'),
    path('my-inquiries/', views.my_inquiries_view, name='my_inquiries'),
    path('verify-email/', views.send_verification_view, name='send_verification'),
    path('verify-email/<str:token>/', views.verify_email_view, name='verify_email'),
    # Reviews
    path('property/<int:pk>/review/', views.add_review_view, name='add_review'),
    path('review/<int:pk>/delete/', views.delete_review_view, name='delete_review'),
    path('review/<int:pk>/respond/', views.respond_review_view, name='respond_review'),
    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:pk>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    # Messaging
    path('inbox/', views.inbox_view, name='inbox'),
    path('outbox/', views.outbox_view, name='outbox'),
    path('send-message/', views.send_message_view, name='send_message'),
    path('send-message/<int:receiver_id>/', views.send_message_view, name='send_message_to'),
    path('send-message/property/<int:property_id>/', views.send_message_view, name='send_message_property'),
    path('reply-message/<int:pk>/', views.reply_message_view, name='reply_message'),
    path('message/<int:pk>/delete/', views.delete_message_view, name='delete_message'),
]
