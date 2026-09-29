// Automatically initializes TomSelect for multiselect fields and tag fields.
(function () {
  function initTomSelect(el) {
    if (el.tomSelect || el.getAttribute('data-tomselect-initialized')) return;

    var mode = el.getAttribute('data-tomselect') || (el.tagName === 'SELECT' && el.multiple ? 'multiple' : 'tags');
    var isTags = mode === 'tags' || el.tagName === 'INPUT';

    var options = {
      controlClass: 'ts-control',
      plugins: ['remove_button'],
      persist: false,
      createOnBlur: isTags,
      create: isTags,
      delimiter: isTags ? ',' : undefined,
      maxOptions: null,
      hideSelected: true,
      copyClassesToDropdown: false,
      placeholder: isTags ? 'Type tags separated by comma...' : 'Select options...',
    };

    try {
      var ts = new TomSelect(el, options);
      el.setAttribute('data-tomselect-initialized', 'true');
      if (mode === 'single') {
        // Drop the previously selected item as soon as the user starts
        // typing, so searching always starts from a blank slate instead of
        // looking like it's being appended to the old selection.
        ts.on('type', function (str) {
          if (str && ts.items.length) {
            ts.clear(true);
          }
        });
      }
      if (ts.control) {
        ts.control.classList.remove('input', 'select', 'border', 'border-base-300', 'w-full');
      }
      if (ts.wrapper) {
        ts.wrapper.classList.remove('input', 'select', 'border', 'border-base-300');
      }
      if (ts.control_input) {
        ts.control_input.classList.remove('input', 'select', 'border', 'border-base-300', 'w-full');
      }
    } catch (e) {
      console.error('TomSelect initialization failed for element:', el, e);
    }
  }

  function initAll() {
    if (typeof TomSelect === 'undefined') return;
    document.querySelectorAll('select[multiple], [data-tomselect]').forEach(initTomSelect);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }
})();
