from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Category, List, Comment, Bid


def index(request):
    activeList = List.objects.all()
    categoryList = Category.objects.all()
    return render(request, "auctions/index.html", {
        "indexlist": activeList,
        "categories": categoryList
    })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


def createList(request):
    if request.method == "GET":
        categoryList = Category.objects.all()
        return render(request, "auctions/create.html", {
            "categories": categoryList
        })
    else:
        title = request.POST["title"]
        description = request.POST["description"]
        imageurl = request.POST["imageurl"]
        price = request.POST["bidPrice"]
        category = request.POST["category"]
        currentUser = request.user
        categoryInfo = Category.objects.get(categoryName=category)
        bid = Bid(bid=float(price), user=currentUser)
        bid.save()
        newList = List(
            title=title,
            description=description,
            imageUrl=imageurl,
            price=bid,
            category=categoryInfo,
            ownUser=currentUser
        )

        newList.save()
        return HttpResponseRedirect(reverse(index))    

def displayCategory(request):
    if request.method == "POST":
        categoryForm = request.POST['category']
        category = Category.objects.get(categoryName=categoryForm)
    activeList = List.objects.filter(category=category)
    categoryList = Category.objects.all()
    return render(request, "auctions/index.html", {
        "indexlist": activeList,
        "categories": categoryList
    })

def listitem(request, id):
    listiteminfo = List.objects.get(pk=id)
    listitemwatchlist = request.user in listiteminfo.watchlist.all()
    allComments = Comment.objects.filter(listitem=listiteminfo)
    isOwner = request.user.username == listiteminfo.ownUser.username
    return render(request, "auctions/listitem.html", {
        "listitem": listiteminfo,
        "listitemwatchlist": listitemwatchlist,
        "isOwner": isOwner,
        "allComments": allComments
    })

def watchlist(request):
    currentUser = request.user
    indexlist = currentUser.listWatchlist.all()
    return render(request, "auctions/watchlist.html",{
        "indexlist": indexlist
    })

def addWatchlist(request, id):
    listiteminfo = List.objects.get(pk=id)
    currentUser = request.user
    listiteminfo.watchlist.add(currentUser)
    return HttpResponseRedirect(reverse("listitem",args=(id, )))

def removeWatchlist(request, id):
    listiteminfo = List.objects.get(pk=id)
    currentUser = request.user
    listiteminfo.watchlist.remove(currentUser)
    return HttpResponseRedirect(reverse("listitem",args=(id, )))

def addComment(request, id):
    currentUser = request.user
    listiteminfo = List.objects.get(pk=id)
    message = request.POST['addComment']

    addComment = Comment(
        author = currentUser,
        listitem=listiteminfo,
        message=message
    )

    addComment.save()

    return HttpResponseRedirect(reverse("listitem",args=(id, )))


def addBid(request, id):
    newBid = request.POST['addBid']
    listiteminfo = List.objects.get(pk=id)
    listitemwatchlist = request.user in listiteminfo.watchlist.all()
    allComments = Comment.objects.filter(listitem=listiteminfo)
    isOwner = request.user.username == listiteminfo.ownUser.username
    if int(newBid) > listiteminfo.price.bid:
        updateBid = Bid(user=request.user, bid=int(newBid))
        updateBid.save()
        listiteminfo.price = updateBid
        listiteminfo.save()
        return render(request, "auctions/listitem.html",{
            "listitem": listiteminfo,
            "bidmessage": "Your auction bid has been successfully registered.",
            "update": True,
            "listitemwatchlist": listitemwatchlist,
            "allComments": allComments,
            "isOwner": isOwner
        })
    else:
        return render(request, "auctions/listitem.html",{
            "listitem": listiteminfo,
            "bidmessage": "No bids were received.",
            "update": False,
            "listitemwatchlist": listitemwatchlist,
            "allComments": allComments,
            "isOwner": isOwner
        })
    

def closeAuction(request, id):
    listiteminfo = List.objects.get(pk=id)
    listiteminfo.activeStatus = False
    listiteminfo.save()
    listitemwatchlist = request.user in listiteminfo.watchlist.all()
    allComments = Comment.objects.filter(listitem=listiteminfo)
    isOwner = request.user.username == listiteminfo.ownUser.username
    return render(request, "auctions/listitem.html", {
        "listitem": listiteminfo,
        "listitemwatchlist": listitemwatchlist,
        "allComments": allComments,
        "isOwner": isOwner,
        "update": True,
        "bidmessage": "Your auction has been closed."
        })