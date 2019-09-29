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
      console.log(ui.item.label)
      window.location = $("a:contains("+ui.item.label+")").attr('href');
  }
  });


    $("h3:contains('Stony')").css("background-color", "grey");
  
});
