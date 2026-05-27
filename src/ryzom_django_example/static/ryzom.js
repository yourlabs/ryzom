// Event delegation for data-ryzom-handlers attributes.
// This is the only part of ryzom.js needed by the simple.py example app.
// It wires onclick/onmouseover/etc. methods (transpiled by py2js into bundle.js)
// to their DOM elements via data-ryzom-component / data-ryzom-handlers attributes.
// The full WebSocket/DDP runtime lives in ryzom_django_channels/static/ryzom.js.

setup = function() {
  setupEventDelegation();
}

setupEventDelegation = function() {
  var events = ['click', 'mouseover', 'submit', 'change', 'input'];
  events.forEach(function(eventType) {
    document.addEventListener(eventType, function(event) {
      var target = event.target;
      while (target && target !== document) {
        var handlers = target.getAttribute('data-ryzom-handlers');
        var component = target.getAttribute('data-ryzom-component');
        if (handlers && component) {
          var handlerName = 'on' + eventType;
          if (handlers.split(',').indexOf(handlerName) !== -1) {
            var func = window[component + '_' + handlerName];
            if (typeof func === 'function') func.call(target, event);
          }
        }
        target = target.parentElement;
      }
    }, true);
  });
}

setup();
