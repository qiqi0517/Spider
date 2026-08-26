const infoCollapse = document.getElementById("infoCollapse");
const infoToggleButtons = document.querySelectorAll(".infoToggleButton");
if (infoCollapse && infoToggleButtons.length > 0) {
    infoCollapse.addEventListener("show.bs.collapse", function () {
        infoToggleButtons.forEach(function (button) {
            button.textContent = "折叠简介";
        });
    });
    infoCollapse.addEventListener("hide.bs.collapse", function () {
        infoToggleButtons.forEach(function (button) {
            button.textContent = "展开简介";
        });
    });
}
