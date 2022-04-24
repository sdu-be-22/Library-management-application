from datetime import date

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.shortcuts import render

from librarymanagement.settings import EMAIL_HOST_USER
from . import forms, models


def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'library/index.html')



def studentclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'library/studentclick.html')



def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'library/adminclick.html')


def adminsignup_view(request):
    form = forms.AdminSignupForm()
    if request.method == 'POST':
        print(request.POST)
        form = forms.AdminSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            print(user)
            user.set_password(user.password)
            user.save()

            my_admin_group = Group.objects.get_or_create(name='ADMIN')
            print(my_admin_group[0].user_set.values())
            my_admin_group[0].user_set.add(user)

            return HttpResponseRedirect('adminlogin')
    return render(request, 'library/adminsignup.html', {'form': form})


def studentsignup_view(request):
    form1 = forms.StudentUserForm()
    form2 = forms.StudentExtraForm()
    mydict = {'form1': form1, 'form2': form2}
    if request.method == 'POST':
        form1 = forms.StudentUserForm(request.POST)
        form2 = forms.StudentExtraForm(request.POST)
        if form1.is_valid() and form2.is_valid():
            user = form1.save()
            user.set_password(user.password)
            user.save()
            f2 = form2.save(commit=False)
            f2.user = user
            user2 = f2.save()

            my_student_group = Group.objects.get_or_create(name='STUDENT')
            my_student_group[0].user_set.add(user)

        return HttpResponseRedirect('studentlogin')
    return render(request, 'library/studentsignup.html', context=mydict)

def is_admin(user):
    return user.groups.filter(name='ADMIN').exists()


def afterlogin_view(request):
    if is_admin(request.user):
        return render(request, 'library/adminafterlogin.html')
    else:
        return render(request, 'library/studentafterlogin.html')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def addbook_view(request):
    
    form = forms.BookForm()
    if request.method == 'POST':
        
        form = forms.BookForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'library/bookadded.html')
    return render(request, 'library/addbook.html', {'form': form})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def viewbook_view(request):
    books = models.Book.objects.all()
    return render(request, 'library/viewbook.html', {'books': books})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def issuebook_view(request):
    form = forms.IssuedBookForm()
    if request.method == 'POST':
        
        form = forms.IssuedBookForm(request.POST)
        if form.is_valid():
            obj = models.IssuedBook()
            obj.enrollment = request.POST.get('enrollment2')
            obj.isbn = request.POST.get('isbn2')
            obj.save()
            return render(request, 'library/bookissued.html')
    return render(request, 'library/issuebook.html', {'form': form})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def viewissuedbook_view(request):
    issuedbooks = models.IssuedBook.objects.all()
    li = []

    for ib in issuedbooks:
        issuedate = ib.issuedate
        expirydate = ib.expirydate
        issdate = f'{issuedate.day}-{issuedate.month}-{issuedate.year}'
        expdate = f'{expirydate.day}-{expirydate.month}-{expirydate.year}'
        days = (date.today() - issuedate)
        f = calc_fine(days.days)

        b = list(models.Book.objects.filter(isbn=ib.isbn))
        std = list(models.StudentExtra.objects.filter(enrollment=ib.enrollment))
        li.append((std[0].get_name, std[0].enrollment, b[0].name, b[0].author, issdate, expdate, f))

    return render(request, 'library/viewissuedbook.html', {'li': li})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def viewstudent_view(request):
    students = models.StudentExtra.objects.all()
    return render(request, 'library/viewstudent.html', {'students': students})


@login_required(login_url='studentlogin')
def viewissuedbookbystudent(request):
    student = models.StudentExtra.objects.filter(user_id=request.user.id)
    issuedbook = models.IssuedBook.objects.filter(enrollment=student[0].enrollment)

    li1 = []
    li2 = []
    for ib in issuedbook:
        books = models.Book.objects.filter(isbn=ib.isbn)
        for book in books:
            t = (request.user, student[0].enrollment, student[0].branch, book.name, book.author)
            li1.append(t)
        issuedate = ib.issuedate
        expirydate = ib.expirydate
        issdate = f'{issuedate.day}-{issuedate.month}-{issuedate.year}'
        expdate = f'{expirydate.day}-{expirydate.month}-{expirydate.year}'
        days = (date.today() - ib.issuedate)
        fine = calc_fine(days.days)
        li2.append((issdate, expdate, fine))

    return render(request, 'library/viewissuedbookbystudent.html', {'li1': li1, 'li2': li2})


def calc_fine(d, fine=0):
    if d > 15:
        day = d - 15
        fine = day * 10
    return fine


def aboutus_view(request):
    return render(request, 'library/aboutus.html')


def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name = sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name) + ' || ' + str(email), message, EMAIL_HOST_USER, ['niskzo11d2018@gmail.com'],
                      fail_silently=False)
            return render(request, 'library/contactussuccess.html')
    return render(request, 'library/contactus.html', {'form': sub})



