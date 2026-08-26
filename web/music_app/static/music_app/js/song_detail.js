const lyricsCollapse = document.getElementById("lyricsCollapse");
const lyricsToggleButtons = document.querySelectorAll(".lyricsToggleButton");
if (lyricsCollapse && lyricsToggleButtons.length > 0) {
    lyricsCollapse.addEventListener("show.bs.collapse", function () {
        lyricsToggleButtons.forEach(function (button) {
            button.textContent = "折叠歌词";
        });
    });
    lyricsCollapse.addEventListener("hide.bs.collapse", function () {
        lyricsToggleButtons.forEach(function (button) {
            button.textContent = "展开歌词";
        });
    });
}

const commentInput = document.getElementById("commentInput");
if (commentInput) {
    commentInput.addEventListener("input", function () {
        this.style.height = "auto";
        this.style.height = this.scrollHeight + "px";
    });
}

history.scrollRestoration = "manual";
document.querySelectorAll(".comment-action-form").forEach(function (form) {
    form.addEventListener("submit", function () {
        sessionStorage.setItem("commentScrollPosition", window.scrollY);
    });
});
window.addEventListener("load", function () {
    const commentScrollPosition = sessionStorage.getItem("commentScrollPosition");
    if (commentScrollPosition != null) {
        window.scrollTo(0, Number(commentScrollPosition));
        sessionStorage.removeItem("commentScrollPosition");
    }
});
