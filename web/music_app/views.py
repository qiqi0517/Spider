from django.shortcuts import render, get_object_or_404
from django.http import Http404, HttpResponseRedirect
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator
from . import config
from .models import Singer, Song, Comment
from datetime import datetime

# Create your views here.
def song_list(request):
    songs = Song.objects.all().order_by("id")
    paginator = Paginator(songs, config.SONG_PER_PAGE)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    page_numbers = get_page_numbers(page_obj)
    context = {
        "page_obj": page_obj,
        "page_numbers": page_numbers,
        "query_str": "",
    }
    return render(request, "song_list.html", context)


def song_detail(request, id):
    try:
        song = Song.objects.get(id=id)
    except Song.DoesNotExist:
        raise Http404(f"song {id} does not exists")
    comments = song.comments.all().order_by("-time")    # type: ignore
    context = {
        "song": song,
        "comments": comments,
    }
    return render(request, "song_detail.html", context)


def singer_list(request):
    singers = Singer.objects.annotate(song_count=Count("songs")).order_by("-song_count")
    paginator = Paginator(singers, config.SINGER_PER_PAGE)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    page_numbers = get_page_numbers(page_obj)
    context = {
        "page_obj": page_obj,
        "page_numbers": page_numbers,
        "query_str": "",
    }
    return render(request, "singer_list.html", context)


def singer_detail(request, id):
    try:
        singer = Singer.objects.get(id=id)
    except Singer.DoesNotExist:
        raise Http404(f"singer {id} does not exists")
    context = {
        "singer": singer,
    }
    return render(request, "singer_detail.html", context)


def search_result(request):
    query = request.GET.get("q")
    search_type = request.GET.get("type")
    # serching algorithm
    query_str = f"q={query}&type={search_type}&"
    context = None
    return render(request, "search_result.html", context)


def delete_comment(request, id):
    if request.method != "POST":
        raise Http404("wrong method to delete comment")
    try:
        comment = Comment.objects.get(id=id)
    except Comment.DoesNotExist:
        raise Http404(f"comment {id} does not exists")
    song_id = comment.song.id
    comment.delete()
    return HttpResponseRedirect(reverse("song_detail", args=[song_id]))


def create_comment(request, id):
    if request.method != "POST":
        raise Http404("wrong method to create comment")
    try:
        song = Song.objects.get(id=id)
    except Song.DoesNotExist:
        raise Http404(f"comment {id} does not exists")
    text = request.POST.get("text")
    time = timezone.now()
    Comment.objects.create(
        song = song,
        text = text,
        time = time
    )
    return HttpResponseRedirect(reverse("song_detail", args=[id]))



# utils
def get_page_numbers(page_obj):
    current = page_obj.number
    total = page_obj.paginator.num_pages
    if total <= 9:
        return list(range(1, total+1))
    page_numbers = [1, 2]
    if current > 5:
        page_numbers.append("...")  # type: ignore
    start = max(3, current-2)
    end = min(total-2, current+2)
    page_numbers.extend(range(start, end+1))
    if current < total-3:
        page_numbers.append("...")  # type: ignore
    page_numbers.extend([total-1, total])
    return page_numbers