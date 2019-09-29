$(function() {
  var availableTags = [];
  $(".station-link").each(function(index, obj) {
    availableTags.push($(this).text());
  });
  var set = new Set(availableTags);

  availableTags = [...set];
  $("#search-box").autocomplete({
    source: availableTags,
    select: function( event, ui ) {
      window.location = $("a").filter(function() {
        return $(this).text() === ui.item.label;
    }).attr('href');
  }
  });


    $("h3:contains('Stony')").css("background-color", "grey");
  
});
