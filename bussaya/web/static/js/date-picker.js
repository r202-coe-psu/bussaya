// Wires text inputs rendered by the `render_date_picker` macro to their cally
// <calendar-date> popover. The input always holds an ISO (%Y-%m-%d) value; the
// calendar is only an alternate way to pick one.
(function () {
  var ISO = /^\d{4}-\d{2}-\d{2}$/;

  function wire(input) {
    var pop = document.getElementById(input.getAttribute('data-date-picker'));
    if (!pop) return;
    var cal = pop.querySelector('calendar-date');
    if (!cal) return;

    // When the popover opens, seed the calendar from the input's current value.
    pop.addEventListener('toggle', function (e) {
      if (e.newState !== 'open') return;
      var v = input.value.trim();
      // setAttribute (not the property) so it survives a not-yet-upgraded element.
      if (ISO.test(v)) {
        cal.setAttribute('value', v);
      } else {
        cal.removeAttribute('value');
      }
    });

    // When a date is picked, write it back to the input and close the popover.
    cal.addEventListener('change', function () {
      if (!cal.value) return;
      input.value = cal.value;
      input.dispatchEvent(new Event('change', { bubbles: true }));
      if (pop.hidePopover) pop.hidePopover();
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('input[data-date-picker]').forEach(wire);
  });
})();
