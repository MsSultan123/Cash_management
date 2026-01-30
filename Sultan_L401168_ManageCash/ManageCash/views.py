from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Q
from django.views.decorators.http import require_http_methods
from .models import AddCash, Expense


def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        
        # Validation
        if not all([email, username, password]):
            messages.error(request, 'Email, Username, and Password are required!')
            return render(request, 'ManageCash/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return render(request, 'ManageCash/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return render(request, 'ManageCash/register.html')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        login(request, user)
        messages.success(request, 'Account created successfully!')
        return redirect('dashboard')
    
    return render(request, 'ManageCash/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'ManageCash/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('login')


@login_required(login_url='login')
def dashboard(request):
    # Get all cash additions and expenses for the current user
    cash_additions = AddCash.objects.filter(user=request.user).order_by('-datetime')
    expenses = Expense.objects.filter(user=request.user).order_by('-datetime')
    
    # Calculate totals
    total_added = AddCash.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    total_spent = Expense.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_added - total_spent
    
    # Get recent transactions (last 5)
    recent_added = cash_additions[:5]
    recent_expenses = expenses[:5]
    
    context = {
        'total_added': total_added,
        'total_spent': total_spent,
        'balance': balance,
        'cash_additions_count': cash_additions.count(),
        'expenses_count': expenses.count(),
        'recent_added': recent_added,
        'recent_expenses': recent_expenses,
    }
    
    return render(request, 'ManageCash/dashboard.html', context)


@login_required(login_url='login')
def add_cash(request):
    if request.method == 'POST':
        source = request.POST.get('source', '')
        amount = request.POST.get('amount', '')
        description = request.POST.get('description', '')
        
        if not source or not amount:
            messages.error(request, 'Source and Amount are required!')
            return render(request, 'ManageCash/add_cash.html')
        
        try:
            amount = float(amount)
            if amount <= 0:
                messages.error(request, 'Amount must be greater than 0!')
                return render(request, 'ManageCash/add_cash.html')
        except ValueError:
            messages.error(request, 'Invalid amount!')
            return render(request, 'ManageCash/add_cash.html')
        
        cash = AddCash.objects.create(
            user=request.user,
            source=source,
            amount=amount,
            description=description
        )
        messages.success(request, 'Cash added successfully!')
        return redirect('dashboard')
    
    return render(request, 'ManageCash/add_cash.html')


@login_required(login_url='login')
def add_expense(request):
    if request.method == 'POST':
        description = request.POST.get('description', '')
        amount = request.POST.get('amount', '')
        
        if not description or not amount:
            messages.error(request, 'Description and Amount are required!')
            return render(request, 'ManageCash/add_expense.html')
        
        try:
            amount = float(amount)
            if amount <= 0:
                messages.error(request, 'Amount must be greater than 0!')
                return render(request, 'ManageCash/add_expense.html')
        except ValueError:
            messages.error(request, 'Invalid amount!')
            return render(request, 'ManageCash/add_expense.html')
        
        expense = Expense.objects.create(
            user=request.user,
            description=description,
            amount=amount
        )
        messages.success(request, 'Expense recorded successfully!')
        return redirect('dashboard')
    
    return render(request, 'ManageCash/add_expense.html')


@login_required(login_url='login')
def cash_list(request):
    cash_additions = AddCash.objects.filter(user=request.user).order_by('-datetime')
    
    # Search functionality
    search_query = request.GET.get('q', '')
    if search_query:
        cash_additions = cash_additions.filter(
            Q(source__icontains=search_query) | Q(description__icontains=search_query)
        )
    
    total = cash_additions.aggregate(Sum('amount'))['amount__sum'] or 0
    count = cash_additions.count()
    average = total / count if count > 0 else 0
    
    context = {
        'cash_additions': cash_additions,
        'search_query': search_query,
        'total': total,
        'average': average,
    }
    
    return render(request, 'ManageCash/cash_list.html', context)


@login_required(login_url='login')
def expense_list(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-datetime')
    
    # Search functionality
    search_query = request.GET.get('q', '')
    if search_query:
        expenses = expenses.filter(description__icontains=search_query)
    
    total = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    count = expenses.count()
    average = total / count if count > 0 else 0
    
    context = {
        'expenses': expenses,
        'search_query': search_query,
        'total': total,
        'average': average,
    }
    
    return render(request, 'ManageCash/expense_list.html', context)


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def delete_cash(request, pk):
    try:
        cash = AddCash.objects.get(pk=pk, user=request.user)
        if request.method == 'POST':
            cash.delete()
            messages.success(request, 'Cash entry deleted successfully!')
            return redirect('cash_list')
        
        return render(request, 'ManageCash/confirm_delete.html', {
            'object': cash,
            'object_type': 'Cash Entry',
            'delete_url': 'delete_cash',
            'pk': pk
        })
    except AddCash.DoesNotExist:
        messages.error(request, 'Entry not found!')
        return redirect('cash_list')


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def delete_expense(request, pk):
    try:
        expense = Expense.objects.get(pk=pk, user=request.user)
        if request.method == 'POST':
            expense.delete()
            messages.success(request, 'Expense deleted successfully!')
            return redirect('expense_list')
        
        return render(request, 'ManageCash/confirm_delete.html', {
            'object': expense,
            'object_type': 'Expense',
            'delete_url': 'delete_expense',
            'pk': pk
        })
    except Expense.DoesNotExist:
        messages.error(request, 'Expense not found!')
        return redirect('expense_list')


@login_required(login_url='login')
def profile(request):
    """View for managing user profile"""
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        
        # Validate
        if not email:
            messages.error(request, 'Email is required!')
            return render(request, 'ManageCash/profile.html')
        
        # Check if email already exists for another user
        if User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
            messages.error(request, 'Email already in use!')
            return render(request, 'ManageCash/profile.html')
        
        # Update user profile
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email
        request.user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    context = {
        'user': request.user,
    }
    return render(request, 'ManageCash/profile.html', context)
