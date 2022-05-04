import re
from datetime import date
from random import randint

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.core.mail import send_mail
# from django.core.serializers import json
from django.http import HttpResponseRedirect
from django.shortcuts import render
import simplejson as json

from librarymanagement.settings import EMAIL_HOST_USER
from . import forms, models
from django.contrib.auth.models import User


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
    print(request.POST)
    post = request.POST.copy()  # to make it mutable
    post['enrollment'] = request.POST.get('username')
    request.POST = post
    print(request.POST)
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
        isbn = request.POST.get('isbn')

        if isbn == '0':
            isbn = str(randint(1000000000000, 9999999999999))
            post = request.POST.copy()  # to make it mutable
            post['isbn'] = isbn
            request.POST = post
            print(isbn)

        form = forms.BookForm(request.POST)

        if form.is_valid():
            if models.Book.objects.filter(isbn=isbn):
                return render(request, 'library/addbook.html', {'form': form, 'isbn_error': 'must be unique'})
            elif len(isbn) != 13:
                return render(request, 'library/addbook.html',
                              {'form': form, 'isbn_error': 'should be 13 characters long'})

            form.save()

            return render(request, 'library/bookadded.html')
    return render(request, 'library/addbook.html', {'form': form})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def viewbook_view(request):
    isbn = request.POST.get('isbn')
    if isbn:
        if models.IssuedBook.objects.filter(isbn=isbn):
            models.IssuedBook.objects.get(isbn=isbn).delete()
        if models.RequestedBook.objects.filter(isbn=isbn):
            models.RequestedBook.objects.filter(isbn=isbn).delete()
        models.Book.objects.filter(isbn=isbn)[0].delete()
    books = models.Book.objects.all()
    return render(request, 'library/viewbook.html', {'books': books})


@login_required(login_url='studentlogin')
def viewbookbystudent_view(request):
    removeISBN = request.POST.get('remove')
    if removeISBN:
        print("REMOVE")
        models.RequestedBook.objects.get(isbn=removeISBN, enrollment=request.user.id).delete()

    books = models.Book.objects.all()
    already_requested_books = models.RequestedBook.objects.filter(enrollment=request.user.id)
    issued_books = models.IssuedBook.objects.all()

    print(f'req - {already_requested_books.values()}')
    print(f'issued - {issued_books.values()}')
    requested_books = models.Book.objects.all()
    for requests in already_requested_books:
        books = books.exclude(isbn=requests.isbn)

    requested_books = requested_books.difference(books)

    taken = []
    objects_filter = models.IssuedBook.objects.filter(enrollment=request.user.username)
    print(f'ob{objects_filter}')
    for ib in objects_filter:
        books = books.exclude(isbn=ib.isbn)
        taken.append(models.Book.objects.get(isbn=ib.isbn))

    print(f'taken - {taken}')

    return render(request, 'library/viewbookbystudent.html',
                  {'books': books, 'requestedbooks': requested_books, 'taken': taken})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def issuebook_view(request):
    books = models.Book.objects.all()
    for e in models.IssuedBook.objects.all():
        books = books.exclude(isbn=e.isbn)

    if request.method == 'POST':
        obj = models.IssuedBook()
        obj.isbn = str(request.POST.get('isbn')).split(' | ')[1]
        obj.enrollment = str(request.POST.get('enrollment')).split(' | ')[1]
        obj.save()
        return render(request, 'library/bookissued.html')

    return render(request, 'library/issuebook.html', {'books': books, 'students': models.StudentExtra.objects.all()})


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
        print(std)

        li.append((std[0].get_name, b[0].isbn, b[0].name, b[0].author, issdate, expdate, f))

    return render(request, 'library/viewissuedbook.html', {'li': li})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def viewstudent_view(request):
    r_enrollment = request.POST.get('remove_enrollment')
    if r_enrollment:
        st = models.StudentExtra.objects.filter(enrollment=r_enrollment)[0]
        issued = models.IssuedBook.objects.filter(enrollment=r_enrollment)
        if issued:
            issued.delete()
        requested = models.RequestedBook.objects.filter(enrollment=st.user.id)
        if requested:
            requested.delete()
        stex = models.StudentExtra.objects.filter(enrollment=r_enrollment)[0]
        stex.delete()
        st.delete()
        user = User.objects.filter(username=r_enrollment)
        user.delete()

    students = models.StudentExtra.objects.all()
    return render(request, 'library/viewstudent.html', {'students': students})


@login_required(login_url='studentlogin')
def viewissuedbookbystudent(request):
    student = models.StudentExtra.objects.get(user_id=request.user.id)
    issuedbook = models.IssuedBook.objects.filter(enrollment=student.enrollment)

    li1 = []
    li2 = []
    for ib in issuedbook:
        book = models.Book.objects.get(isbn=ib.isbn)
        t = (request.user, student.enrollment, student.branch, book.name, book.author)
        li1.append(t)
        issuedate = ib.issuedate
        expirydate = ib.expirydate
        issdate = f'{issuedate.day}-{issuedate.month}-{issuedate.year}'
        expdate = f'{expirydate.day}-{expirydate.month}-{expirydate.year}'
        days = (date.today() - ib.issuedate)
        fine = calc_fine(days.days)
        li2.append((issdate, expdate))

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


def remove_book(request):
    print(request.POST.get('bookid'))
    obj = models.IssuedBook.objects.filter(isbn=request.POST.get('bookid'))[0].delete()
    models.IssuedBook.objects.update()
    print(models.IssuedBook.objects.all().values())
    return HttpResponseRedirect('viewissuedbook')


def requestbook(request):
    request_book = models.RequestedBook()
    request_book.isbn = request.POST.get('bookid')
    request_book.enrollment = request.user.id
    request_book.save()
    return HttpResponseRedirect('viewbookbystudent')


def student_request(request):
    buff = models.StudentExtra.objects.all()
    req = models.RequestedBook.objects.all()
    students = models.StudentExtra.objects.all()
    print(req.values())
    for r in req:
        buff = buff.exclude(user_id=r.enrollment)
    students = students.difference(buff)
    return render(request, 'library/viewstudentrequest.html', {'students': students})


def open_std_req(request):
    print(request.POST.get('enrollment'))
    student = models.StudentExtra.objects.get(enrollment=request.POST.get('enrollment')).user
    buff = models.RequestedBook.objects.filter(enrollment=student.id)
    books = models.Book.objects.all()
    print(buff.values())
    requested_books = models.Book.objects.all()
    for r in buff:
        books = books.exclude(isbn=r.isbn)

    requested_books = requested_books.difference(books)
    print(requested_books.values())
    return render(request, 'library/openrequests.html', {'r': requested_books, 'name': student.first_name})
