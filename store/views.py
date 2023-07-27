import django
from django.contrib.auth.models import User
from store.models import Address, Cart, Category, Order, Product, payments, Rationcarddetails, staff,feedback
from django.shortcuts import redirect, render, get_object_or_404
from .forms import RegistrationForm, AddressForm, addstockform, dailreportform, addproductform, RationcardForm, \
    StaffUpdateorderForm, LoginForm
from django.contrib import messages
from django.views import View
import decimal
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator  # for Class Based Views
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField, PasswordChangeForm, \
    PasswordResetForm, SetPasswordForm
from django.db import models
from django.db.models import fields
from django.forms import widgets
from django.forms.fields import CharField
from django.utils.translation import gettext, gettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.conf import settings


# Create your views here.
def new(request):
    return render(request, 'new.html')

def care(request):
    return render(request, 'store/care.html')

def new11(request):
    return render(request, 'new11.html')


def home(request):
    categories = Category.objects.filter(is_active=True, is_featured=True)[:3]
    products = Product.objects.filter(is_active=True, is_featured=True)[:8]
    context = {
        'categories': categories,
        'products': products,
    }

    # for x in categories:
    #     print(x)
    for y in products:
        print(y.title, '------->', y.product_image)
    return render(request, 'store/index.html', context)


def detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.exclude(id=product.id).filter(is_active=True, category=product.category)
    context = {
        'product': product,
        'related_products': related_products,

    }
    return render(request, 'store/detail.html', context)


def all_categories(request):
    categories = Category.objects.filter(is_active=True)
    return render(request, 'store/categories.html', {'categories': categories})


def category_products(request, slug):
    print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(is_active=True, category=category)
    categories = Category.objects.filter(is_active=True)
    context = {
        'category': category,
        'products': products,
        'categories': categories,
    }

    print(category)
    print(products)
    print(categories)
    return render(request, 'store/category_products.html', context)


def raticarddet(request):
    context = {}

    # create object of form
    form = RationcardForm(request.POST or None, request.FILES or None)

    # check if form data is valid
    if form.is_valid():
        # save the form data to model
        form.save()

    context['form'] = form
    return render(request, 'store/addrationcard.html', context)


# Authentication Starts Here

class RegistrationView(View):
    def get(self, request):
        form = RegistrationForm()
        return render(request, 'account/register.html', {'form': form})

    def post(self, request):
        form = RegistrationForm(request.POST)
        print(form)
        if form.is_valid():
            messages.success(request, "Congratulations! Registration Successful!")
            form.save()
        return render(request, 'account/register.html', {'form': form})


class LoginView(View):
    template_name = 'account/login.html'
    form_class = LoginForm

    def get(self, request):
        form = self.form_class()
        message = ''
        return render(request, self.template_name, context={'form': form, 'message': message})

    def post(self, request):
        form = self.form_class(request.POST)
        print(form)
        print('ggggg')
        print(request.POST['username'])
        print(request.POST['password'])
        if not form.is_valid():
            user = authenticate(
                username=request.POST['username'],
                password=request.POST['password'],
            )

            print('user--->',user)

            if user is not None:
                login(request, user)
                return redirect('store:profile')
        message = 'Login failed!'
        # return redirect('store:profile')
        return render(request,'account/login.html')
@login_required
def profile(request):
    addresses = Address.objects.filter(user=request.user)
    orders = Order.objects.filter(user=request.user)
    return render(request, 'account/profile.html', {'addresses': addresses, 'orders': orders})


@method_decorator(login_required, name='dispatch')
class AddressView(View):
    def get(self, request):
        form = AddressForm()
        return render(request, 'account/add_address.html', {'form': form})

    def post(self, request):
        form = AddressForm(request.POST)
        if form.is_valid():
            user = request.user
            locality = form.cleaned_data['locality']
            city = form.cleaned_data['city']
            mobno = form.cleaned_data['mobno']
            reg = Address(user=user, locality=locality, city=city, mobno=mobno)
            reg.save()
            messages.success(request, "New Address Added Successfully.")
        return redirect('store:profile')


@login_required
def remove_address(request, id):
    a = get_object_or_404(Address, user=request.user, id=id)
    a.delete()
    messages.success(request, "Address removed.")
    return redirect('store:profile')


@login_required
def add_to_cart(request):
    user = request.user
    product_id = request.GET.get('prod_id')
    product = get_object_or_404(Product, id=product_id)

    # Check whether the Product is alread in Cart or Not
    item_already_in_cart = Cart.objects.filter(product=product_id, user=user)
    if item_already_in_cart:
        cp = get_object_or_404(Cart, product=product_id, user=user)
        cp.quantity += 1
        cp.save()
    else:
        Cart(user=user, product=product).save()

    return redirect('store:cart')


@login_required
def cart(request):
    user = request.user
    cart_products = Cart.objects.filter(user=user)

    # Display Total on Cart Page
    amount = decimal.Decimal(0)
    shipping_amount = decimal.Decimal(10)
    # using list comprehension to calculate total amount based on quantity and shipping
    cp = [p for p in Cart.objects.all() if p.user == user]
    if cp:
        for p in cp:
            temp_amount = (p.quantity * p.product.price)
            amount += temp_amount

    # Customer Addresses
    addresses = Address.objects.filter(user=user)

    context = {
        'cart_products': cart_products,
        'amount': amount,
        'shipping_amount': shipping_amount,
        'total_amount': amount + shipping_amount,
        'addresses': addresses,
    }
    return render(request, 'store/cart.html', context)


