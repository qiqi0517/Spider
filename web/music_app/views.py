from time import perf_counter

from django.core.paginator import Paginator
from django.db.models import Count
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from . import config, search
from .models import Comment, Singer, Song


# Create your views here.
def song_list(request):
    songs = Song.objects.prefetch_related("singers").order_by("id")
    paginator = Paginator(songs, config.ITEM_PER_PAGE)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    page_numbers = get_page_numbers(page_obj)
    context = {
        "page_obj": page_obj,
        "page_numbers": page_numbers,
        "page_adjusted": str(page_obj.number) != str(page_number),
        "pagination_label": "歌曲列表分页",
        "query_str": "",
    }
    return render(request, "song_list.html", context)


def song_detail(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    comments = song.comments.all().order_by("-time")  # type: ignore
    context = {
        "song": song,
        "comments": comments,
    }
    return render(request, "song_detail.html", context)


def singer_list(request):
    singers = Singer.objects.annotate(song_count=Count("songs")).order_by("-song_count")
    paginator = Paginator(singers, config.ITEM_PER_PAGE)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    page_numbers = get_page_numbers(page_obj)
    context = {
        "page_obj": page_obj,
        "page_numbers": page_numbers,
        "page_adjusted": str(page_obj.number) != str(page_number),
        "pagination_label": "歌手列表分页",
        "query_str": "",
    }
    return render(request, "singer_list.html", context)


def singer_detail(request, singer_id):
    singers = Singer.objects.prefetch_related("songs__singers")
    singer = get_object_or_404(singers, id=singer_id)
    context = {
        "singer": singer,
    }
    return render(request, "singer_detail.html", context)


def search_result(request):
    start_time = perf_counter()
    query = request.GET.get("q", "").strip()
    search_type = request.GET.get("type")
    # Errors
    if not query:
        return HttpResponseBadRequest("搜索关键词不能为空。")
    if len(query) > config.SEARCH_QUERY_MAX_LENGTH:
        return HttpResponseBadRequest(f"搜索关键词不能超过 {config.SEARCH_QUERY_MAX_LENGTH} 个字符。")
    if search_type not in ("song", "singer"):
        return HttpResponseBadRequest("未知的搜索类型。")
    # get result
    if search_type == "song":
        result = search.search_songs(query)
        pagination_label = "歌曲搜索结果分页"
    else:
        result = search.search_singers(query)
        pagination_label = "歌手搜索结果分页"
    # form page
    paginator = Paginator(result, config.ITEM_PER_PAGE)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    page_numbers = get_page_numbers(page_obj)
    # form query_str
    query_params = request.GET.copy()
    query_params["q"] = query
    query_params["type"] = search_type
    query_params.pop("page", None)
    query_str = query_params.urlencode() + "&"
    # return response
    context = {
        "query": query,
        "search_type": search_type,
        "page_obj": page_obj,
        "search_time": config.SEARCH_TIME_PLACEHOLDER,
        "page_numbers": page_numbers,
        "page_adjusted": str(page_obj.number) != str(page_number),
        "pagination_label": pagination_label,
        "query_str": query_str,
    }
    if search_type == "song":
        template_name = "search_result_song.html"
    else:
        template_name = "search_result_singer.html"
    content = render_to_string(template_name, context, request)
    search_time = perf_counter() - start_time
    content = content.replace(config.SEARCH_TIME_PLACEHOLDER, f"{search_time:.4f}")
    return HttpResponse(content)


def delete_comment(request, comment_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    comment = get_object_or_404(Comment, id=comment_id)
    song_id = comment.song.id
    comment.delete()
    return HttpResponseRedirect(reverse("song_detail", args=[song_id]))


def create_comment(request, song_id):
    # song & Errors
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    song = get_object_or_404(Song, id=song_id)
    # text & Errors
    text = request.POST.get("text", "").strip()
    if not text:
        return HttpResponseBadRequest("评论不能为空。")
    if len(text) > config.USER_COMMENT_MAX_LENGTH:
        return HttpResponseBadRequest(f"评论不能超过 {config.USER_COMMENT_MAX_LENGTH} 个字符。")
    # return response
    Comment.objects.create(
        song=song,
        text=text,
        time=timezone.now(),
    )
    return HttpResponseRedirect(reverse("song_detail", args=[song_id]))



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
