$(document).ready(() => {
    $("span.spoilerText-3p6IlD").click(function() {
        $(this).toggleClass("hidden-HHr2R9");
    });
    
    $(".button-3Jq0g9").click(() => {
        $(".backdrop-1wrmKB").show();
        $(".modal-1UGdnR").css("opacity", 1);
        $(".button-38aScr, .backdrop-1wrmKB").click(function() {
            $(".backdrop-1wrmKB").hide();
            $(".modal-1UGdnR").css("opacity", 0);
            return false;
        });
    });
});