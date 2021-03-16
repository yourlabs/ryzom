  initialized = false;

  $ = function(q) {
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

    // setRoutes();
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
      return $('[ryzom-id="'+uuid+'"]');
    }
  };

  createDOMelement = function(component) {
    var elem;
    if (component.tag == 'text')
      elem = document.createTextNode(component.content);
    else if (typeof(component) == 'string')
      elem = document.createTextNode(component);
    else {
      elem = document.createElement(component.tag);
      Object.keys(component.attrs).forEach(function(k) {
        elem.setAttribute(k, component.attrs[k]);
      });
    }

    if (component.publication) {
      ryzom.subscribe(component.publication, component.subscription, component.id, function(r, e) {
        if (e) { console.log(e); }
      });
    };

    if (component.content && typeof(component.content) != 'string' && component.content.length) {
      component.content.forEach(function(child) {
        var c = createDOMelement(child);
        var prev = elem.childNodes[c.position]
        elem.insertBefore(c, prev);
        eval(child.script);
      });
    };

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
      var prev = parent.childNodes[component.position]
      parent.insertBefore(elem, prev);
      eval(component.script);
    });

    //setRoutes();
  };

  removeDOM = function(params) {
    var parentNode = getElementByUuid(params.parent);
    var node = getElementByUuid(params.id);
    parentNode.removeChild(node);
  };

  changeDOM = function(params) {
    var prev_node = getElementByUuid(params.id);
    var cur_node = createDOMelement(params);
    var parent = getElementByUuid(params.parent);
    parent.removeChild(prev_node);
    prev_node = parent.childNodes[params.position]
    parent.insertBefore(cur_node, prev_node)
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

  ws_connect = function(reconnecting) {
    ws_path = 'ws://' + window.location.host + '/ws/ddp/'
    ws_path += '?' + token
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

  if ('token' in window)
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
