$(function () {
    $("#search").autocomplete({
        source: function (request, response) {
            $.ajax({
                url: "/search/autocomplete/",
                data: {
                    term: request.term
                },
                dataType: "json",
                success: function (data) {
                    response($.map(data, function (item) {
                        return {
                            label: item.label,
                            value: item.label,
                            url: item.url
                        };
                    }));
                }
            });
        },
        minLength: 2,
        select: function (event, ui) {
            window.location.href = ui.item.url;
        }
    });
});