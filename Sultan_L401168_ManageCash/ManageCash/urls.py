from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    
    # Cash management
    path('add-cash/', views.add_cash, name='add_cash'),
    path('cash-list/', views.cash_list, name='cash_list'),
    path('cash/<int:pk>/delete/', views.delete_cash, name='delete_cash'),
    
    # Expense management
    path('add-expense/', views.add_expense, name='add_expense'),
    path('expense-list/', views.expense_list, name='expense_list'),
    path('expense/<int:pk>/delete/', views.delete_expense, name='delete_expense'),
]
