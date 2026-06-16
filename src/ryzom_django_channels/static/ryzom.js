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
        var target = event.target.closest('[data-ryzom-component]');
        if (!target) return;

        var handlers = target.getAttribute('data-ryzom-handlers');
        var component = target.getAttribute('data-ryzom-component');
        if (!handlers || !component) return;

        var handlerName = 'on' + eventType;
        if (handlers.split(',').indexOf(handlerName) !== -1) {
          var funcName = component + '_' + handlerName;
          if (typeof window[funcName] === 'function') {
            window[funcName](target);
          }
        }
      }, true);
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

  applyDDP = function(data) {
    switch (data.type) {
      case 'insert': constructDOM(data.params); break;
      case 'remove': removeDOM(data.params); break;
      case 'change': changeDOM(data.params); break;
      default: break;
    };
  };

  // A reactive update must never mutate the page while the user has a modal
  // dialog open: the server render is the *closed* dialog, so applying it would
  // close the modal and wipe whatever the user is typing inside it (e.g. a key
  // holder entering their key passphrase). Every DDP handler also re-fires a
  // synthetic 'load', which would re-init the open dialog. So while any dialog
  // is open we queue updates and flush them once it closes.
  ddpQueue = [];
  flushDDP = function() {
    if (document.querySelector('.mdc-dialog--open')) return;
    var q = ddpQueue; ddpQueue = [];
    q.forEach(function(d) { applyDDP(d); });
  };
  handleDDP = function(data) {
    if (document.querySelector('.mdc-dialog--open')) {
      ddpQueue.push(data);
      return;
    }
    applyDDP(data);
  };

  constructDOM = function(data) {
    if (!Array.isArray(data)) {
      data = [data]
    }

    data.forEach(function(component) {
      // Dedupe: if a node with this ryzom-id is already in the document
      // (an insert raced a previous insert/reconnect replay), patch it in
      // place instead of inserting a duplicate sibling.
      var existing = getElementByUuid(component.id);
      if (existing && document.contains(existing)) {
        changeDOM(component);
        return;
      }
      var elem = createDOMelement(component);
      var parent = getElementByUuid(component.parent)
      if (!parent) return;
      var prev = parent.children[component.position]
      parent.insertBefore(elem, prev);
    });

    dispatchEvent(new Event('load'));
  };

  removeDOM = function(params) {
    var parentNode = getElementByUuid(params.parent);
    var node = getElementByUuid(params.id);
    // Already gone (double remove, or removed with a containing subtree):
    // nothing to do — don't throw and break the rest of the message batch.
    if (!node || !node.parentNode) return;
    parentNode = node.parentNode;
    // animate on delete
    if (node.dataset && node.dataset.ryzomAod) {
      node.style.animation = node.dataset.ryzomAod;
      node.addEventListener('animationend', function() {
	parentNode.removeChild(node);
      });
    } else {
        parentNode.removeChild(node);
    }
    dispatchEvent(new Event('load'));
  };

  patchAttrs = function(elem, newAttrs) {
    // Remove attributes not present in newAttrs
    var toRemove = [];
    for (var i = 0; i < elem.attributes.length; i++) {
      var name = elem.attributes[i].name;
      if (name === 'ryzom-id') continue;
      if (!(name in newAttrs) && name !== 'style') {
        toRemove.push(name);
      }
    }
    toRemove.forEach(function(name) { elem.removeAttribute(name); });

    // Set/update attributes
    Object.keys(newAttrs).forEach(function(k) {
      var val = newAttrs[k];
      if (k === 'style') {
        elem.style.cssText = '';
        Object.keys(val).forEach(function(sk) {
          elem.style[sk] = val[sk];
        });
      } else {
        if (elem.getAttribute(k) !== String(val)) {
          elem.setAttribute(k, val);
        }
      }
    });
  };

  patchChildren = function(parentElem, newContent) {
    if (typeof newContent === 'string') {
      if (parentElem.textContent !== newContent) {
        parentElem.textContent = newContent;
      }
      return;
    }

    var oldChildren = Array.prototype.slice.call(parentElem.childNodes);
    var newLen = newContent.length;
    var oldLen = oldChildren.length;
    var minLen = Math.min(oldLen, newLen);

    // Patch existing children in place
    for (var i = 0; i < minLen; i++) {
      var newChild = newContent[i];
      var oldChild = oldChildren[i];

      if (newChild.tag === 'text' || typeof newChild === 'string') {
        // New child is text
        var text = typeof newChild === 'string'
          ? newChild
          : decodeHtml(newChild.content);
        if (oldChild.nodeType === 3) {
          if (oldChild.textContent !== text) {
            oldChild.textContent = text;
          }
        } else {
          var textNode = document.createTextNode(text);
          parentElem.replaceChild(textNode, oldChild);
        }
        if (typeof newChild !== 'string') {
          registerComponent(newChild, parentElem.childNodes[i]);
        }
      } else if (
        oldChild.nodeType === 1 &&
        oldChild.tagName.toLowerCase() === newChild.tag
      ) {
        // Same element tag: patch in place
        patchAttrs(oldChild, newChild.attrs || {});
        patchChildren(oldChild, newChild.content || []);
        registerComponent(newChild, oldChild);
      } else {
        // Tag mismatch: full replacement
        var replacement = createDOMelement(newChild);
        parentElem.replaceChild(replacement, oldChild);
      }
    }

    // Append new children
    for (var j = oldLen; j < newLen; j++) {
      parentElem.appendChild(createDOMelement(newContent[j]));
    }

    // Remove excess old children
    while (parentElem.childNodes.length > newLen) {
      parentElem.removeChild(parentElem.childNodes[newLen]);
    }
  };

  changeDOM = function(params) {
    var prev_node = getElementByUuid(params.id);
    var parent = getElementByUuid(params.parent);

    // Fall back to full replacement if node missing or tag changed
    if (!prev_node || prev_node.nodeType !== 1 ||
        prev_node.tagName.toLowerCase() !== params.tag) {
      if (prev_node && prev_node.parentNode) parent = prev_node.parentNode;
      if (!parent) return;
      var cur_node = createDOMelement(params);
      if (prev_node) {
        parent.insertBefore(cur_node, prev_node);
        parent.removeChild(prev_node);
      } else {
        var ref = parent.children[params.position];
        parent.insertBefore(cur_node, ref);
      }
      dispatchEvent(new Event('load'));
      return;
    }

    // Differential update: patch attrs and children in place
    patchAttrs(prev_node, params.attrs || {});
    patchChildren(prev_node, params.content || []);
    registerComponent(params, prev_node);
    dispatchEvent(new Event('load'));
  };

  var dialogListenerInstalled = false;
  init = function() {
    if (window.onwsready_cb) {
      // One-shot: drain the queue so callbacks (queued sends, mostly) don't
      // re-fire on every reconnect's 'Connected' message.
      var cbs = window.onwsready_cb;
      window.onwsready_cb = [];
      cbs.forEach(function(cb) {
        cb();
      });
    }
    // When a modal dialog closes, apply any reactive updates we deferred while
    // it was open (MDCDialog:closed bubbles to document). Install once —
    // init() runs again on every reconnect.
    if (!dialogListenerInstalled) {
      dialogListenerInstalled = true;
      document.addEventListener('MDCDialog:closed', function() { flushDDP(); });
    }
    initialized = true;
  };

  var ws;
  // Track active transport: 'ws' or 'poll'
  var activeTransport = null;
  // Track if we already fell back to prevent WS onclose from retrying
  var fellBackToPoll = false;
  // WS opened successfully at least once this session. Once true we KNOW the
  // network allows WebSockets, so any later failure is a transient outage:
  // we keep retrying WS forever and never degrade to polling. Polling is thus
  // reserved for clients whose network actually blocks WebSockets.
  var wsEverConnected = false;
  // Consecutive failed connection attempts before the first success. We retry
  // a few times before concluding WS is blocked, so a transient first-attempt
  // hiccup doesn't strand the client on polling.
  var wsInitialFailures = 0;
  var WS_MAX_INITIAL_FAILURES = 3;
  // Per-attempt open timeout (ms) and delay between (re)connect attempts.
  var WS_CONNECT_TIMEOUT = 8000;
  var WS_RETRY_DELAY = 1000;
  var pingInterval = null;
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

  ws_connect = function() {
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
    var settled = false; // handle this attempt's open/failure exactly once

    // A connection that fails to OPEN within the timeout is a failed attempt
    // (slow or silently-blocked handshake). An already-open socket that later
    // drops is handled by onclose, not here.
    var connectTimeout = setTimeout(function() {
      if (!wsConnected) onAttemptFail();
    }, WS_CONNECT_TIMEOUT);

    // Decide what to do after a connection attempt fails to open.
    function onAttemptFail() {
      if (settled) return;
      settled = true;
      clearTimeout(connectTimeout);
      try {
        ws.onopen = ws.onmessage = ws.onerror = ws.onclose = null;
        ws.close();
      } catch (e) {}

      if (wsEverConnected || config.transport === 'ws') {
        // WS has worked before (or is forced): the network allows it, so this
        // is a transient outage. Keep retrying WS; never degrade to polling.
        setTimeout(ws_connect, WS_RETRY_DELAY);
        return;
      }

      // Never connected yet: retry a few times before giving up on WS.
      wsInitialFailures += 1;
      if (wsInitialFailures < WS_MAX_INITIAL_FAILURES) {
        setTimeout(ws_connect, WS_RETRY_DELAY);
        return;
      }

      // WS could not be established after several attempts -> the network
      // blocks WebSockets. This is the ONLY path to polling.
      notify_transport_switch(config);
      poll_connect();
    }

    ws.onopen = function(e) {
      // Ignore a late open that races a timeout/error already handled by
      // onAttemptFail(): otherwise a failed attempt would be mistaken for a
      // success and a truly-blocked client would never fall back to poll.
      if (settled) return;
      wsConnected = true;
      wsEverConnected = true;
      wsInitialFailures = 0;
      settled = true;
      clearTimeout(connectTimeout);
      // Reset any ping loop from a prior connection before starting a new one.
      if (pingInterval) clearInterval(pingInterval);
      pingInterval = setInterval(ws_ping, 5000);
    };

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

          // The callback may be gone (registered on a previous socket that
          // dropped before the reply arrived) — don't throw.
          if (ws.callbacks && typeof ws.callbacks[data.id] === 'function') {
            ws.callbacks[data.id](result, error);
            delete ws.callbacks[data.id]
          }
      };
    };

    ws.onerror = function(e) {
      // Only a pre-open error is a failed attempt; a post-open error is
      // followed by onclose, which drives reconnection.
      if (!wsConnected) onAttemptFail();
    };

    ws.onclose = function(e) {
      if (fellBackToPoll) return;
      if (wsConnected) {
        // An established connection dropped (blip / server restart): reconnect
        // over WS. The server replies 'Connected' (seamless) or 'Reload'.
        setTimeout(ws_connect, WS_RETRY_DELAY);
      } else {
        // Closed before opening (e.g. handshake refused): a failed attempt.
        onAttemptFail();
      }
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
      if (initialized && ws && ws.readyState === WebSocket.OPEN) {
        ws.callbacks[id] = cb;
        ws.send(JSON.stringify(data));
      } else {
        // Socket not (yet) open — first connect or a reconnect in flight.
        // Sending now would throw InvalidStateError (the ping interval keeps
        // firing while closed). Drop pings (the next interval tick retries);
        // queue anything else for the next 'Connected'.
        if (data.type === 'ping') return;
        onwsready(function() {
          ws.callbacks[id] = cb;
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
