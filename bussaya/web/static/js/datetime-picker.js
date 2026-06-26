// Wires text inputs rendered by the `render_datetime_picker` macro to their cally
// <calendar-date> + <input type="time"> popover. The input always holds an ISO
// "%Y-%m-%d %H:%M" value; the popover is only an alternate way to pick one.
(function () {
  var DT = /^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})/;

  function wire(input) {
    var pop = document.getElementById(input.getAttribute('data-datetime-picker'));
    if (!pop) return;
    var cal = pop.querySelector('calendar-date');
    var time = pop.querySelector('input[data-time]');
    if (!cal || !time) return;

    function compose() {
      var d = cal.value;   // YYYY-MM-DD
      if (!d) return;
      var t = time.value || '00:00';  // HH:MM (24h, locale-independent)
      input.value = d + ' ' + t;
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }

    // When the popover opens, seed the calendar + time from the input's value.
    pop.addEventListener('toggle', function (e) {
      if (e.newState !== 'open') return;
      var m = DT.exec(input.value.trim());
      if (m) {
        cal.setAttribute('value', m[1]);  // setAttribute survives not-yet-upgraded element
        time.value = m[2];
      } else {
        cal.removeAttribute('value');
      }
    });

    cal.addEventListener('change', compose);
    time.addEventListener('change', compose);
    time.addEventListener('input', compose);
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('input[data-datetime-picker]').forEach(wire);
  });
})();
