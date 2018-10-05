function notify(level, msg) {
  $(".alert").remove();
  var div = $('<div class="alert alert-' + level + '">' + msg + '</div>');
  $("#page-wrapper").prepend(div);
  div.delay(6000).fadeOut();
}

/* if (document.querySelector("div.panel-primary")) {
  setTimeout(async() => {
    const res = await fetch("/api/stats", { method: "GET" });
    const stats = await res.json();
    const color = {
      messages: "primary",
      guilds: "green",
      users: "yellow",
      channels: "red"
    };
    for (const key in stats) {
      $(`div.panel-${color[key]} .huge`).text(stats[key]);
    }
  }, 1500);
} */