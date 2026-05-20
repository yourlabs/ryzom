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

    // setRoutes();
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

  setRoutes = function() {
    document.addEventListener('click', function(event) {
      if (event.defaultPrevented)
        return;

      var elem = event.target;
      while (elem && !(elem instanceof HTMLAnchorElement))
        elem = elem.parentNode;
      if (!elem)
        return;

      if (elem.origin == window.location.origin)
        event.preventDefault();
        if (elem.href != window.location.href)
          route(elem.pathname, elem.search);
    });
  };

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
        console.log('component is array')
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

    if (component.publication) {
      ryzom.subscribe(component.publication, component.subscription, component.id, function(r, e) {
        if (e) { console.log(e); }
      });
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
      // Note: removed eval(component.script) for CSP compliance
      // Components should use HTMLElement.connectedCallback instead of py2js
    });

    dispatchEvent(new Event('load'));
    //setRoutes();
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
    // Note: removed eval(params.script) for CSP compliance
    // Components should use HTMLElement.connectedCallback instead of py2js
    dispatchEvent(new Event('load'));
  };

  /*
  pushState = function(url, q) {
    path = url;
    if (q && q.length)
      path += '?' + q;
    state = window.location.protocol + '//' +
      window.location.hostname + ':' +
      window.location.port + '/' +
      path;
    if (!history.state || history.state.fullpath != state)
      history.pushState({fullpath: state, path: path}, null, state)
  };

  route = function(url, q, backward=false) {
    if (!('token' in window)) {
      if (q)
        url += '?' + q
      window.location.href = url
      return;
    }
    ws_send({
      type: 'geturl',
      params: {
        url: url,
        query: q
      }
    }, function(r, e) {
      if (e)
        console.log(e);
      else {
        constructDOM(r.params);
        if (initialized && !backward)
          pushState(url, q);
      }
    });
  };

  window.onpopstate = function(event) {
    if (event.state) {
      route(event.state.path, '', true);
      event.preventDefault()
    } else {
      history.back()
    }
  };
  */

  init = function() {
    if (window.onwsready_cb) {
      window.onwsready_cb.forEach(function(cb) {
        cb();
      });
    }
    //pushState(current_url, query_string);
    initialized = true;
  };

  var ws;

  // Read websocket config from meta tag (CSP-compliant, no inline scripts)
  getRyzomConfig = function() {
    var meta = document.querySelector('meta[name="ryzom-config"]');
    if (meta) {
      return {
        token: meta.getAttribute('content'),
        ws_host: meta.getAttribute('data-ws-host'),
        ws_port: meta.getAttribute('data-ws-port')
      };
    }
    // Fallback to window globals for backwards compatibility
    if ('token' in window) {
      return {
        token: window.token,
        ws_host: window.ws_host,
        ws_port: window.ws_port
      };
    }
    return null;
  };

  ws_connect = function(reconnecting) {
    var config = getRyzomConfig();
    if (!config) return;

    var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    var ws_host = config.ws_host ? config.ws_host : window.location.hostname;
    var ws_port = config.ws_port ? config.ws_port : window.location.port;
    var ws_path = ws_scheme + '://' + ws_host + ':' + ws_port + '/ws/ddp/';
    ws_path += '?' + config.token;
    ws = new WebSocket(ws_path);

    if (reconnecting) {
      ws.onopen = function() {
        window.location.reload(true);
      };
    } else {
      ws.onopen = function(e) {
        setInterval(ws_ping, 5000)
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

    ws.onclose = function(e) {
      setTimeout(function() {
        ws_connect();
      }, 1000);
    };

    ws.callbacks = [];
  };

  // Auto-connect if config is available
  if (getRyzomConfig())
    ws_connect();

  ws_send = function(data, cb) {
    var id = ID();
    data.id = id;
    ws.callbacks[id] = cb;
    if (initialized)
      ws.send(JSON.stringify(data));
    else {
      onwsready(function() {
        ws.send(JSON.stringify(data));
      });
    }
  };

  ws_ping = function(cb) {
    ws_send({type: 'ping', params: {}}, function(r, e) {
      if (e) { window.location.reload(true); }
    })
  }

  onwsready = function(cb) {
    if (typeof(window.onwsready_cb) == 'undefined') {
      window.onwsready_cb = []
    }
    window.onwsready_cb.push(cb);
  };

  ryzom = {
    login: function(credentials) {
      ws_send({
        type: 'login',
        params: credentials
      }, function(r, e) {
        if (e)
          console.log(e);
        else
          localStorage.setItem('auth_token', r.params.token)
      });
    },

    logout: function() {
    },

    call: function(name, params) {
      ws_send({
        type: 'method',
        params: {
          name: name,
          params: params
        }
      }, function(r, e) {
        if (e)
          console.log(e);
      });
    },

    subscribe: function(name, id, pid, cb) {
      console.log(pid)
      ws_send({
        type: 'subscribe',
        params: {
          name: name,
          parent_id: pid,
          sub_id: id,
          opts: []
        }
      }, cb);
    }
  };

  setup();