@login_required
def remove_cart(request, cart_id):
    if request.method == 'GET':
        c = get_object_or_404(Cart, id=cart_id)
        c.delete()
        messages.success(request, "Product removed from Cart.")
    return redirect('store:cart')


@login_required
def plus_cart(request, cart_id):
    if request.method == 'GET':
        cp = get_object_or_404(Cart, id=cart_id)
        cp.quantity += 1
        cp.save()
    return redirect('store:cart')


@login_required
def minus_cart(request, cart_id):
    if request.method == 'GET':
        cp = get_object_or_404(Cart, id=cart_id)
        # Remove the Product if the quantity is already 1
        if cp.quantity == 1:
            cp.delete()
        else:
            cp.quantity -= 1
            cp.save()
    return redirect('store:cart')


@login_required
def checkout(request):
    user = request.user
    address_id = request.GET.get('address')

    address = get_object_or_404(Address, id=address_id)
    # Get all the products of User in Cart
    cart = Cart.objects.filter(user=user)
    for c in cart:
        # Saving all the products from Cart to Order
        Order(user=user, address=address, product=c.product, quantity=c.quantity).save()
        # And Deleting from Cart
        c.delete()
    return redirect('store:orders')


@login_required
def orders(request):
    all_orders = Order.objects.filter(user=request.user).order_by('-ordered_date')
    return render(request, 'store/orders.html', {'orders': all_orders})


def shop(request):
    return render(request, 'store/shop.html')


def test(request):
    return render(request, 'store/test.html')


def paymentview(request):
    if request.method == 'POST':
        cardname = request.POST['cardname']
        cardno = request.POST['cardno']

        amount = request.POST['amount']
        payments(name=cardname, cardno=cardno, amount=amount).save()
        return redirect('store:orders')
    return render(request, 'store/payment.html')


# staff
# def stafflogin(request):
#     # staffId = request.form['staff_id']
#
#     # print('$$$$$$', staffId)
#     # staffdetails = staff.objects.get(id=staff_id, name=name, password=password)
#     #
#     return render(request, 'staff/stafflogin.html')


def staffloginaction(request):
    if request.method == 'POST':

        staffId = request.POST['staff_id']
        name = request.POST['name']
        password = request.POST['password']

        print('$$$$$', staffId)
        print('$$$$$', name)
        print('$$$$$', password)

        staffdetails = staff.objects.get(staff_id=staffId, name=name, password=password)

        if staffdetails:
            return render(request, 'staff/staffhome.html')

        print('%%%%%%%%', staffdetails)
    return render(request, 'staff/stafflogin.html')


def staffhome(request):
    return render(request, 'staff/staffhome.html')


def addproducts(request):
    context = {}

    print('%%%%%%', request.FILES)
    print('%%%%%%', request.POST)
    # create object of form
    form = addproductform(request.POST or None, request.FILES or None)

    print('&&&&&', form)

    # check if form data is valid
    if form.is_valid():
        # save the form data to model
        form.save()

    context['form'] = form
    return render(request, "staff/addproduct.html", context)


def stafftakeorder(request):
    all_orders = Order.objects.filter(user=request.user).order_by('-ordered_date')

    return render(request, 'staff/takeorder.html', {'orders': all_orders, })


def staffupdateorder(request):
    context = {}

    # create object of form
    form = StaffUpdateorderForm(request.POST or None, request.FILES or None)

    # check if form data is valid
    if form.is_valid():
        # save the form data to model
        form.save(commit=False)

    context['form'] = form

    return render(request, 'staff/updateorder.html', context)


def staffviewcustomer(request):
    context = {
        'customerdetails': Address.objects.all(),
    }

    return render(request, 'staff/viewcustomerdetail.html', context)


def staffviewrationcard(request):
    context = {
        'ration': Rationcarddetails.objects.all(),
    }
    return render(request, 'staff/viewrationcard.html', context)


def staffaddreport(request):
    context = {}

    # create object of form
    form = dailreportform(request.POST or None, request.FILES or None)

    # check if form data is valid
    if form.is_valid():
        # save the form data to model
        form.save()

    context['form'] = form
    return render(request, 'staff/addreport.html', context)


def staffaddstock(request):
    context = {}

    # create object of form
    form = addstockform(request.POST or None, request.FILES or None)

    # check if form data is valid
    if form.is_valid():
        # save the form data to model
        form.save()

    context['form'] = form
    return render(request, 'staff/addstock.html', context)


def staffvieworderdetails(request):
    all_orders = Order.objects.filter(user=request.user).order_by('-ordered_date')
    return render(request, 'staff/view orderdetails.html', {'orders': all_orders})


def getsubseedycat(request):

    cat=Category.objects.filter(choice='Subseedy')
    print(cat)
    if cat:
        return render(request, 'store/subseedyproduct.html', {'cat': cat})

    # caat1=Category.objects.filter(choice='NoSubseedy')


def getnosubseedycat(request):

    cati = Category.objects.filter(choice='Nosubseedy')
    print(cati)
    if cati:
        return render(request,'store/nosubseedyproduct.html',{'cati':cati})


def feedpage(request):
    if request.method=='POST':
        name=request.POST['name']   
        surname=request.POST['surname']
        email=request.POST['email']
        comment=request.POST['comment']
        feedback(Name=name,Surname=surname,Email=email,Comment=comment).save()
        messages.success(request,'The New Feedback '+request.POST['name']+" is saved Successfully...!")
        return render(request,'store/feedback.html')
    else:
        return render(request,'store/feedback.html')



