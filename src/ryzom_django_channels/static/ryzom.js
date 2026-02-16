  initialized = false;

  _$ = function(q) {
    return document.querySelector(q);
  };

  ID = function(){
    function chr4(){
      return Math.random().toString(16).slice(-4);
    }
    return chr4() + chr4() +
      '-' + chr4() +
      '-' + chr4() +
      '-' + chr4() +
      '-' + chr4() + chr4() + chr4();
  }

  setup = function() {
    window.components = [];
    window.components['html'] = document.getElementsByTagName('html')[0];
    window.components['head'] = document.getElementsByTagName('head')[0];
    window.components['body'] = document.getElementsByTagName('body')[0];

    // Setup event delegation for CSP-compliant event handling
    setupEventDelegation();
  }

  // Event delegation for data-ryzom-handlers attributes
  // This replaces inline event handlers for CSP compliance
  setupEventDelegation = function() {
    var events = ['click', 'mouseover', 'submit', 'change', 'input'];

    events.forEach(function(eventType) {
      document.addEventListener(eventType, function(event) {
        // Find the closest element with ryzom handlers
        var target = event.target;
        while (target && target !== document) {
          var handlers = target.getAttribute('data-ryzom-handlers');
          var component = target.getAttribute('data-ryzom-component');

          if (handlers && component) {
            var handlerList = handlers.split(',');
            var handlerName = 'on' + eventType;

            if (handlerList.indexOf(handlerName) !== -1) {
              // Call the bundled function: ComponentName_oneventtype(target)
              var funcName = component + '_' + handlerName;
              if (typeof window[funcName] === 'function') {
                window[funcName](target);
              }
            }
          }
          target = target.parentElement;
        }
      }, true); // Use capture phase to handle events before they bubble
    });
  }

  registerComponent = function(component, DOMelem) {
    window.components[component.id] = DOMelem;
  };

  getElementByUuid = function(uuid) {
    var elem = window.components[uuid];
    if (elem != undefined )
      return elem
    else {
      return _$('[ryzom-id="'+uuid+'"]');
    }
  };

  decodeHtml = function(html) {
    var txt = document.createElement('textarea');
    txt.innerHTML = html
    return txt.value
  }

  createDOMelement = function(component) {
    var elem;
    if (component.tag == 'text')
      elem = document.createTextNode(decodeHtml(component.content));
    else if (typeof(component) == 'string')
      elem = document.createTextNode(component);
    else {
      if (Array.isArray(component)) {
        elem = document.createElement('p');
        component = {content: component};
      } else {
        elem = document.createElement(component.tag);
      }

      // Create and append all children FIRST, before setting attributes
      // This ensures children are available when connectedCallback fires
      if (component.content && typeof(component.content) != 'string' && component.content.length) {
        component.content.forEach(function(child) {
          var c = createDOMelement(child);
          var prev = elem.children[c.position]
          elem.insertBefore(c, prev);
        });
      }

      // Set attributes after children are in place
      if (component.attrs) {
        Object.keys(component.attrs).forEach(function(k) {
          val = component.attrs[k];
          if (k == 'style') {
            Object.keys(val).forEach(function(sk) {
              elem.style[sk] = val[sk];
            });
          } else {
            elem.setAttribute(k, val);
          }
        });
      }
    }

    registerComponent(component, elem)

    return elem;
  };

  handleDDP = function(data) {
    switch (data.type) {
      case 'insert': constructDOM(data.params); break;
      case 'remove': removeDOM(data.params); break;
      case 'change': changeDOM(data.params); break;
      default: break;
    };
  };

  constructDOM = function(data) {
    if (!Array.isArray(data)) {
      data = [data]
    }

    data.forEach(function(component) {
      var elem = createDOMelement(component);
      var parent = getElementByUuid(component.parent)
      var prev = parent.children[component.position]
      parent.insertBefore(elem, prev);
    });

    dispatchEvent(new Event('load'));
  };

  removeDOM = function(params) {
    var parentNode = getElementByUuid(params.parent);
    var node = getElementByUuid(params.id);
    // animate on delete
    if (node.dataset.ryzomAod) {
      node.style.animation = node.dataset.ryzomAod;
      node.addEventListener('animationend', function() {
	parentNode.removeChild(node);
      });
    } else {
        parentNode.removeChild(node);
    }
    dispatchEvent(new Event('load'));
  };

  changeDOM = function(params) {
    var prev_node = getElementByUuid(params.id);
    var cur_node = createDOMelement(params);
    var parent = getElementByUuid(params.parent);
    parent.insertBefore(cur_node, prev_node)
    parent.removeChild(prev_node);
    dispatchEvent(new Event('load'));
  };

  init = function() {
    if (window.onwsready_cb) {
      window.onwsready_cb.forEach(function(cb) {
        cb();
      });
    }
    initialized = true;
  };

  var ws;
  // Track active transport: 'ws' or 'poll'
  var activeTransport = null;
  // Track if we already fell back to prevent WS onclose from retrying
  var fellBackToPoll = false;
  // Polling state
  var pollTimer = null;
  var pollInterval = 500;
  var pollIntervalMin = 500;
  var pollIntervalMax = 5000;
  var pollIntervalStep = 500;

  // Read config from meta tag (CSP-compliant)
  getRyzomConfig = function() {
    var meta = document.querySelector('meta[name="ryzom-config"]');
    if (!meta) return null;
    return {
      token: meta.getAttribute('content'),
      ws_host: meta.getAttribute('data-ws-host'),
      ws_port: meta.getAttribute('data-ws-port'),
      transport: meta.getAttribute('data-transport') || 'auto',
      poll_url: meta.getAttribute('data-poll-url') || '/ddp/'
    };
  };

  // Main entry point: choose transport based on config
  ryzom_connect = function() {
    var config = getRyzomConfig();
    if (!config) return;

    if (config.transport === 'poll') {
      poll_connect();
    } else if (config.transport === 'ws') {
      ws_connect();
    } else {
      // 'auto': try WS first, fall back to poll on failure
      ws_connect();
    }
  };

  ws_connect = function(reconnecting) {
    var config = getRyzomConfig();
    if (!config) return;

    // If we already fell back to poll, don't try WS again
    if (fellBackToPoll) return;

    var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    var ws_host = config.ws_host ? config.ws_host : window.location.hostname;
    var ws_port = config.ws_port ? config.ws_port : window.location.port;
    var ws_path = ws_scheme + '://' + ws_host + ':' + ws_port + '/ws/ddp/';
    ws_path += '?' + config.token;
    ws = new WebSocket(ws_path);
    activeTransport = 'ws';

    var wsConnected = false;

    // 5s connection timeout: fall back to poll if WS doesn't connect
    var connectTimeout = setTimeout(function() {
      if (!wsConnected) {
        ws.onclose = function() {}; // prevent retry
        ws.onerror = function() {};
        ws.close();
        notify_transport_switch(config);
        poll_connect();
      }
    }, 5000);

    if (reconnecting) {
      ws.onopen = function() {
        wsConnected = true;
        clearTimeout(connectTimeout);
        window.location.reload(true);
      };
    } else {
      ws.onopen = function(e) {
        wsConnected = true;
        clearTimeout(connectTimeout);
        setInterval(ws_ping, 5000);
      }
    }

    ws.onmessage = function(e) {
      var data = JSON.parse(e.data);
      var result, error;
      switch (data.type) {
        case 'Reload': document.location.reload(); break;
        case 'Connected': init(); break;
        case 'DDP': handleDDP(data.params); break;
        default:
          if (data.type == 'Error')
            error = data;
          else if (data.type == 'Success')
            result = data;

          ws.callbacks[data.id](result, error);
          delete ws.callbacks[data.id]
      };
    };

    ws.onerror = function(e) {
      if (!wsConnected && config.transport !== 'ws') {
        // WS failed before connecting and we're in auto mode: fall back
        clearTimeout(connectTimeout);
        ws.onclose = function() {}; // prevent retry
        notify_transport_switch(config);
        poll_connect();
      }
    };

    ws.onclose = function(e) {
      if (fellBackToPoll) return;
      setTimeout(function() {
        ws_connect();
      }, 1000);
    };

    ws.callbacks = [];
  };

  // Notify the server that this client is switching to poll transport
  notify_transport_switch = function(config) {
    fellBackToPoll = true;
    activeTransport = 'poll';
    var url = config.poll_url + 'switch/';
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Ryzom-Token': config.token
      },
      body: '{}'
    }).catch(function() {});
  };

  // Start HTTP polling transport
  poll_connect = function() {
    activeTransport = 'poll';
    fellBackToPoll = true;
    // Initialize immediately (fire onwsready callbacks etc.)
    init();
    // Start the polling loop
    poll_loop();
  };

  poll_loop = function() {
    poll_receive(function() {
      pollTimer = setTimeout(poll_loop, pollInterval);
    });
  };

  // Fetch pending messages from the server
  poll_receive = function(done) {
    var config = getRyzomConfig();
    if (!config) { if (done) done(); return; }

    var url = config.poll_url + 'poll/';
    fetch(url, {
      method: 'GET',
      headers: {
        'X-Ryzom-Token': config.token
      }
    }).then(function(resp) {
      return resp.json();
    }).then(function(data) {
      if (data.messages && data.messages.length > 0) {
        // Got messages: process them and speed up polling
        pollInterval = pollIntervalMin;
        data.messages.forEach(function(msg) {
          if (msg.type === 'DDP') {
            handleDDP(msg.params);
          } else if (msg.type === 'Reload') {
            document.location.reload();
          }
        });
      } else {
        // No messages: slow down polling (adaptive)
        if (pollInterval < pollIntervalMax) {
          pollInterval += pollIntervalStep;
        }
      }
      if (done) done();
    }).catch(function() {
      // On error, slow down
      if (pollInterval < pollIntervalMax) {
        pollInterval += pollIntervalStep;
      }
      if (done) done();
    });
  };

  // Send a DDP command via HTTP POST
  poll_send = function(data, cb) {
    var config = getRyzomConfig();
    if (!config) return;

    var url = config.poll_url + 'send/';
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Ryzom-Token': config.token
      },
      body: JSON.stringify(data)
    }).then(function(resp) {
      return resp.json();
    }).then(function(result) {
      var r = null, e = null;
      if (result.type === 'Error') {
        e = result;
      } else {
        r = result;
      }
      if (cb) cb(r, e);
      // Trigger an immediate poll to pick up any server-side changes
      if (pollTimer) {
        clearTimeout(pollTimer);
      }
      pollInterval = pollIntervalMin;
      poll_loop();
    }).catch(function(err) {
      if (cb) cb(null, {type: 'Error', params: {name: 'Network error', message: String(err)}});
    });
  };

  // Unified send: dispatch to WS or poll based on active transport
  ryzom_send = function(data, cb) {
    var id = ID();
    data.id = id;
    if (activeTransport === 'poll') {
      poll_send(data, cb);
    } else {
      ws.callbacks[id] = cb;
      if (initialized)
        ws.send(JSON.stringify(data));
      else {
        onwsready(function() {
          ws.send(JSON.stringify(data));
        });
      }
    }
  };

  // Auto-connect if config is available
  if (getRyzomConfig())
    ryzom_connect();

  // Keep ws_send as alias for backwards compatibility
  ws_send = ryzom_send;

  ws_ping = function(cb) {
    ryzom_send({type: 'ping', params: {}}, function(r, e) {
      if (e) { window.location.reload(true); }
    })
  }

  onwsready = function(cb) {
    if (typeof(window.onwsready_cb) == 'undefined') {
      window.onwsready_cb = []
    }
    window.onwsready_cb.push(cb);
  };

  ryzom = {};

  setup();
