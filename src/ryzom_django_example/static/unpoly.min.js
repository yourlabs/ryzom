/******/ (() => { // webpackBootstrap
/******/ 	var __webpack_modules__ = ([
/* 0 */,
/* 1 */
/***/ (() => {

window.up = {
    version: '3.14.3'
};


/***/ }),
/* 2 */
/***/ (() => {

up.mockable = function (originalFn) {
    if (window.jasmine) {
        let name = originalFn.name;
        let obj = { [name]: originalFn };
        let mockableFn = function () {
            return obj[name].apply(this, arguments);
        };
        mockableFn.mock = () => spyOn(obj, name);
        return mockableFn;
    }
    else {
        return originalFn;
    }
};


/***/ }),
/* 3 */
/***/ (() => {

up.util = (function () {
    function noop() {
    }
    function asyncNoop() {
        return Promise.resolve();
    }
    function memoize(func, cacheProp) {
        let cache = {};
        return function (...args) {
            if (cacheProp)
                cache = (this[cacheProp] ||= {});
            if (cache.value)
                return cache.value[0];
            if (cache.error)
                throw cache.error;
            try {
                return (cache.value = [func.apply(this, args)])[0];
            }
            catch (error) {
                throw (cache.error = error);
            }
        };
    }
    function normalizeURL(url, options) {
        options = newOptions(options, { host: 'cross-domain' });
        const parts = parseURL(url);
        let normalized = '';
        if (options.host === 'cross-domain') {
            options.host = isCrossOrigin(parts);
        }
        if (options.host) {
            normalized += parts.protocol + "//" + parts.host;
        }
        let { pathname } = parts;
        if (options.trailingSlash === false && pathname !== '/') {
            pathname = pathname.replace(/\/$/, '');
        }
        normalized += pathname;
        if (options.search !== false) {
            normalized += parts.search;
        }
        if (options.hash !== false) {
            normalized += parts.hash;
        }
        return normalized;
    }
    function matchURLs(leftURL, rightURL, options) {
        return matchableURL(leftURL, options) === matchableURL(rightURL, options);
    }
    function matchableURL(url, options) {
        if (!url)
            return;
        return normalizeURL(url, { hash: false, trailingSlash: false, ...options });
    }
    function matchableURLPatternAtom(patternAtom) {
        if (patternAtom.endsWith('/'))
            return [patternAtom, patternAtom.slice(0, -1)];
        if (patternAtom.includes('/?'))
            return [patternAtom, patternAtom.replace('/?', '?')];
        if (patternAtom.endsWith('/*'))
            return [patternAtom, patternAtom.slice(0, -2), patternAtom.slice(0, -2) + '?*'];
        return patternAtom;
    }
    const APP_PROTOCOL = location.protocol;
    const APP_HOSTNAME = location.hostname;
    function isCrossOrigin(urlOrAnchor) {
        if (isString(urlOrAnchor) && (urlOrAnchor.indexOf('//') === -1)) {
            return false;
        }
        const parts = parseURL(urlOrAnchor);
        return (APP_HOSTNAME !== parts.hostname) || (APP_PROTOCOL !== parts.protocol);
    }
    function parseURL(url) {
        if (url.pathname) {
            return url;
        }
        let link = document.createElement('a');
        link.href = url;
        return link;
    }
    function normalizeMethod(method) {
        return method ? method.toUpperCase() : 'GET';
    }
    function methodAllowsPayload(method) {
        return (method !== 'GET') && (method !== 'HEAD');
    }
    function iteratee(block) {
        if (isString(block)) {
            return (item) => item[block];
        }
        else {
            return block;
        }
    }
    function map(list, block) {
        if (list.length === 0) {
            return [];
        }
        block = iteratee(block);
        let mapped = [];
        let i = 0;
        for (let item of list) {
            mapped.push(block(item, i++));
        }
        return mapped;
    }
    function mapObject(array, pairer) {
        return Object.fromEntries(array.map(pairer));
    }
    function each(array, block) {
        let i = 0;
        for (let item of array) {
            block(item, i++);
        }
    }
    function isNull(value) {
        return value === null;
    }
    function isTruthy(value) {
        return !!value;
    }
    function isUndefined(value) {
        return value === undefined;
    }
    const isDefined = negate(isUndefined);
    function isMissing(value) {
        return isUndefined(value) || isNull(value);
    }
    const isGiven = negate(isMissing);
    function isBlank(value) {
        if (isMissing(value)) {
            return true;
        }
        if (isObject(value) && value[isBlank.key]) {
            return value[isBlank.key]();
        }
        if (isString(value) || isList(value)) {
            return value.length === 0;
        }
        if (isOptions(value)) {
            return Object.keys(value).length === 0;
        }
        return false;
    }
    isBlank.key = 'up.util.isBlank';
    function presence(value, tester = isPresent) {
        if (tester(value)) {
            return value;
        }
    }
    const isPresent = negate(isBlank);
    function isFunction(value) {
        return typeof (value) === 'function';
    }
    function isString(value) {
        return (typeof (value) === 'string') || value instanceof String;
    }
    function isBoolean(value) {
        return (typeof (value) === 'boolean') || value instanceof Boolean;
    }
    function isNumber(value) {
        return (typeof (value) === 'number') || value instanceof Number;
    }
    function isOptions(value) {
        return (typeof (value) === 'object') && !isNull(value) && (isUndefined(value.constructor) || (value.constructor === Object));
    }
    function isObject(value) {
        const typeOfResult = typeof (value);
        return ((typeOfResult === 'object') && !isNull(value)) || (typeOfResult === 'function');
    }
    function isElement(value) {
        return value instanceof Element;
    }
    function isTextNode(value) {
        return value instanceof Text;
    }
    function isRegExp(value) {
        return value instanceof RegExp;
    }
    function isError(value) {
        return value instanceof Error;
    }
    function isJQuery(value) {
        return up.browser.canJQuery() && value instanceof jQuery;
    }
    function isElementLike(value) {
        return !!(value && (value.addEventListener || (isJQuery(value) && value[0]?.addEventListener)));
    }
    function isPromise(value) {
        return isObject(value) && isFunction(value.then);
    }
    const { isArray } = Array;
    function isFormData(value) {
        return value instanceof FormData;
    }
    function toArray(value) {
        return isArray(value) ? value : copyArrayLike(value);
    }
    function isList(value) {
        return isArray(value) ||
            isNodeList(value) ||
            isArguments(value) ||
            isJQuery(value) ||
            isHTMLCollection(value);
    }
    function isNodeList(value) {
        return value instanceof NodeList;
    }
    function isHTMLCollection(value) {
        return value instanceof HTMLCollection;
    }
    function isArguments(value) {
        return Object.prototype.toString.call(value) === '[object Arguments]';
    }
    function isAdjacentPosition(value) {
        return /^(before|after)/.test(value);
    }
    function wrapList(value) {
        if (isList(value)) {
            return value;
        }
        else if (isMissing(value)) {
            return [];
        }
        else {
            return [value];
        }
    }
    function copy(value) {
        if (isObject(value) && value[copy.key]) {
            value = value[copy.key]();
        }
        else if (isList(value)) {
            value = copyArrayLike(value);
        }
        else if (isOptions(value)) {
            value = Object.assign({}, value);
        }
        return value;
    }
    function copyArrayLike(arrayLike) {
        return Array.prototype.slice.call(arrayLike);
    }
    copy.key = 'up.util.copy';
    Date.prototype[copy.key] = function () { return new Date(+this); };
    function merge(...sources) {
        return Object.assign({}, ...sources);
    }
    function mergeDefined(...sources) {
        const result = {};
        for (let source of sources) {
            if (source) {
                for (let key in source) {
                    const value = source[key];
                    if (isDefined(value)) {
                        result[key] = value;
                    }
                }
            }
        }
        return result;
    }
    function newOptions(object, defaults) {
        if (defaults) {
            return merge(defaults, object);
        }
        else if (object) {
            return copy(object);
        }
        else {
            return {};
        }
    }
    function parseArgIntoOptions(args, argKey) {
        let [positionalArg, options] = parseArgs(args, 'val', 'options');
        if (isDefined(positionalArg)) {
            options[argKey] = positionalArg;
        }
        return options;
    }
    function findInList(list, tester) {
        tester = iteratee(tester);
        let match;
        for (let element of list) {
            if (tester(element)) {
                match = element;
                break;
            }
        }
        return match;
    }
    function some(list, tester) {
        return !!findResult(list, tester);
    }
    function findResult(list, tester) {
        tester = iteratee(tester);
        let i = 0;
        for (let item of list) {
            const result = tester(item, i++);
            if (result) {
                return result;
            }
        }
    }
    function every(list, tester) {
        tester = iteratee(tester);
        let match = true;
        let i = 0;
        for (let item of list) {
            if (!tester(item, i++)) {
                match = false;
                break;
            }
        }
        return match;
    }
    function compact(array) {
        return filterList(array, isGiven);
    }
    function compactObject(object) {
        return pickBy(object, isGiven);
    }
    function uniq(array) {
        if (array.length < 2) {
            return array;
        }
        return Array.from(new Set(array));
    }
    function uniqBy(array, mapper) {
        if (array.length < 2) {
            return array;
        }
        mapper = iteratee(mapper);
        const seenElements = new Set();
        return filterList(array, function (elem, index) {
            const mapped = mapper(elem, index);
            if (seenElements.has(mapped)) {
                return false;
            }
            else {
                seenElements.add(mapped);
                return true;
            }
        });
    }
    function filterList(list, tester) {
        tester = iteratee(tester);
        const matches = [];
        each(list, function (element, index) {
            if (tester(element, index)) {
                return matches.push(element);
            }
        });
        return matches;
    }
    function reject(list, tester) {
        tester = negate(iteratee(tester));
        return filterList(list, tester);
    }
    function intersect(array1, array2) {
        return filterList(array1, (element) => contains(array2, element));
    }
    function scheduleTimer(millis, callback) {
        return setTimeout(callback, millis);
    }
    function queueTask(task) {
        setTimeout(task);
    }
    function queueFastTask(task) {
        const channel = new MessageChannel();
        channel.port1.onmessage = () => task();
        channel.port2.postMessage(0);
    }
    function last(value) {
        return value[value.length - 1];
    }
    function contains(value, subValue) {
        let indexOf = value.indexOf || Array.prototype.indexOf;
        return indexOf.call(value, subValue) >= 0;
    }
    function containsAll(values, subValues) {
        return every(subValues, (subValue) => contains(values, subValue));
    }
    function objectContains(object, subObject) {
        const reducedValue = pick(object, Object.keys(subObject));
        return isEqual(subObject, reducedValue);
    }
    function pick(object, keys) {
        const filtered = {};
        for (let key of keys) {
            if (key in object) {
                filtered[key] = object[key];
            }
        }
        return filtered;
    }
    function pickBy(object, tester) {
        tester = iteratee(tester);
        const filtered = {};
        for (let key in object) {
            const value = object[key];
            if (tester(value, key)) {
                filtered[key] = object[key];
            }
        }
        return filtered;
    }
    function omit(object, keys) {
        return pickBy(object, (_value, key) => !contains(keys, key));
    }
    function unresolvablePromise() {
        return new Promise(noop);
    }
    function remove(array, element) {
        const index = array.indexOf(element);
        if (index >= 0) {
            array.splice(index, 1);
            return element;
        }
    }
    function evalOption(value, ...args) {
        return isFunction(value) ? value(...args) : value;
    }
    function evalAutoOption(value, autoMeans, ...args) {
        value = evalOption(value, ...args);
        if (value === 'auto') {
            value = evalOption(autoMeans, ...args);
        }
        return value;
    }
    const ESCAPE_HTML_ENTITY_MAP = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': '&quot;',
        "'": '&#x27;'
    };
    function escapeHTML(string) {
        return string.replace(/[&<>"']/g, (char) => ESCAPE_HTML_ENTITY_MAP[char]);
    }
    function escapeRegExp(string) {
        return string.replace(/[\\^$*+?.()|[\]{}]/g, '\\$&');
    }
    function pluckKey(object, key) {
        const value = object[key];
        delete object[key];
        return value;
    }
    function renameKey(object, oldKey, newKey) {
        if (oldKey in object) {
            object[newKey] = pluckKey(object, oldKey);
        }
    }
    function extractLastArg(args, tester) {
        if (tester(last(args))) {
            return args.pop();
        }
    }
    function extractCallback(args) {
        return extractLastArg(args, isFunction);
    }
    function extractOptions(args) {
        return extractLastArg(args, isOptions) || {};
    }
    function identity(arg) {
        return arg;
    }
    function sequence(...fns) {
        return (...callArgs) => callAll(fns, callArgs);
    }
    function callAll(fns, ...args) {
        fns = scanFunctions(fns);
        return map(fns, (fn) => fn(...args));
    }
    function flatten(array) {
        const flattened = [];
        for (let object of array) {
            if (isList(object)) {
                flattened.push(...object);
            }
            else {
                flattened.push(object);
            }
        }
        return flattened;
    }
    function flatMap(array, block) {
        return flatten(map(array, block));
    }
    function always(promise, callback = identity) {
        return promise.then(callback, callback);
    }
    function newDeferred() {
        let resolveFn;
        let rejectFn;
        const nativePromise = new Promise(function (givenResolve, givenReject) {
            resolveFn = givenResolve;
            rejectFn = givenReject;
        });
        nativePromise.resolve = resolveFn;
        nativePromise.reject = rejectFn;
        return nativePromise;
    }
    function isBasicObjectProperty(k) {
        return Object.prototype.hasOwnProperty(k);
    }
    function isEqual(a, b) {
        if (a === b) {
            return true;
        }
        if (a?.valueOf) {
            a = a.valueOf();
        }
        if (b?.valueOf) {
            b = b.valueOf();
        }
        if (a === b) {
            return true;
        }
        if (typeof (a) !== typeof (b)) {
            return false;
        }
        if (isList(a) && isList(b)) {
            return isEqualList(a, b);
        }
        if (isObject(a) && a[isEqual.key]) {
            return a[isEqual.key](b);
        }
        if (isOptions(a) && isOptions(b)) {
            return isEqualOptions(a, b);
        }
        return false;
    }
    function isEqualOptions(a, b) {
        const aKeys = Object.keys(a);
        const bKeys = Object.keys(b);
        return isEqualList(aKeys, bKeys) && every(aKeys, (key) => isEqual(a[key], b[key]));
    }
    isEqual.key = 'up.util.isEqual';
    function isEqualList(a, b) {
        return (a.length === b.length) && every(a, (elem, index) => isEqual(elem, b[index]));
    }
    function getSimpleTokens(value, { json = false, separator = /[,\s]/ } = {}) {
        if (!isString(value)) {
            return wrapList(value);
        }
        else if (json && /^\[.*]$/.test(value)) {
            return parseRelaxedJSON(value);
        }
        else {
            return splitSimpleTokenString(value, separator);
        }
    }
    function splitSimpleTokenString(value, separator) {
        let parts = up.migrate.splitAtOr?.(value) || value.split(separator);
        return parts.map((s) => s.trim()).filter(identity);
    }
    function getComplexTokens(value) {
        if (!isString(value)) {
            return wrapList(value);
        }
        else {
            let { maskedTokens, restore } = complexTokenOutlines(value);
            return maskedTokens.map((token) => restore(token));
        }
    }
    function complexTokenOutlines(string) {
        let { masked, restore } = expressionOutline(string);
        let maskedTokens = splitSimpleTokenString(masked, ',');
        return { maskedTokens, restore };
    }
    function wrapValue(constructor, ...args) {
        return (args[0] instanceof constructor) ? args[0] : new constructor(...args);
    }
    let nextUid = 0;
    function uid() {
        return nextUid++;
    }
    function withRenamedKeys(object, renameKeyFn) {
        const renamed = {};
        for (let key in object) {
            let transformed = renameKeyFn(key);
            if (isGiven(transformed)) {
                renamed[transformed] = object[key];
            }
        }
        return renamed;
    }
    function camelToKebabCase(str) {
        return str.replace(/[A-Z]/g, (char) => '-' + char.toLowerCase());
    }
    function kebabToCamelCase(str) {
        return str.replace(/-([a-z])/g, (_match, char) => char.toUpperCase());
    }
    function lowerCaseFirst(str) {
        return str[0].toLowerCase() + str.slice(1);
    }
    function upperCaseFirst(str) {
        return str[0].toUpperCase() + str.slice(1);
    }
    function defineDelegates(object, props, targetProvider) {
        for (let prop of props) {
            Object.defineProperty(object, prop, {
                get() {
                    const target = targetProvider.call(this);
                    let value = target[prop];
                    if (isFunction(value)) {
                        value = value.bind(target);
                    }
                    return value;
                },
                set(newValue) {
                    const target = targetProvider.call(this);
                    target[prop] = newValue;
                }
            });
        }
    }
    function delegatePromise(object, targetProvider) {
        return defineDelegates(object, ['then', 'catch', 'finally'], targetProvider);
    }
    function stringifyArg(arg, placeholder = '%o') {
        let string;
        const maxLength = 200;
        if (placeholder === '%c') {
            return '';
        }
        if (placeholder === '%s' && isGiven(arg)) {
            arg = arg.toString();
        }
        if (isString(arg)) {
            string = arg.trim().replace(/[\n\r\t ]+/g, ' ');
            if (placeholder === '%o') {
                string = JSON.stringify(string);
            }
        }
        else if (isUndefined(arg)) {
            string = 'undefined';
        }
        else if (isNumber(arg) || isFunction(arg)) {
            string = arg.toString();
        }
        else if (isArray(arg)) {
            string = `[${map(arg, stringifyArg).join(', ')}]`;
        }
        else if (isJQuery(arg)) {
            string = `$(${map(arg, stringifyArg).join(', ')})`;
        }
        else if (isElement(arg)) {
            string = tagOuterHTML(arg);
        }
        else if (isRegExp(arg) || isError(arg)) {
            string = arg.toString();
        }
        else {
            try {
                string = JSON.stringify(arg);
            }
            catch (error) {
                if (error.name === 'TypeError') {
                    string = '(circular structure)';
                }
                else {
                    throw error;
                }
            }
        }
        if (string.length > maxLength) {
            string = `${string.substr(0, maxLength)}…${last(string)}`;
        }
        return string;
    }
    const SPRINTF_PLACEHOLDERS = /%[oOdisfc]/g;
    function sprintf(message, ...args) {
        return message.replace(SPRINTF_PLACEHOLDERS, (placeholder) => stringifyArg(args.shift(), placeholder));
    }
    const SERIALIZED_TAG_PATTERN = /<("[^"]*"|[^">])*>/;
    function tagOuterHTML(element) {
        return element.cloneNode().outerHTML.match(SERIALIZED_TAG_PATTERN)[0];
    }
    function negate(fn) {
        return function (...args) {
            return !fn(...args);
        };
    }
    function memoizeMethod(object, propLiteral) {
        for (let prop in propLiteral) {
            let originalDescriptor = Object.getOwnPropertyDescriptor(object, prop);
            let oldImpl = originalDescriptor.value;
            let memoizedImpl = memoize(oldImpl, `__${prop}MemoizeCache`);
            object[prop] = memoizedImpl;
        }
    }
    function safeStringifyJSON(value) {
        let json = JSON.stringify(value);
        return escapeHighASCII(json);
    }
    function escapeHighASCII(string) {
        let unicodeEscape = (char) => "\\u" + char.charCodeAt(0).toString(16).padStart(4, '0');
        return string.replace(/[^\x00-\x7F]/g, unicodeEscape);
    }
    function variant(source, changes = {}) {
        let variant = Object.create(source);
        Object.assign(variant, changes);
        return variant;
    }
    function parseArgs(args, ...specs) {
        let results = [];
        while (specs.length) {
            let lastSpec = specs.pop();
            if (lastSpec === 'options') {
                results.unshift(extractOptions(args));
            }
            else if (lastSpec === 'callback') {
                results.unshift(extractCallback(args));
            }
            else if (lastSpec === 'val') {
                results.unshift(args.pop());
            }
            else if (isFunction(lastSpec)) {
                let value = lastSpec(last(args)) ? args.pop() : undefined;
                results.unshift(value);
            }
        }
        return results;
    }
    function scanFunctions(...values) {
        return values.flat(2).filter(isFunction);
    }
    function cleaner(order = 'lifo') {
        let fns = [];
        let track = function (values, transform) {
            values = scanFunctions(values).map(transform);
            fns.push(...scanFunctions(values));
        };
        let api = function (...values) {
            track(values, identity);
        };
        api.guard = function (...values) {
            track(values, up.error.guardFn);
        };
        api.clean = function (...args) {
            if (order === 'lifo')
                fns.reverse();
            fns.forEach((fn) => fn(...args));
            fns = [];
        };
        return api;
    }
    function maskPattern(str, patterns, { keepDelimiters = false } = {}) {
        let maskCount = 0;
        let maskPattern = /§\d+/g;
        let maskings = {};
        let replaceLayers = [];
        let replace = (replacePattern, allowRestoreTransform) => {
            let didReplace = false;
            str = str.replaceAll(replacePattern, function (match) {
                didReplace = true;
                let mask = '§' + (maskCount++);
                let remain;
                let masked;
                if (keepDelimiters) {
                    let startDelimiter = match[0];
                    let endDelimiter = match.slice(-1);
                    masked = match.slice(1, -1);
                    remain = startDelimiter + mask + endDelimiter;
                }
                else {
                    masked = match;
                    remain = mask;
                }
                maskings[mask] = masked;
                return remain;
            });
            if (didReplace)
                replaceLayers.unshift({ allowRestoreTransform });
        };
        replace(maskPattern, false);
        for (let pattern of patterns)
            replace(pattern, true);
        let restore = (s, transform = identity) => {
            for (let { allowRestoreTransform } of replaceLayers) {
                let iterationTransform = allowRestoreTransform ? transform : identity;
                s = s.replace(maskPattern, (match) => iterationTransform(assert(maskings[match], isString)));
            }
            return s;
        };
        return { masked: str, restore };
    }
    const QUOTED_STRING_PATTERN = /'(?:\\\\|\\'|[^'])*'|"(?:\\\\|\\"|[^"])*"/g;
    const NESTED_GROUP_PATTERN = /{(?:[^{}]|{[^{}]*})*}|\((?:[^\(\)]|\([^\(\)]*\))*\)|\[(?:[^\[\]]|\[[^\[\]]*\])*\]/g;
    function expressionOutline(str) {
        return maskPattern(str, [QUOTED_STRING_PATTERN, NESTED_GROUP_PATTERN], { keepDelimiters: true });
    }
    function ensureDoubleQuotes(str) {
        if (str[0] === '"')
            return str;
        assert(str[0] === "'");
        str = str.slice(1, -1);
        let transformed = str.replace(/(\\\\)|(\\')|(\\")|(")/g, function (_match, escapedBackslash, escapedSingleQuote, _doubleQuote) {
            return escapedBackslash
                || (escapedSingleQuote && "'")
                || '\\"';
        });
        return '"' + transformed + '"';
    }
    function parseString(value) {
        return JSON.parse(ensureDoubleQuotes(value));
    }
    function parseRelaxedJSON(str) {
        let { masked, restore } = maskPattern(str, [QUOTED_STRING_PATTERN]);
        masked = masked.replace(/([a-z_$][\w$]*:)/gi, (unquotedProperty) => ('"' + unquotedProperty.slice(0, -1) + '":'));
        masked = masked.replace(/,\s*([}\]])/g, '$1');
        masked = restore(masked, ensureDoubleQuotes);
        return JSON.parse(masked);
    }
    function parseScalarJSONPairs(str) {
        let { maskedTokens, restore } = complexTokenOutlines(str);
        return maskedTokens.map((maskedToken) => {
            let [_match, string, json] = maskedToken.match(/([^{]+)({[^}]*})?/);
            return [
                restore(string.trim()),
                json && parseRelaxedJSON(restore(json))
            ];
        });
    }
    function spanObject(keys, value) {
        return mapObject(keys, (key) => [key, value]);
    }
    function parseNumber(str) {
        if (isNumber(str)) {
            return str;
        }
        else if (isString(str) && /^-?\.?\d[\d._]*$/.test(str)) {
            return parseFloat(str.replaceAll('_', ''));
        }
    }
    function assert(value, testFn = isTruthy) {
        if (testFn(value)) {
            return value;
        }
        else {
            throw "assert failed";
        }
    }
    return {
        parseURL,
        normalizeURL,
        matchableURL,
        matchableURLPatternAtom,
        matchURLs,
        normalizeMethod,
        methodAllowsPayload,
        copy,
        merge,
        mergeDefined,
        options: newOptions,
        parseArgIntoOptions,
        each,
        map,
        flatMap,
        mapObject,
        spanObject,
        findResult,
        some,
        every,
        find: findInList,
        filter: filterList,
        reject,
        intersect,
        compact,
        compactObject,
        uniq,
        uniqBy,
        last,
        isNull,
        isDefined,
        isUndefined,
        isGiven,
        isMissing,
        isPresent,
        isBlank,
        presence,
        isObject,
        isFunction,
        isString,
        isBoolean,
        isNumber,
        isElement,
        isTextNode,
        isJQuery,
        isElementLike,
        isPromise,
        isOptions,
        isArray,
        isFormData,
        isList,
        isRegExp,
        isAdjacentPosition,
        timer: scheduleTimer,
        contains,
        containsAll,
        objectContains,
        toArray,
        pick,
        pickBy,
        omit,
        unresolvablePromise,
        remove,
        memoize,
        pluckKey,
        renameKey,
        extractOptions,
        extractCallback,
        noop,
        asyncNoop,
        identity,
        escapeHTML,
        escapeRegExp,
        sequence,
        callAll,
        evalOption,
        evalAutoOption,
        flatten,
        newDeferred,
        always,
        isBasicObjectProperty,
        isCrossOrigin,
        task: queueTask,
        fastTask: queueFastTask,
        isEqual,
        getSimpleTokens,
        getComplexTokens,
        wrapList,
        wrapValue,
        uid,
        upperCaseFirst,
        lowerCaseFirst,
        delegate: defineDelegates,
        delegatePromise,
        camelToKebabCase,
        kebabToCamelCase,
        sprintf,
        withRenamedKeys,
        memoizeMethod,
        safeStringifyJSON,
        variant,
        cleaner,
        scanFunctions,
        args: parseArgs,
        parseRelaxedJSON,
        parseScalarJSONPairs,
        maskPattern,
        expressionOutline,
        parseString,
        assert,
        parseNumber,
    };
})();


/***/ }),
/* 4 */
/***/ (() => {

up.error = (function () {
    function fail(...args) {
        throw new up.Error(args);
    }
    function isCritical(error) {
        return (typeof error !== 'object') || ((error.name !== 'AbortError') && !(error instanceof up.RenderResult) && !(error instanceof up.Response));
    }
    function muteUncriticalRejection(promise) {
        return promise.catch(throwCritical);
    }
    function muteUncriticalSync(block) {
        try {
            return block();
        }
        catch (e) {
            throwCritical(e);
        }
    }
    function throwCritical(value) {
        if (isCritical(value)) {
            throw value;
        }
    }
    function guard(fn, ...args) {
        try {
            return fn(...args);
        }
        catch (error) {
            reportError(error);
        }
    }
    function guardPromise(promise) {
        return promise.catch(reportError);
    }
    function guardFn(fn) {
        if (fn) {
            return (...args) => guard(() => fn(...args));
        }
    }
    return {
        fail,
        throwCritical,
        muteUncriticalRejection,
        muteUncriticalSync,
        guard,
        guardPromise,
        guardFn,
    };
})();
up.fail = up.error.fail;


/***/ }),
/* 5 */
/***/ (() => {

up.migrate = {
    config: {},
};


/***/ }),
/* 6 */
/***/ (() => {

up.browser = (function () {
    function submitForm(form) {
        form.submit();
    }
    function canPushState() {
        return up.protocol.initialRequestMethod() === 'GET';
    }
    function canJQuery() {
        return !!window.jQuery;
    }
    function popCookie(name) {
        let value = document.cookie.match(new RegExp(name + "=(\\w+)"))?.[1];
        if (value) {
            document.cookie = name + '=;Max-Age=0;Path=/';
            return value;
        }
    }
    function assertConfirmed(options) {
        const confirmed = !options.confirm || window.confirm(options.confirm);
        if (!confirmed) {
            throw new up.Aborted('User canceled action');
        }
        return true;
    }
    return {
        submitForm,
        canPushState,
        canJQuery,
        assertConfirmed,
        popCookie,
    };
})();


/***/ }),
/* 7 */
/***/ ((__unused_webpack_module, __unused_webpack_exports, __webpack_require__) => {

__webpack_require__(8);
up.element = (function () {
    const u = up.util;
    function first(...args) {
        let [root = document, selector] = u.args(args, 'val', 'val');
        return root.querySelector(selector);
    }
    function subtree(root, selector) {
        const descendantMatches = root.querySelectorAll(selector);
        if (elementLikeMatches(root, selector)) {
            return [root, ...descendantMatches];
        }
        else {
            return descendantMatches;
        }
    }
    function subtreeFirst(root, selector) {
        return elementLikeMatches(root, selector) ? root : root.querySelector(selector);
    }
    function elementLikeMatches(elementLike, selector) {
        return u.isElement(elementLike) && elementLike.matches(selector);
    }
    function contains(root, selectorOrElement) {
        const element = getOne(selectorOrElement);
        return Node.prototype.contains.call(root, element);
    }
    function ancestor(element, selector) {
        return element.parentNode?.closest(selector);
    }
    function around(element, selector) {
        return getList(element.closest(selector), subtree(element, selector));
    }
    function getOne(...args) {
        const value = args.pop();
        if (u.isElement(value)) {
            return value;
        }
        else if (u.isString(value)) {
            return first(...args, value);
        }
        else if (u.isList(value)) {
            if (value.length > 1) {
                up.fail('up.element.get(): Cannot cast multiple elements (%o) to a single element', value);
            }
            return value[0];
        }
        else {
            return value;
        }
    }
    function getList(...args) {
        return u.flatMap(args, valueToList);
    }
    function valueToList(value) {
        if (u.isString(value)) {
            return document.querySelectorAll(value);
        }
        else {
            return u.wrapList(value);
        }
    }
    function hide(element) {
        setVisible(element, false);
    }
    function show(element) {
        setVisible(element, true);
    }
    function showTemp(element) {
        return setVisibleTemp(element, true);
    }
    function hideTemp(element) {
        return setVisibleTemp(element, false);
    }
    function setVisibleTemp(element, newVisible) {
        if (newVisible === isVisible(element))
            return u.noop;
        setVisible(element, newVisible);
        return () => setVisible(element, !newVisible);
    }
    function setVisible(element, newVisible) {
        if (newVisible) {
            element.removeAttribute('hidden');
            if (element.style.display === 'none') {
                element.style.display = '';
            }
        }
        else {
            element.setAttribute('hidden', '');
        }
    }
    function toggle(element, newVisible = !isVisible(element)) {
        setVisible(element, newVisible);
    }
    function setAttrPresence(element, attr, value, newPresent) {
        if (newPresent) {
            return element.setAttribute(attr, value);
        }
        else {
            return element.removeAttribute(attr);
        }
    }
    function setAttrs(element, attrs) {
        for (let key in attrs) {
            const value = attrs[key];
            if (u.isGiven(value)) {
                element.setAttribute(key, value);
            }
            else {
                element.removeAttribute(key);
            }
        }
    }
    function setAttrsTemp(element, attrs) {
        let keys = Object.keys(attrs);
        let oldAttrs = pickAttrs(element, keys);
        setAttrs(element, attrs);
        return () => setAttrs(element, oldAttrs);
    }
    function metaContent(name) {
        const selector = "meta" + attrSelector('name', name);
        return document.head.querySelector(selector)?.content;
    }
    function insertBefore(existingNode, newNode) {
        existingNode.parentNode.insertBefore(newNode, existingNode);
    }
    function createFromSelector(selector, attrs = {}) {
        let { includePath } = parseSelector(selector);
        let rootElement;
        let depthElement;
        let previousElement;
        for (let includeSegment of includePath) {
            let { tagName } = includeSegment;
            if (!tagName || tagName === '*') {
                tagName = 'div';
            }
            depthElement = document.createElement(tagName);
            if (!rootElement) {
                rootElement = depthElement;
            }
            makeVariation(depthElement, includeSegment);
            previousElement?.appendChild(depthElement);
            previousElement = depthElement;
        }
        for (let key in attrs) {
            let value = attrs[key];
            if (key === 'class') {
                addClasses(rootElement, u.wrapList(value));
            }
            else if (key === 'style') {
                setInlineStyle(rootElement, value);
            }
            else if (key === 'text') {
                rootElement.textContent = value;
            }
            else if (key === 'content') {
                if (u.isString(value)) {
                    rootElement.innerHTML = value;
                }
                else {
                    rootElement.append(...u.wrapList(value));
                }
            }
            else {
                rootElement.setAttribute(key, value);
            }
        }
        return rootElement;
    }
    function makeVariation(element, { id, classNames, attributes }) {
        if (id) {
            element.id = id;
        }
        for (let [name, value] of Object.entries(attributes)) {
            element.setAttribute(name, value);
        }
        addClasses(element, classNames);
    }
    function parseSelector(rawSelector) {
        let excludeRaw;
        const { masked: selectorOutline, restore: restoreSelectorLiterals, } = u.expressionOutline(rawSelector);
        const includeWithoutAttrs = selectorOutline.replace(/:not\([^)]*\)/, function (match) {
            excludeRaw = restoreSelectorLiterals(match);
            return '';
        });
        let includeRaw = restoreSelectorLiterals(includeWithoutAttrs);
        const includeSegments = includeWithoutAttrs.split(/[ >]+/);
        let includePath = includeSegments.map(function (depthSelector) {
            let parsed = {
                tagName: null,
                classNames: [],
                id: null,
                attributes: {}
            };
            depthSelector = depthSelector.replace(/^[\w-*]+/, function (match) {
                parsed.tagName = match;
                return '';
            });
            depthSelector = depthSelector.replace(/#([\w-]+)/, function (_match, id) {
                parsed.id = id;
                return '';
            });
            depthSelector = depthSelector.replace(/\.([\w-]+)/g, function (_match, className) {
                parsed.classNames.push(className);
                return '';
            });
            depthSelector = depthSelector.replace(/\[[^\]]*]/g, function (attr) {
                attr = restoreSelectorLiterals(attr);
                let [_raw, name, _operator, quote, value] = attr.match(/\[([\w-]+)(?:([~|^$*]?=)(["'])?([^\3\]]*?)\3)?]/);
                quote ||= '"';
                parsed.attributes[name] = value ? u.parseString(quote + value + quote) : '';
                return '';
            });
            if (depthSelector) {
                up.fail('Cannot parse selector: ' + rawSelector);
            }
            return parsed;
        });
        return {
            includePath,
            includeRaw,
            excludeRaw,
        };
    }
    function affix(...args) {
        let [parent, position = 'beforeend', selector, attributes] = u.args(args, 'val', u.isAdjacentPosition, 'val', 'options');
        const element = createFromSelector(selector, attributes);
        parent.insertAdjacentElement(position, element);
        return element;
    }
    const SINGLETON_TAG_NAMES = ['HTML', 'BODY', 'HEAD', 'TITLE'];
    const isSingleton = up.mockable((element) => element.matches(SINGLETON_TAG_NAMES.join()));
    function elementTagName(element) {
        return element.tagName.toLowerCase();
    }
    function attrSelector(attribute, value) {
        if (u.isGiven(value)) {
            value = value.replace(/"/g, '\\"');
            return `[${attribute}="${value}"]`;
        }
        else {
            return `[${attribute}]`;
        }
    }
    function idSelector(id) {
        if (id.match(/^[a-z][a-z0-9\-_]*$/i)) {
            return `#${id}`;
        }
        else {
            return attrSelector('id', id);
        }
    }
    function classSelector(klass) {
        klass = klass.replace(/[^\w-]/g, '\\$&');
        return `.${klass}`;
    }
    function createBrokenDocumentFromHTML(html) {
        const firstTag = firstTagNameInHTML(html);
        if (['TR', 'TD', 'TH', 'THEAD', 'TBODY'].includes(firstTag)) {
            html = `<table>${html}</table>`;
        }
        return new DOMParser().parseFromString(html, 'text/html');
    }
    function revivedClone(element) {
        let clone = createFromHTML(element.outerHTML);
        if ('nonce' in element)
            clone.nonce = element.nonce;
        return clone;
    }
    function createFromHTML(html) {
        return extractSingular(createNodesFromHTML(html));
    }
    function extractSingular(nodes) {
        return tryExtractSingular(nodes) || up.fail('Expected a single element, but got %d nodes', nodes.length);
    }
    function tryExtractSingular(nodes) {
        if (nodes.length === 1 && u.isElementLike(nodes[0])) {
            return nodes[0];
        }
    }
    function createNodesFromHTML(html) {
        html = html.trim();
        const range = document.createRange();
        range.setStart(document.body, 0);
        const fragment = range.createContextualFragment(html);
        return fragment.childNodes;
    }
    function getRoot() {
        return document.documentElement;
    }
    function paint(element) {
        element.offsetHeight;
    }
    function fixedToAbsolute(element) {
        const elementRectAsFixed = element.getBoundingClientRect();
        element.style.position = 'absolute';
        const offsetParentRect = element.offsetParent.getBoundingClientRect();
        setInlineStyle(element, {
            left: (elementRectAsFixed.left - computedStyleNumber(element, 'margin-left') - offsetParentRect.left) + 'px',
            top: (elementRectAsFixed.top - computedStyleNumber(element, 'margin-top') - offsetParentRect.top) + 'px',
            right: '',
            bottom: ''
        });
    }
    function setMissingAttrs(element, attrs) {
        for (let key in attrs) {
            setMissingAttr(element, key, attrs[key]);
        }
    }
    function setMissingAttr(element, key, value) {
        if (u.isMissing(element.getAttribute(key))) {
            element.setAttribute(key, value);
        }
    }
    function unwrap(wrapper) {
        preservingFocus(function () {
            let childNodes = [...wrapper.childNodes];
            for (let child of childNodes)
                insertBefore(wrapper, child);
            wrapper.remove();
        });
    }
    function wrapNodes(nodeOrNodes) {
        const wrapper = document.createElement('up-wrapper');
        wrapper.append(...u.wrapList(nodeOrNodes));
        return wrapper;
    }
    function wrapIfRequired(nodes) {
        if (nodes.length === 1 && u.isElement(nodes[0])) {
            return nodes[0];
        }
        else {
            return wrapNodes(nodes);
        }
    }
    function wrapChildren(element) {
        const wrapper = wrapNodes(element.childNodes);
        element.append(wrapper);
        return wrapper;
    }
    function preservingFocus(fn) {
        const oldFocusElement = document.activeElement;
        try {
            return fn();
        }
        finally {
            if (oldFocusElement && oldFocusElement !== document.activeElement) {
                oldFocusElement.focus({ preventScroll: true });
            }
        }
    }
    function parseAttr(element, attribute, ...parsers) {
        if (!element.hasAttribute?.(attribute))
            return undefined;
        let rawValue = element.getAttribute(attribute);
        for (let parser of parsers) {
            let parserResult = parser(rawValue, attribute, element);
            if (u.isDefined(parserResult))
                return parserResult;
        }
    }
    function stringAttr(element, attribute) {
        return parseAttr(element, attribute, tryParseString);
    }
    let tryParseString = u.identity;
    function booleanAttr(element, attribute) {
        return parseAttr(element, attribute, tryParseBoolean);
    }
    function tryParseBoolean(value, attribute) {
        switch (value) {
            case 'false': {
                return false;
            }
            case 'true':
            case '':
            case attribute:
                {
                    return true;
                }
        }
    }
    function booleanOrStringAttr(element, attribute) {
        return parseAttr(element, attribute, tryParseBoolean, tryParseString);
    }
    function booleanOrNumberAttr(element, attribute) {
        return parseAttr(element, attribute, tryParseBoolean, tryParseNumber);
    }
    function booleanOrNumberOrStringAttr(element, attribute) {
        return parseAttr(element, attribute, tryParseBoolean, tryParseNumber, tryParseString);
    }
    function numberAttr(element, attribute) {
        return parseAttr(element, attribute, tryParseNumber);
    }
    function tryParseNumber(value) {
        return u.parseNumber(value);
    }
    function jsonAttr(element, attribute) {
        return parseAttr(element, attribute, tryParseJSON);
    }
    function tryParseJSON(value) {
        if (value?.trim()) {
            return u.parseRelaxedJSON(value);
        }
    }
    function closestAttr(element, attr, readAttrFn = stringAttr) {
        let match = element.closest('[' + attr + ']');
        if (match) {
            return readAttrFn(match, attr);
        }
    }
    function addClasses(element, classes) {
        for (let klass of classes)
            element.classList.add(klass);
    }
    function addClassTemp(element, klass) {
        return setClassStateTemp(element, klass, true);
    }
    function removeClassTemp(element, klass) {
        return setClassStateTemp(element, klass, false);
    }
    function setClassStateTemp(element, klass, targetState) {
        if (element.classList.contains(klass) === targetState)
            return u.noop;
        element.classList.toggle(klass, targetState);
        return () => element.classList.toggle(klass, !targetState);
    }
    function computedStyle(element, props) {
        const style = window.getComputedStyle(element);
        return extractFromStyleObject(style, props);
    }
    function computedStyleNumber(element, prop) {
        const rawValue = computedStyle(element, prop);
        if (u.isPresent(rawValue)) {
            return parseFloat(rawValue);
        }
    }
    function inlineStyle(element, props) {
        const { style } = element;
        return extractFromStyleObject(style, props);
    }
    function extractFromStyleObject(style, keyOrKeys) {
        if (up.migrate.loaded)
            keyOrKeys = up.migrate.fixGetStyleProps(keyOrKeys);
        if (u.isString(keyOrKeys)) {
            return style.getPropertyValue(keyOrKeys);
        }
        else {
            return u.mapObject(keyOrKeys, (key) => [key, style.getPropertyValue(key)]);
        }
    }
    function setInlineStyle(element, props, unit = '') {
        if (up.migrate.loaded)
            props = up.migrate.fixSetStyleProps(props, unit);
        if (u.isString(props)) {
            element.setAttribute('style', props);
        }
        else {
            const { style } = element;
            for (let key in props) {
                let value = props[key];
                style.setProperty(key, value + unit);
            }
        }
    }
    function setStyleTemp(element, newStyles) {
        const oldStyles = inlineStyle(element, Object.keys(newStyles));
        setInlineStyle(element, newStyles);
        return () => setInlineStyle(element, oldStyles);
    }
    function isVisible(element) {
        return !!(element.offsetWidth || element.offsetHeight || element.getClientRects().length);
    }
    function isUpPrefixed(string) {
        return /^up-/.test(string);
    }
    function pickAttrs(element, attrNames) {
        return u.mapObject(attrNames, (name) => [name, element.getAttribute(name)]);
    }
    function upAttrs(element) {
        let attrNames = element.getAttributeNames().filter(isUpPrefixed);
        return pickAttrs(element, attrNames);
    }
    function upClasses(element) {
        return u.filter(element.classList.values(), isUpPrefixed);
    }
    function isEmpty(element) {
        return !element.children.length > 0 && !element.innerText.trim();
    }
    function crossOriginSelector(attr) {
        return `[${attr}*="//"]:not([${attr}*="//${location.host}/"])`;
    }
    function isIntersectingWindow(element, { margin = 0 } = {}) {
        const rect = up.Rect.fromElement(element);
        rect.grow(margin);
        return (rect.bottom > 0) && (rect.top < window.innerHeight) &&
            (rect.right > 0) && (rect.left < window.innerWidth);
    }
    function unionSelector(includes, excludes, condition) {
        let selector = `:is(${includes.join()})`;
        if (u.isPresent(excludes))
            selector += `:not(${excludes.join()})`;
        if (condition)
            selector += `:is(${condition})`;
        return selector;
    }
    function documentPosition(element) {
        let nextSibling = element.nextElementSibling;
        if (nextSibling) {
            return [nextSibling, 'beforebegin'];
        }
        else {
            return [element.parentElement, 'beforeend'];
        }
    }
    const FIRST_TAG_NAME_PATTERN = /^\s*(<!--[^-]*.*?-->\s*)*<([a-z-!]+)\b/i;
    function firstTagNameInHTML(html) {
        return FIRST_TAG_NAME_PATTERN.exec(html)?.[2].toUpperCase();
    }
    function isFullDocumentHTML(html) {
        let firstTag = firstTagNameInHTML(html);
        return firstTag === 'HTML' || firstTag === '!DOCTYPE';
    }
    function leadingElement(nodes) {
        for (let node of nodes) {
            if (u.isElement(node)) {
                return node;
            }
            else if (u.isTextNode(node) && node.textContent.trim()) {
                return;
            }
            else {
            }
        }
    }
    function removeAttrsFromHTML(html, attrs) {
        let tagPattern = /<[^<]+>/g;
        let attrPattern = new RegExp(`\\s+(${attrs.join('|')})="[^"]*"`, 'g');
        let cleanTag = (match) => match.replace(attrPattern, '');
        html = html.replace(tagPattern, cleanTag);
        return html;
    }
    return {
        subtree,
        subtreeFirst,
        contains,
        closestAttr,
        ancestor,
        around,
        get: getOne,
        list: getList,
        toggle,
        hide,
        hideTemp,
        show,
        showTemp,
        metaContent,
        insertBefore,
        createFromSelector,
        setAttrs,
        setAttrsTemp,
        affix,
        idSelector,
        classSelector,
        isSingleton,
        attrSelector,
        tagName: elementTagName,
        createBrokenDocumentFromHTML,
        revivedClone,
        createNodesFromHTML,
        createFromHTML,
        extractSingular,
        get root() { return getRoot(); },
        paint,
        fixedToAbsolute,
        setMissingAttrs,
        setMissingAttr,
        unwrap,
        wrapChildren,
        wrapIfRequired,
        attr: stringAttr,
        booleanAttr,
        numberAttr,
        jsonAttr,
        parseAttr,
        booleanOrStringAttr,
        booleanOrNumberAttr,
        booleanOrNumberOrStringAttr,
        setStyleTemp,
        style: computedStyle,
        styleNumber: computedStyleNumber,
        inlineStyle,
        setStyle: setInlineStyle,
        isVisible,
        upAttrs,
        upClasses,
        setAttrPresence,
        addClasses,
        addClassTemp,
        removeClassTemp,
        parseSelector,
        isEmpty,
        crossOriginSelector,
        isIntersectingWindow,
        unionSelector,
        elementLikeMatches,
        documentPosition,
        isFullDocumentHTML,
        leadingElement,
        removeAttrsFromHTML,
    };
})();


/***/ }),
/* 8 */
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
// extracted by mini-css-extract-plugin


/***/ }),
/* 9 */
/***/ (() => {

up.Error = class Error extends window.Error {
    constructor(message, props = {}) {
        if (Array.isArray(message)) {
            message = up.util.sprintf(...message);
        }
        super(message);
        let name = 'up.' + this.constructor.name;
        Object.assign(this, { name }, props);
    }
};


/***/ }),
/* 10 */
/***/ (() => {

up.NotImplemented = class NotImplemented extends up.Error {
};


/***/ }),
/* 11 */
/***/ (() => {

up.Aborted = class Aborted extends up.Error {
    constructor(message) {
        super(message, { name: 'AbortError' });
    }
};


/***/ }),
/* 12 */
/***/ (() => {

up.Blocked = class Blocked extends up.Error {
};


/***/ }),
/* 13 */
/***/ (() => {

up.CannotMatch = class CannotMatch extends up.Error {
};


/***/ }),
/* 14 */
/***/ (() => {

up.CannotParse = class CannotParse extends up.Error {
};


/***/ }),
/* 15 */
/***/ (() => {

up.CannotTarget = class CannotTarget extends up.Error {
};


/***/ }),
/* 16 */
/***/ (() => {

up.Offline = class Offline extends up.Error {
};


/***/ }),
/* 17 */
/***/ (() => {

const u = up.util;
up.Record = class Record {
    keys() {
        throw 'Return an array of keys';
    }
    defaults(_options) {
        return {};
    }
    constructor(options) {
        Object.assign(this, u.mergeDefined(this.defaults(options), this.attributes(options)));
    }
    attributes(source = this) {
        return u.pick(source, this.keys());
    }
    [u.copy.key]() {
        return u.variant(this);
    }
    [u.isEqual.key](other) {
        return (this.constructor === other.constructor) && u.isEqual(this.attributes(), other.attributes());
    }
};


/***/ }),
/* 18 */
/***/ (() => {

const u = up.util;
const e = up.element;
up.Config = class Config {
    constructor(blueprintFn = (() => ({}))) {
        this._blueprintFn = blueprintFn;
        this.reset();
        document.addEventListener('up:framework:reset', () => this.reset());
    }
    reset() {
        Object.assign(this, this._blueprintFn());
    }
    matches(element, prop, condition) {
        return element?.matches(this.selector(prop, condition));
    }
    matchesFn(prop) {
        return (element, condition) => this.matches(element, prop, condition);
    }
    selector(prop, condition = '') {
        let includes = this[prop];
        let excludes = this['no' + u.upperCaseFirst(prop)];
        return e.unionSelector(includes, excludes, condition);
    }
    selectorFn(prop) {
        return (condition) => this.selector(prop, condition);
    }
    selectorFns(prop) {
        return [this.selectorFn(prop), this.matchesFn(prop)];
    }
};


/***/ }),
/* 19 */
/***/ (() => {

let enabledKey = 'up.log.enabled';
let enabled = false;
try {
    enabled = !!sessionStorage?.getItem(enabledKey);
}
catch {
}
up.LogConfig = class LogConfig extends up.Config {
    constructor() {
        super(() => ({
            banner: true,
            format: true,
        }));
    }
    get enabled() {
        return enabled;
    }
    set enabled(newEnabled) {
        enabled = newEnabled;
        try {
            sessionStorage?.setItem(enabledKey, newEnabled ? '1' : '');
        }
        catch {
        }
    }
};


/***/ }),
/* 20 */
/***/ (() => {

const u = up.util;
up.Registry = class Registry {
    constructor(valueDescription, normalize = u.identity) {
        this._data = {};
        this._normalize = normalize;
        this._valueDescription = valueDescription;
        this.put = this.put.bind(this);
        document.addEventListener('up:framework:reset', () => this.reset());
    }
    put(key, object) {
        object = this._normalize(object);
        object.isDefault = up.framework.evaling;
        this._data[key] = object;
    }
    get(name) {
        return this._data[name] || up.fail("Unknown %s %o", this._valueDescription, name);
    }
    reset() {
        this._data = u.pickBy(this._data, 'isDefault');
    }
};


/***/ }),
/* 21 */
/***/ (() => {

const u = up.util;
const e = up.element;
up.OptionsParser = class OptionsParser {
    constructor(element, options, parserOptions = {}) {
        this._options = options;
        this._element = element;
        this._fail = parserOptions.fail;
        this._closest = parserOptions.closest;
        this._attrPrefix = parserOptions.attrPrefix || 'up-';
        this._defaults = parserOptions.defaults ?? {};
    }
    string(key, keyOptions) {
        this.parse(e.attr, key, keyOptions);
    }
    boolean(key, keyOptions) {
        this.parse(e.booleanAttr, key, keyOptions);
    }
    number(key, keyOptions) {
        this.parse(e.numberAttr, key, keyOptions);
    }
    booleanOrString(key, keyOptions) {
        this.parse(e.booleanOrStringAttr, key, keyOptions);
    }
    booleanOrNumber(key, keyOptions) {
        this.parse(e.booleanOrNumberAttr, key, keyOptions);
    }
    booleanOrNumberOrString(key, keyOptions) {
        this.parse(e.booleanOrNumberOrStringAttr, key, keyOptions);
    }
    json(key, keyOptions) {
        this.parse(e.jsonAttr, key, keyOptions);
    }
    renderCallback(key, keyOptions = {}) {
        let attrReader = (link, attr) => up.RenderOptions.callbackAttr(link, attr, key);
        this.parse(attrReader, key, keyOptions);
    }
    parse(attrReader, key, keyOptions = {}) {
        const attrNames = u.wrapList(keyOptions.attr ?? this._attrNameForKey(key));
        let value = this._options[key];
        for (let attrName of attrNames) {
            value ??= this._parseFromAttr(attrReader, this._element, attrName);
        }
        if (this._defaults !== false) {
            value ??= keyOptions.default ?? this._defaults[key];
        }
        if (u.isDefined(value)) {
            let normalizeFn = keyOptions.normalize;
            if (normalizeFn) {
                value = normalizeFn(value);
            }
            this._options[key] = value;
        }
        let failKey;
        if (this._fail && (failKey = up.fragment.failKey(key))) {
            const failAttrNames = u.compact(u.map(attrNames, (attrName) => this._deriveFailAttrName(attrName)));
            this.parse(attrReader, failKey, { ...keyOptions, attr: failAttrNames });
        }
    }
    include(optionsFn, parserOptions) {
        let fnResult = optionsFn(this._element, this._options, { defaults: this._defaults, ...parserOptions });
        Object.assign(this._options, fnResult);
    }
    _parseFromAttr(attrValueFn, element, attrName) {
        if (this._closest) {
            return e.closestAttr(element, attrName, attrValueFn);
        }
        else {
            return attrValueFn(element, attrName);
        }
    }
    _deriveFailAttrName(attr) {
        return this._deriveFailAttrNameForPrefix(attr, this._attrPrefix + 'on-') ||
            this._deriveFailAttrNameForPrefix(attr, this._attrPrefix);
    }
    _deriveFailAttrNameForPrefix(attr, prefix) {
        if (attr.startsWith(prefix)) {
            return `${prefix}fail-${attr.substring(prefix.length)}`;
        }
    }
    _attrNameForKey(option) {
        return `${this._attrPrefix}${u.camelToKebabCase(option)}`;
    }
};


/***/ }),
/* 22 */
/***/ (() => {

const u = up.util;
up.FIFOCache = class FIFOCache {
    constructor({ capacity = 10, normalizeKey = u.identity } = {}) {
        this._map = new Map();
        this._capacity = capacity;
        this._normalizeKey = normalizeKey;
    }
    get(key) {
        key = this._normalizeKey(key);
        return this._map.get(key);
    }
    set(key, value) {
        if (this._map.size === this._capacity) {
            let oldestKey = this._map.keys().next().value;
            this._map.delete(oldestKey);
        }
        key = this._normalizeKey(key);
        this._map.set(key, value);
    }
    clear() {
        this._map.clear();
    }
};


/***/ }),
/* 23 */
/***/ (() => {

up.Rect = class Rect extends up.Record {
    keys() {
        return [
            'left',
            'top',
            'width',
            'height'
        ];
    }
    get bottom() {
        return this.top + this.height;
    }
    get right() {
        return this.left + this.width;
    }
    grow(padding) {
        this.left -= padding;
        this.top -= padding;
        this.width += padding * 2;
        this.height += padding * 2;
    }
    static fromElement(element) {
        return new (this)(element.getBoundingClientRect());
    }
    static fromElementAsFixed(element) {
        let fixedClone = element.cloneNode(true);
        element.after(fixedClone);
        fixedClone.style.position = 'fixed';
        let rect = this.fromElement(fixedClone);
        fixedClone.remove();
        return rect;
    }
};


/***/ }),
/* 24 */
/***/ (() => {

const e = up.element;
const u = up.util;
const SHIFT_CLASS = 'up-scrollbar-away';
up.BodyShifter = class BodyShifter {
    constructor() {
        this._anchoredElements = new Set();
        this._stack = 0;
        this._cleaner = u.cleaner();
    }
    lowerStack() {
        if (--this._stack === 0)
            this._unshiftNow();
    }
    raiseStack() {
        if (++this._stack === 1)
            this._shiftNow();
    }
    onAnchoredElementInserted(element) {
        this._anchoredElements.add(element);
        this._shiftElement(element, 'right');
        return () => this._anchoredElements.delete(element);
    }
    _isShifted() {
        return this._stack > 0;
    }
    _shiftNow() {
        this._rootScrollbarWidth = up.viewport.rootScrollbarWidth();
        this._cleaner(e.setStyleTemp(e.root, {
            '--up-scrollbar-width': this._rootScrollbarWidth + 'px'
        }));
        this._shiftElement(document.body, 'padding-right');
        for (let element of this._anchoredElements) {
            this._shiftElement(element, 'right');
        }
    }
    _unshiftNow() {
        this._cleaner.clean();
    }
    _shiftElement(element, styleProp) {
        if (!this._isShifted())
            return;
        let originalValue = e.style(element, styleProp);
        this._cleaner(e.setStyleTemp(element, { ['--up-original-' + styleProp]: originalValue }), e.addClassTemp(element, SHIFT_CLASS));
    }
};


/***/ }),
/* 25 */
/***/ (() => {

up.Change = class Change {
    constructor(options) {
        this.options = options;
    }
    execute() {
        throw new up.NotImplemented();
    }
    deriveFailOptions() {
        return up.RenderOptions.deriveFailOptions(this.options);
    }
};


/***/ }),
/* 26 */
/***/ (() => {

const u = up.util;
const e = up.element;
up.Change.Addition = class Addition extends up.Change {
    constructor(options) {
        super(options);
        this._acceptLayer = options.acceptLayer;
        this._dismissLayer = options.dismissLayer;
        this._eventPlans = options.eventPlans || [];
        this._response = options.response;
    }
    handleLayerChangeRequests(newElements, newLocation) {
        if (this.layer.isOverlay()) {
            this._tryAcceptLayerFromServer();
            this.layer.assertAlive();
            this.layer.tryAcceptForLocation(newLocation, this._response);
            this.layer.assertAlive();
            this.layer.tryAcceptForElements(newElements, this._response);
            this.layer.assertAlive();
            this._tryDismissLayerFromServer();
            this.layer.assertAlive();
            this.layer.tryDismissForLocation(newLocation, this._response);
            this.layer.assertAlive();
            this.layer.tryDismissForElements(newElements, this._response);
            this.layer.assertAlive();
        }
        this.layer.asCurrent(() => {
            for (let eventPlan of this._eventPlans) {
                up.emit({ ...eventPlan, response: this._response });
                this.layer.assertAlive();
            }
        });
    }
    _tryAcceptLayerFromServer() {
        if (u.isDefined(this._acceptLayer)) {
            this.layer.accept(this._acceptLayer, { response: this._response });
        }
    }
    _tryDismissLayerFromServer() {
        if (u.isDefined(this._dismissLayer)) {
            this.layer.dismiss(this._dismissLayer, { response: this._response });
        }
    }
    _setSource({ oldElement, newElement, source }) {
        if (source === 'keep') {
            source = (oldElement && up.fragment.source(oldElement));
        }
        if (source) {
            e.setMissingAttr(newElement, 'up-source', up.fragment.normalizeSource(source));
        }
    }
    _setTime({ newElement, time }) {
        e.setMissingAttr(newElement, 'up-time', time ? time.toUTCString() : false);
    }
    _setETag({ newElement, etag }) {
        e.setMissingAttr(newElement, 'up-etag', etag || false);
    }
    setReloadAttrs(options) {
        this._setSource(options);
        this._setTime(options);
        this._setETag(options);
    }
    executeSteps({ steps, responseDoc, noneOptions }) {
        return new up.Change.UpdateSteps({ steps, noneOptions }).execute(responseDoc);
    }
};


/***/ }),
/* 27 */
/***/ (() => {

var _a;
const u = up.util;
up.RenderJob = (_a = class RenderJob {
        constructor(renderOptions) {
            this.renderOptions = renderOptions;
        }
        execute() {
            this._rendered = this._executePromise();
            return this;
        }
        async _executePromise() {
            try {
                this._emitGuardEvent();
                this.renderOptions = up.RenderOptions.preprocess(this.renderOptions);
                up.browser.assertConfirmed(this.renderOptions);
                up.RenderOptions.assertContentGiven(this.renderOptions);
                let result = await this._getChange().execute();
                this._handleResult(result);
                return result;
            }
            catch (resultOrError) {
                this._handleResult(resultOrError) || this._handleError(resultOrError);
                throw resultOrError;
            }
        }
        _handleResult(result) {
            if (result instanceof up.RenderResult) {
                let { onRendered, onFinished } = result.renderOptions;
                if (!result.none)
                    up.error.guard(() => onRendered?.(result));
                let guardedOnFinished = function (result) {
                    up.error.guard(() => onFinished?.(result));
                };
                this.finished.then(guardedOnFinished, u.noop);
                return true;
            }
        }
        _handleError(error) {
            let prefix = error instanceof up.Aborted ? 'Rendering was aborted' : 'Error while rendering';
            up.puts('up.render()', `${prefix}: ${error.name}: ${error.message}`);
            up.error.guard(() => this.renderOptions.onError?.(error));
        }
        get finished() {
            return this._awaitFinished();
        }
        async _awaitFinished() {
            try {
                let result = await this._rendered;
                return await result.finished;
            }
            catch (error) {
                if (error instanceof up.RenderResult) {
                    throw await error.finished;
                }
                else {
                    throw error;
                }
            }
        }
        _getChange() {
            let handleAbort = u.memoize((request) => this._handleAbortOption(request));
            let renderOptions = { ...this.renderOptions, handleAbort };
            if (renderOptions.url) {
                return new up.Change.FromURL(renderOptions);
            }
            else if (renderOptions.response) {
                return new up.Change.FromResponse(renderOptions);
            }
            else {
                return new up.Change.FromContent(renderOptions);
            }
        }
        _emitGuardEvent() {
            let guardEvent = u.pluckKey(this.renderOptions, 'guardEvent');
            if (guardEvent) {
                guardEvent.renderOptions = this.renderOptions;
                if (up.emit(guardEvent, { target: this.renderOptions.origin }).defaultPrevented) {
                    throw new up.Aborted(`Rendering was prevented by ${guardEvent.type} listener`);
                }
            }
        }
        _handleAbortOption({ bindFragments, bindLayer, origin, layer, request }) {
            let { abort } = this.renderOptions;
            if (!abort)
                return;
            let abortOptions = {
                except: request,
                logOnce: ['up.render()', 'Change with { abort } option will abort other requests'],
                newLayer: (layer === 'new'),
                origin,
                jid: this.renderOptions.jid,
            };
            if (abort === 'target') {
                up.fragment.abort(bindFragments, { ...abortOptions });
            }
            else if (abort === 'layer') {
                up.fragment.abort({ ...abortOptions, layer: bindLayer });
            }
            else if (abort === 'all' || abort === true) {
                up.fragment.abort({ ...abortOptions, layer: 'any' });
            }
            else if (u.isFunction(abort)) {
                abort(abortOptions);
            }
            else {
                up.fragment.abort(abort, { ...abortOptions, layer: bindLayer });
            }
        }
    },
    (() => {
        u.delegatePromise(_a.prototype, function () { return this._rendered; });
        u.memoizeMethod(_a.prototype, {
            _awaitFinished: true,
            _getChange: true,
        });
    })(),
    _a);


/***/ }),
/* 28 */
/***/ (() => {

up.Change.DestroyFragment = class DestroyFragment extends up.Change {
    constructor(options) {
        super(options);
        this._layer = up.layer.get(options) || up.layer.current;
        this._element = this.options.element;
        this._animation = this.options.animation;
        this._log = this.options.log;
    }
    execute() {
        this._parent = this._element.parentNode;
        up.fragment.markAsDestroying(this._element);
        up.animate(this._element, this._animation, {
            ...this.options,
            onFinished: () => {
                this._erase();
                this._emitDestroyed();
                this.options.onFinished?.();
            }
        });
    }
    _erase() {
        this._layer.asCurrent(() => {
            up.fragment.abort(this._element);
            up.script.clean(this._element, { layer: this._layer });
            this._element.remove();
        });
    }
    _emitDestroyed() {
        up.fragment.emitDestroyed(this._element, { parent: this._parent, log: this._log });
    }
};


/***/ }),
/* 29 */
/***/ (() => {

let u = up.util;
up.Change.OpenLayer = class OpenLayer extends up.Change.Addition {
    constructor(options) {
        super(options);
        this.target = options.target;
        this._origin = options.origin;
        this._baseLayer = options.baseLayer;
    }
    getPreflightProps() {
        return {
            mode: this.options.mode,
            context: this._buildLayer().context,
            origin: this.options.origin,
            target: this.target,
            bindLayer: this._baseLayer,
            layer: 'new',
            bindFragments: u.compact([up.fragment.get(':main', { layer: this._baseLayer })]),
            fragments: [],
        };
    }
    execute(responseDoc, onApplicable) {
        this._matchPostflight(responseDoc);
        onApplicable();
        this._createOverlay();
        let renderOtherLayersOnce = u.memoize(() => this._renderOtherLayers(responseDoc));
        let unbindClosing = this.layer.on('up:layer:accepting up:layer:dismissing', renderOtherLayersOnce);
        try {
            let partialResults = [
                this._renderOverlayContent(responseDoc),
                ...renderOtherLayersOnce(),
            ];
            return new up.RenderResult({
                layer: this.layer,
                target: this.target,
                renderOptions: this.options,
                partialResults,
            });
        }
        finally {
            unbindClosing();
        }
    }
    _matchPostflight(responseDoc) {
        if (this.target === ':none') {
            this._content = document.createElement('up-none');
        }
        else {
            this._content = responseDoc.select(this.target);
        }
        if (!this._content || !this._baseLayer.isAlive()) {
            throw new up.CannotMatch();
        }
    }
    _createOverlay() {
        up.puts('up.render()', `Opening element "${this.target}" in new overlay`);
        this._assertOpenEventEmitted();
        this.layer = this._buildLayer();
        this._baseLayer.peel({ history: !this.layer.history, intent: this.options.peel });
        this._baseLayer.saveHistory();
        up.layer.stack.push(this.layer);
        this.layer.createElements();
        this.layer.setupHandlers();
    }
    _renderOverlayContent(responseDoc) {
        this.handleLayerChangeRequests([this._content], this._getNewLocation());
        responseDoc.commitElement(this._content);
        this.layer.setContent(this._content);
        responseDoc.finalizeElement(this._content);
        this._handleHistory();
        this.setReloadAttrs({ newElement: this._content, source: this.options.source });
        let compilePromise = this._compileLayer();
        this._handleFocus();
        this._handleScroll();
        this.layer.state = 'opened';
        this._emitOpenedEvent();
        this.layer.assertAlive();
        let animatePromise = this.layer.startOpenAnimation();
        return {
            fragments: [this._content],
            finished: Promise.all([compilePromise, animatePromise]),
            verifyFinished: () => this.layer.assertAlive()
        };
    }
    _renderOtherLayers(responseDoc) {
        let steps = this._getHungrySteps().other;
        return this.executeSteps({ steps, responseDoc });
    }
    async _compileLayer() {
        await up.hello(this.layer.element, {
            ...this.options,
            layer: this.layer,
            dataRoot: this._content
        });
    }
    _buildLayer() {
        const beforeNew = (optionsWithLayerDefaults) => {
            return this.options = up.RenderOptions.finalize(optionsWithLayerDefaults);
        };
        return up.layer.build(this.options, beforeNew);
    }
    _handleHistory() {
        if (this.layer.history === 'auto') {
            this.layer.history = up.fragment.hasAutoHistory([this._content], this.layer);
        }
        this.layer.history &&= this._baseLayer.history;
        this.layer.updateHistory(this._getEffectiveHistoryOptions());
    }
    _handleFocus() {
        this._baseLayer.overlayFocus?.moveToBack();
        this.layer.overlayFocus.moveToFront();
        const fragmentFocus = new up.FragmentFocus({
            fragment: this._content,
            layer: this.layer,
            autoMeans: ['autofocus', 'layer'],
            inputDevice: this.options.inputDevice,
        });
        fragmentFocus.process(this.options.focus);
    }
    _handleScroll() {
        const scrollingOptions = {
            ...this.options,
            fragment: this._content,
            layer: this.layer,
            autoMeans: ['hash', 'layer']
        };
        const scrolling = new up.FragmentScrolling(scrollingOptions);
        scrolling.process(this.options.scrollMap ?? this.options.scroll);
    }
    _assertOpenEventEmitted() {
        up.event.assertEmitted('up:layer:open', {
            origin: this._origin,
            baseLayer: this._baseLayer,
            layerOptions: this.options,
            log: "Opening new overlay"
        });
    }
    _emitOpenedEvent() {
        this.layer.emit('up:layer:opened', {
            origin: this._origin,
            callback: this.layer.callback('onOpened'),
            log: `Opened new ${this.layer}`
        });
    }
    _getHungrySteps() {
        return up.radio.hungrySteps(this._getEffectiveRenderOptions());
    }
    _getEffectiveRenderOptions() {
        return {
            ...this.options,
            layer: this.layer,
            history: this.layer.history,
        };
    }
    _getEffectiveHistoryOptions() {
        return up.history.options(this.options);
    }
    _getNewLocation() {
        return this._getEffectiveRenderOptions().location;
    }
};


/***/ }),
/* 30 */
/***/ (() => {

var _a;
const u = up.util;
up.Change.UpdateLayer = (_a = class UpdateLayer extends up.Change.Addition {
        constructor(options) {
            options = up.RenderOptions.finalize(options);
            super(options);
            this.layer = options.layer;
            this.target = options.target;
            this._context = options.context;
            this._steps = up.fragment.parseTargetSteps(this.target, this.options);
        }
        getPreflightProps() {
            this._matchPreflight();
            let fragments = this._getFragments();
            return {
                layer: this.layer,
                bindLayer: this.layer,
                mode: this.layer.mode,
                context: u.merge(this.layer.context, this._context),
                origin: this.options.origin,
                target: this._bestPreflightSelector(),
                fragments,
                bindFragments: fragments,
            };
        }
        _bestPreflightSelector() {
            this._matchPreflight();
            const isProbable = (step) => !step.maybe || step.oldElement?.isConnected;
            let bestSteps = this._steps.filter(isProbable);
            let selectors = u.map(bestSteps, 'selector');
            return selectors.join(', ') || ':none';
        }
        _getFragments() {
            this._matchPreflight();
            return u.map(this._steps, 'oldElement');
        }
        execute(responseDoc, onApplicable) {
            this._matchPostflight(responseDoc);
            onApplicable();
            let renderOtherLayersOnce = u.memoize(() => this._renderOtherLayers(responseDoc));
            let unbindClosing = this.layer.on('up:layer:accepting up:layer:dismissing', renderOtherLayersOnce);
            try {
                let partialResults = [
                    ...this._renderCurrentLayer(responseDoc),
                    ...renderOtherLayersOnce(),
                ];
                return new up.RenderResult({
                    target: this.target,
                    layer: this.layer,
                    renderOptions: this.options,
                    partialResults,
                });
            }
            finally {
                unbindClosing();
            }
        }
        _renderCurrentLayer(responseDoc) {
            if (this._steps.length) {
                up.puts('up.render()', `Updating "${this._bestPreflightSelector()}" in ${this.layer}`);
            }
            this._coordinateSteps();
            if (this.options.saveScroll) {
                up.viewport.saveScroll({ layer: this.layer });
            }
            if (this.options.saveFocus) {
                up.viewport.saveFocus({ layer: this.layer });
            }
            let { peel } = this.options;
            if (peel) {
                this.layer.peel({ history: !this._hasHistory(), intent: peel });
            }
            if (this.options.abort !== false) {
                up.fragment.abort(this._getFragments(), {
                    reason: 'Fragment is being replaced',
                    jid: this.options.jid,
                });
            }
            Object.assign(this.layer.context, this._context);
            this.handleLayerChangeRequests(u.map(this._steps, 'newElement'), this._getNewLocation());
            this.layer.updateHistory(this._getEffectiveHistoryOptions());
            return this.executeSteps({
                steps: this._steps,
                noneOptions: this.options,
                responseDoc,
            });
        }
        _renderOtherLayers(responseDoc) {
            let otherLayerSteps = this._getHungrySteps().other;
            return this.executeSteps({
                steps: otherLayerSteps,
                responseDoc,
            });
        }
        _matchPreflight() {
            this._matchOldElements();
            this._compressNestedSteps();
        }
        _matchPostflight(responseDoc) {
            this._matchOldElements();
            this._addHungryStepsOnCurrentLayer();
            this._compressNestedSteps();
            this._matchNewElements(responseDoc);
        }
        _addHungryStepsOnCurrentLayer() {
            this._steps.push(...this._getHungrySteps().current);
        }
        _matchOldElements() {
            this._steps = this._steps.filter((step) => {
                const finder = new up.FragmentFinder(u.pick(step, ['selector', 'origin', 'layer', 'match', 'preferOldElements']));
                step.oldElement ||= finder.find();
                if (step.oldElement) {
                    return true;
                }
                else if (!step.maybe) {
                    throw new up.CannotMatch();
                }
            });
        }
        _matchNewElements(responseDoc) {
            this._steps = responseDoc.selectSteps(this._steps);
        }
        _compressNestedSteps() {
            this._steps = up.fragment.compressNestedSteps(this._steps);
        }
        _getHungrySteps() {
            return up.radio.hungrySteps(this._getEffectiveRenderOptions());
        }
        _coordinateSteps() {
            let focusCapsule = up.FocusCapsule.preserve(this.layer);
            let oldScrollTops = up.viewport.getScrollTops({ layer: this.layer });
            this._steps.forEach((step, i) => {
                step.focusCapsule = focusCapsule;
                step.oldScrollTops = oldScrollTops;
                if (step.scrollMap)
                    step.scroll = false;
                if (i > 0) {
                    step.focus = false;
                    step.scrollMap = undefined;
                    if (step.scroll !== 'keep')
                        step.scroll = false;
                    step.data = undefined;
                }
            });
        }
        _hasHistory() {
            return u.evalAutoOption(this.options.history, this._hasAutoHistory.bind(this));
        }
        _hasAutoHistory() {
            const oldFragments = u.map(this._steps, 'oldElement');
            return up.fragment.hasAutoHistory(oldFragments, this.layer);
        }
        _getNewLocation() {
            return this._getEffectiveHistoryOptions().location;
        }
        _getEffectiveRenderOptions() {
            return {
                ...this.options,
                layer: this.layer,
                history: this._hasHistory(),
            };
        }
        _getEffectiveHistoryOptions() {
            if (this._hasHistory()) {
                return up.history.options(this.options);
            }
            else {
                return {};
            }
        }
    },
    (() => {
        u.memoizeMethod(_a.prototype, {
            _matchPreflight: true,
            _matchOldElements: true,
            _hasHistory: true,
            _getHungrySteps: true,
        });
    })(),
    _a);


/***/ }),
/* 31 */
/***/ (() => {

const u = up.util;
const e = up.element;
up.Change.UpdateSteps = class UpdateSteps extends up.Change.Addition {
    constructor(options) {
        super(options);
        this._steps = u.copy(u.assert(options.steps));
        this._noneOptions = options.noneOptions || {};
    }
    execute(responseDoc) {
        this.responseDoc = responseDoc;
        this._steps = responseDoc.selectSteps(this._steps);
        this._steps = responseDoc.commitSteps(this._steps);
        return [
            ...this._executeSteps(),
            this._assertLayersAlive(),
        ];
    }
    _executeSteps() {
        if (this._steps.length) {
            return this._steps.toReversed().map((step) => this._executeStep(step)).toReversed();
        }
        else {
            return this._executeNoSteps();
        }
    }
    _assertLayersAlive() {
        return {
            verifyFinished: () => {
                for (let step of this._steps) {
                    step.layer.assertAlive();
                }
            }
        };
    }
    _executeStep(step) {
        switch (step.placement) {
            case 'swap': {
                let keepPlan = up.fragment.keepPlan(step);
                if (keepPlan) {
                    return this._executeKeepEverythingStep(step, keepPlan);
                }
                else {
                    return this._executeSwapStep(step);
                }
            }
            case 'content': {
                return this._executeSwapChildrenStep(step);
            }
            case 'before':
            case 'after': {
                return this._executeInsertChildrenStep(step);
            }
            default: {
                up.fail('Unknown placement: %o', step.placement);
            }
        }
    }
    _executeNoSteps() {
        this._handleFocus(null, this._noneOptions);
        this._handleScroll(null, this._noneOptions);
        return [{}];
    }
    _executeKeepEverythingStep(step, keepPlan) {
        if (!keepPlan)
            return;
        up.fragment.emitKept(keepPlan);
        this._handleFocus(step.oldElement, step);
        this._handleScroll(step.oldElement, step);
        return {};
    }
    _executeSwapStep(step) {
        const parent = step.parentElement ?? step.oldElement.parentNode;
        up.fragment.markAsDestroying(step.oldElement);
        this._preserveDescendantKeepables(step);
        let compilePromise;
        let morphPromise = up.motion.morph(step.oldElement, step.newElement, step.transition, {
            ...step,
            afterInsert: () => {
                this._restoreDescendantKeepables(step);
                compilePromise = this._welcomeElement(step.newElement, step);
                this._finalizeDescendantKeepables(step);
                this._handleFocus(step.newElement, step);
                this._handleScroll(step.newElement, step);
            },
            beforeRemove: () => {
                up.script.clean(step.oldElement, { layer: step.layer });
            },
            afterRemove: () => {
                up.fragment.emitDestroyed(step.oldElement, { parent, log: false });
                step.afterRemove?.();
            }
        });
        return {
            fragments: [step.newElement],
            finished: Promise.all([morphPromise, compilePromise]),
        };
    }
    _executeSwapChildrenStep(step) {
        let newChildren = [...step.newElement.children];
        let oldWrapper = e.wrapChildren(step.oldElement);
        let newWrapper = e.wrapChildren(step.newElement);
        let wrapperResult = this._executeSwapStep({
            ...step,
            placement: 'swap',
            parentElement: step.oldElement.parentNode,
            oldElement: oldWrapper,
            newElement: newWrapper,
            focus: false,
            afterRemove: () => {
                e.unwrap(newWrapper);
                this._handleFocus(step.oldElement, step);
            }
        });
        return {
            fragments: newChildren,
            finished: wrapperResult.finished,
        };
    }
    _executeInsertChildrenStep(step) {
        let newChildren = [...step.newElement.children];
        let wrapper = e.wrapChildren(step.newElement);
        let position = step.placement === 'before' ? 'afterbegin' : 'beforeend';
        step.oldElement.insertAdjacentElement(position, wrapper);
        let compilePromise = this._welcomeElement(wrapper, step);
        this._handleScroll(wrapper, step);
        let animatePromise = up.animate(wrapper, step.animation, {
            ...step,
            onFinished: () => {
                e.unwrap(wrapper);
                const focusElement = e.leadingElement(step.oldElement.childNodes) || step.oldElement;
                this._handleFocus(focusElement, step);
            }
        });
        return {
            fragments: newChildren,
            finished: Promise.all([compilePromise, animatePromise]),
        };
    }
    _welcomeElement(element, step) {
        this.responseDoc.finalizeElement(element);
        this.setReloadAttrs(step);
        return up.hello(element, step);
    }
    _preserveDescendantKeepables(step) {
        const descendantKeepPlans = [];
        if (step.keep) {
            for (let keepable of step.oldElement.querySelectorAll('[up-keep]')) {
                let keepPlan = up.fragment.keepPlan({ ...step, oldElement: keepable, descendantsOnly: true });
                if (keepPlan) {
                    const keepableClone = keepable.cloneNode(true);
                    keepable.insertAdjacentElement('beforebegin', keepableClone);
                    keepable.classList.add('up-keeping');
                    up.script.block(keepPlan.newElement);
                    let viewports = up.viewport.subtree(keepPlan.oldElement);
                    keepPlan.revivers = u.map(viewports, function (viewport) {
                        let cursorProps = up.viewport.copyCursorProps(viewport);
                        return () => up.viewport.copyCursorProps(cursorProps, viewport);
                    });
                    if (this._willChangeBody()) {
                        keepPlan.newElement.replaceWith(keepable);
                    }
                    else {
                        document.body.append(keepable);
                    }
                    descendantKeepPlans.push(keepPlan);
                }
            }
        }
        step.descendantKeepPlans = descendantKeepPlans;
    }
    _restoreDescendantKeepables(step) {
        for (let keepPlan of step.descendantKeepPlans) {
            keepPlan.newElement.replaceWith(keepPlan.oldElement);
            for (let reviver of keepPlan.revivers) {
                reviver();
            }
        }
    }
    _finalizeDescendantKeepables(step) {
        for (let keepPlan of step.descendantKeepPlans) {
            keepPlan.oldElement.classList.remove('up-keeping');
            up.fragment.emitKept(keepPlan);
        }
    }
    _willChangeBody() {
        return u.some(this._steps, (step) => step.oldElement.matches('body'));
    }
    _handleFocus(fragment, options) {
        const fragmentFocus = new up.FragmentFocus({
            ...options,
            fragment,
            autoMeans: up.fragment.config.autoFocus,
        });
        fragmentFocus.process(options.focus);
    }
    _handleScroll(fragment, options) {
        const scrolling = new up.FragmentScrolling({
            ...options,
            fragment,
            autoMeans: up.fragment.config.autoScroll
        });
        scrolling.process(options.scrollMap ?? options.scroll);
    }
};


/***/ }),
/* 32 */
/***/ (() => {

const u = up.util;
up.Change.CloseLayer = class CloseLayer extends up.Change {
    constructor(options) {
        super(options);
        this._verb = options.verb;
        this.layer = up.layer.get(options);
        this._origin = options.origin;
        this._value = options.value;
        this._preventable = options.preventable ?? true;
        this._response = options.response;
        this._history = options.history ?? true;
    }
    execute() {
        this.layer.assertAlive();
        up.browser.assertConfirmed(this.options);
        if (this._emitCloseEvent().defaultPrevented && this._preventable) {
            throw new up.Aborted('Close event was prevented');
        }
        this._emitClosingEvent();
        up.fragment.abort({ reason: 'Layer is closing', layer: this.layer });
        this.layer.state = 'closing';
        const { parent } = this.layer;
        this.layer.peel();
        this._handleFocus(parent);
        this.layer.teardownHandlers();
        this.layer.destroyElements(this.options);
        this.layer.stack.remove(this.layer);
        if (this._history) {
            parent.restoreHistory();
        }
        this.layer.state = 'closed';
        this._emitClosedEvent(parent);
    }
    _emitCloseEvent() {
        let event = this.layer.emit(this._buildEvent(`up:layer:${this._verb}`), {
            callback: this.layer.callback(`on${u.upperCaseFirst(this._verb)}`),
            log: [`Will ${this._verb} ${this.layer} with value %o`, this._value]
        });
        this._value = event.value;
        return event;
    }
    _emitClosingEvent() {
        let event = this._buildEvent(`up:layer:${this._verb}ing`);
        this.layer.emit(event, { log: false });
    }
    _emitClosedEvent(formerParent) {
        const verbPast = `${this._verb}ed`;
        const verbPastUpperCaseFirst = u.upperCaseFirst(verbPast);
        return this.layer.emit(this._buildEvent(`up:layer:${verbPast}`), {
            baseLayer: formerParent,
            callback: this.layer.callback(`on${verbPastUpperCaseFirst}`),
            ensureBubbles: true,
            log: [`${verbPastUpperCaseFirst} ${this.layer} with value %o`, this._value]
        });
    }
    _buildEvent(name) {
        return up.event.build(name, {
            layer: this.layer,
            value: this._value,
            origin: this._origin,
            response: this._response,
        });
    }
    _handleFocus(formerParent) {
        let hadFocus = this.layer.hasFocus();
        this.layer.overlayFocus.teardown();
        formerParent.overlayFocus?.moveToFront();
        if (hadFocus) {
            let newFocusElement = this.layer.origin || formerParent.element;
            up.focus(newFocusElement, { preventScroll: true });
        }
    }
};


/***/ }),
/* 33 */
/***/ (() => {

var _a;
const u = up.util;
up.Change.FromURL = (_a = class FromURL extends up.Change {
        async execute() {
            let newPageReason = this._newPageReason();
            if (newPageReason) {
                up.puts('up.render()', newPageReason);
                up.network.loadPage(this.options);
                return u.unresolvablePromise();
            }
            let requestAttrs = this._getRequestAttrs();
            let request = this.request = up.request(requestAttrs);
            this.options.onRequestKnown?.(request);
            if (this.options.preload)
                return request;
            this.options.handleAbort({ request, ...requestAttrs });
            request.runPreviews(this.options);
            return await u.always(request, (responseOrError) => this._onRequestSettled(responseOrError));
        }
        _newPageReason() {
            if (u.isCrossOrigin(this.options.url)) {
                return 'Loading cross-origin content in new page';
            }
            if (this.options.history && !up.browser.canPushState()) {
                return 'Loading content in new page to restore history support';
            }
        }
        _getRequestAttrs() {
            const successAttrs = this._preflightPropsForRenderOptions(this.options);
            const failAttrs = this._preflightPropsForRenderOptions(this.deriveFailOptions(), { optional: true });
            return {
                ...this.options,
                ...successAttrs,
                ...u.withRenamedKeys(failAttrs, up.fragment.failKey),
            };
        }
        getPreflightProps() {
            return this._getRequestAttrs();
        }
        _preflightPropsForRenderOptions(renderOptions, getPreflightPropsOptions) {
            const preflightChange = new up.Change.FromContent({ ...renderOptions, preflight: true });
            return preflightChange.getPreflightProps(getPreflightPropsOptions);
        }
        _onRequestSettled(response) {
            if (response instanceof up.Response) {
                return this._onRequestSettledWithResponse(response);
            }
            else {
                return this._onRequestSettledWithError(response);
            }
        }
        _onRequestSettledWithResponse(response) {
            return new up.Change.FromResponse({ ...this.options, response }).execute();
        }
        _onRequestSettledWithError(error) {
            if (error instanceof up.Offline) {
                let log = ['Cannot load fragment from %s: %s', error.request.description, error.reason];
                this.request.emit('up:fragment:offline', {
                    callback: this.options.onOffline,
                    renderOptions: this.options,
                    retry: (retryOptions) => up.render({ ...this.options, ...retryOptions }),
                    log,
                });
            }
            throw error;
        }
    },
    (() => {
        u.memoizeMethod(_a.prototype, {
            _getRequestAttrs: true,
        });
    })(),
    _a);


/***/ }),
/* 34 */
/***/ (() => {

var _a;
const u = up.util;
up.Change.FromResponse = (_a = class FromResponse extends up.Change {
        constructor(options) {
            super(options);
            this._response = options.response;
            this._request = this._response.request;
        }
        execute() {
            if (up.fragment.config.skipResponse(this._loadedEventProps())) {
                this._skip();
            }
            else {
                this._request.assertEmitted('up:fragment:loaded', {
                    ...this._loadedEventProps(),
                    callback: this.options.onLoaded,
                    log: ['Loaded fragment from %s', this._response.description],
                    skip: () => this._skip()
                });
                this._assetRenderableResponse();
            }
            let fail = u.evalOption(this.options.fail, this._response) ?? !this._response.ok;
            if (fail) {
                throw this._updateContentFromResponse(this.deriveFailOptions());
            }
            return this._updateContentFromResponse(this.options);
        }
        _assetRenderableResponse() {
            if (!up.fragment.config.renderableResponse(this._response)) {
                throw new up.CannotParse(['Cannot render response with content-type "%s" (configure with up.fragment.config.renderableResponse)', this._response.contentType]);
            }
        }
        _skip() {
            up.puts('up.render()', 'Skipping ' + this._response.description);
            this.options.target = ':none';
            this.options.failTarget = ':none';
        }
        _updateContentFromResponse(finalRenderOptions) {
            if (finalRenderOptions.didForceFailOptions) {
                up.puts('up.render()', 'Rendering failed response using fail-prefixed options (https://unpoly.com/failed-responses)');
            }
            this._augmentOptionsFromResponse(finalRenderOptions);
            finalRenderOptions.meta = this._helloMeta();
            finalRenderOptions.verifyFinished = (result) => this._revalidate(result, finalRenderOptions);
            return new up.Change.FromContent(finalRenderOptions).execute();
        }
        async _revalidate(renderResult, originalRenderOptions) {
            if (!up.fragment.shouldRevalidate(this._request, this._response, originalRenderOptions))
                return;
            let inputTarget = originalRenderOptions.target;
            let effectiveTarget = renderResult.target;
            if (/:(before|after)/.test(inputTarget)) {
                up.warn('up.render()', 'Cannot revalidate cache when prepending/appending (target %s)', inputTarget);
            }
            else {
                up.puts('up.render()', 'Revalidating cached response for target "%s"', effectiveTarget);
                let revalidateResult = await up.reload(effectiveTarget, {
                    ...originalRenderOptions,
                    ...up.RenderOptions.NO_MOTION,
                    ...up.RenderOptions.NO_INPUT_INTERFERENCE,
                    ...up.RenderOptions.NO_PREVIEWS,
                    feedback: originalRenderOptions.feedback,
                    preferOldElements: renderResult.fragments,
                    layer: renderResult.layer,
                    onFinished: null,
                    expiredResponse: this._response,
                    preview: this._revalidatePreview(originalRenderOptions),
                    abort: false,
                    cache: false,
                    background: true,
                });
                if (!revalidateResult.none) {
                    return revalidateResult;
                }
            }
        }
        _revalidatePreview({ preview, revalidatePreview }) {
            if (revalidatePreview === true) {
                return preview;
            }
            else {
                return revalidatePreview;
            }
        }
        _loadedEventProps() {
            const { expiredResponse } = this.options;
            return {
                request: this._request,
                response: this._response,
                renderOptions: this.options,
                revalidating: !!expiredResponse,
                expiredResponse,
            };
        }
        _helloMeta() {
            let meta = { revalidating: !!this.options.expiredResponse, ok: this._response.ok };
            up.migrate.processHelloMeta?.(meta, this._response);
            return meta;
        }
        _augmentOptionsFromResponse(renderOptions) {
            const responseURL = this._response.url;
            let serverLocation = responseURL;
            let hash = this._request.hash;
            if (hash) {
                renderOptions.hash = hash;
                serverLocation += hash;
            }
            const isReloadable = (this._response.method === 'GET');
            if (isReloadable) {
                renderOptions.source = up.history.refineOption(renderOptions.source, responseURL);
            }
            else {
                renderOptions.source = up.history.refineOption(renderOptions.source, 'keep');
                renderOptions.history = !!renderOptions.location;
            }
            let openLayerOptions = this._response.openLayer;
            if (openLayerOptions) {
                up.script.adoptRenderOptionsFromHeader(openLayerOptions, this._response.cspInfo);
                Object.assign(renderOptions, {
                    ...up.Layer.Overlay.UNSET_VISUALS,
                    target: undefined,
                    ...up.fragment.config.navigateOptions,
                    ...openLayerOptions,
                    layer: 'new',
                });
            }
            renderOptions.location = up.history.refineOption(renderOptions.location, serverLocation);
            renderOptions.title = up.history.refineOption(renderOptions.title, this._response.title);
            renderOptions.eventPlans = this._response.eventPlans;
            let serverTarget = this._response.target;
            if (serverTarget) {
                renderOptions.target = serverTarget;
            }
            renderOptions.acceptLayer = this._response.acceptLayer;
            renderOptions.dismissLayer = this._response.dismissLayer;
            renderOptions.document = this._response.text;
            if (this._response.none) {
                renderOptions.target = ':none';
            }
            renderOptions.context = u.merge(renderOptions.context, this._response.context);
            renderOptions.cspInfo = this._response.cspInfo;
            renderOptions.time ??= this._response.lastModified;
            renderOptions.etag ??= this._response.etag;
        }
    },
    (() => {
        u.memoizeMethod(_a.prototype, {
            _loadedEventProps: true,
        });
    })(),
    _a);


/***/ }),
/* 35 */
/***/ (() => {

var _a;
const u = up.util;
up.Change.FromContent = (_a = class FromContent extends up.Change {
        constructor(options) {
            super(options);
            this._origin = options.origin;
            this._preflight = options.preflight;
            this._layers = up.layer.getAll(options);
        }
        _getPlans() {
            let plans = [];
            this._filterLayers();
            this._improveOptionsFromResponseDoc();
            this._expandIntoPlans(plans, this._layers, this.options.target);
            this._expandIntoPlans(plans, this._layers, this.options.fallback);
            return plans;
        }
        _isRenderableLayer(layer) {
            return (layer === 'new') || layer.isAlive();
        }
        _filterLayers() {
            this._layers = u.filter(this._layers, this._isRenderableLayer);
        }
        _expandIntoPlans(plans, layers, targets) {
            for (let layer of layers) {
                for (let target of this._expandTargets(targets, layer)) {
                    const props = { ...this.options, target, layer, defaultPlacement: this._defaultPlacement() };
                    const change = layer === 'new' ? new up.Change.OpenLayer(props) : new up.Change.UpdateLayer(props);
                    plans.push(change);
                }
            }
        }
        _expandTargets(targets, layer) {
            return up.fragment.expandTargets(targets, { layer, mode: this.options.mode, origin: this._origin });
        }
        execute() {
            if (this.options.preload) {
                return Promise.resolve();
            }
            return this._seekPlan(this._executePlan.bind(this)) || this._cannotMatchPostflightTarget();
        }
        _executePlan(matchedPlan) {
            return up.fragment.mutate(() => matchedPlan.execute(this._getResponseDoc(), this._onPlanApplicable.bind(this, matchedPlan)));
        }
        _isApplicablePlanError(error) {
            return !(error instanceof up.CannotMatch);
        }
        _onPlanApplicable(plan) {
            let primaryPlan = this._getPlans()[0];
            if (plan !== primaryPlan) {
                up.puts('up.render()', 'Could not match primary target "%s". Updating a fallback target "%s".', primaryPlan.target, plan.target);
            }
            let { assets } = this._getResponseDoc();
            if (assets) {
                up.script.assertAssetsOK(assets, plan.options);
            }
            this.options.handleAbort(this.getPreflightProps());
        }
        _getResponseDoc() {
            if (this._preflight)
                return;
            const docOptions = u.pick(this.options, [
                'target',
                'content',
                'fragment',
                'document',
                'html',
                'cspInfo',
                'origin',
                'data',
            ]);
            up.migrate.handleResponseDocOptions?.(docOptions);
            if (this._defaultPlacement() === 'content') {
                docOptions.target = this._firstExpandedTarget(docOptions.target);
            }
            return new up.ResponseDoc(docOptions);
        }
        _improveOptionsFromResponseDoc() {
            if (this._preflight)
                return;
            let responseDoc = this._getResponseDoc();
            if (this.options.fragment) {
                this.options.target ||= responseDoc.rootSelector();
            }
            this.options.title = up.history.refineOption(this.options.title, responseDoc.title);
            this.options.metaTags = up.history.refineOption(this.options.metaTags, responseDoc.metaTags);
            this.options.lang = up.history.refineOption(this.options.lang, responseDoc.lang);
        }
        _defaultPlacement() {
            if (!this.options.document && !this.options.fragment) {
                return 'content';
            }
        }
        _firstExpandedTarget(target) {
            let layer = this._layers[0] || up.layer.root;
            return this._expandTargets(target || ':main', layer)[0];
        }
        getPreflightProps(opts = {}) {
            const getPlanProps = (plan) => plan.getPreflightProps();
            return this._seekPlan(getPlanProps) || opts.optional || this._cannotMatchPreflightTarget();
        }
        _cannotMatchPreflightTarget() {
            this._cannotMatchTarget('Could not find target in current page');
        }
        _cannotMatchPostflightTarget() {
            this._cannotMatchTarget('Could not find common target in current page and response');
        }
        _cannotMatchTarget(reason) {
            if (this._getPlans().length) {
                const planTargets = u.uniq(u.map(this._getPlans(), 'target'));
                const humanizedLayerOption = up.layer.optionToString(this.options.layer);
                throw new up.CannotMatch([reason + " (tried selectors %o in %s)", planTargets, humanizedLayerOption]);
            }
            else if (this._layers.length === 0) {
                this._cannotMatchLayer();
            }
            else if (this.options.didForceFailOptions) {
                throw new up.CannotMatch('No target selector given for failed responses (https://unpoly.com/failed-responses)');
            }
            else {
                throw new up.CannotMatch('No target selector given');
            }
        }
        _cannotMatchLayer() {
            throw new up.CannotMatch('Could not find a layer to render in. You may have passed an unmatchable layer reference, or a detached element.');
        }
        _seekPlan(fn) {
            for (let plan of this._getPlans()) {
                try {
                    return fn(plan);
                }
                catch (error) {
                    if (this._isApplicablePlanError(error)) {
                        throw error;
                    }
                }
            }
        }
    },
    (() => {
        u.memoizeMethod(_a.prototype, {
            _getPlans: true,
            _getResponseDoc: true,
            getPreflightProps: true,
        });
    })(),
    _a);


/***/ }),
/* 36 */
/***/ (() => {

const u = up.util;
const NONCE_PATTERN = /'nonce-([^']+)'/g;
function findNonces(cspPart) {
    let matches = cspPart.matchAll(NONCE_PATTERN);
    return u.map(matches, '1');
}
up.CSPInfo = class CSPInfo {
    constructor(declaration = '', nonces = []) {
        this.declaration = declaration;
        this.nonces = nonces;
    }
    isStrictDynamic() {
        return this.declaration.includes("'strict-dynamic'");
    }
    isUnsafeEval() {
        return this.declaration.includes("'unsafe-eval'");
    }
    static fromHeader(cspHeader) {
        let results = {};
        if (cspHeader) {
            let declarations = cspHeader.split(/\s*;\s*/);
            for (let declaration of declarations) {
                let directive = declaration.match(/^(script|default)-src\s/)?.[1];
                if (directive) {
                    results[directive] = [declaration, findNonces(declaration)];
                }
            }
        }
        let bestResult = results.script || results.default;
        if (bestResult) {
            return new this(...bestResult);
        }
        else {
            return this.none();
        }
    }
    static none() {
        return new this();
    }
};


/***/ }),
/* 37 */
/***/ (() => {

const u = up.util;
up.HelloFragment = class HelloFragment {
    constructor(root, macros, compilers, { layer, data, dataRoot, dataMap, meta, insertedEvent }) {
        layer ||= up.layer.get(root) || up.layer.current;
        this._root = root;
        this._macros = macros;
        this._compilers = compilers;
        this._layer = layer;
        this._data = data;
        this._dataRoot = dataRoot || root;
        this._dataMap = dataMap;
        this._compilePromises = [];
        this._insertedEvent = insertedEvent ?? true;
        meta ||= {};
        meta.layer ??= layer;
        meta.ok ??= true;
        meta.revalidating ??= false;
        this._meta = meta;
    }
    async run() {
        up.puts('up.hello()', "Compiling fragment %o", this._root);
        this._assignDataToElements();
        this._runCompilers(this._macros);
        this._emitCompileEvent();
        this._runCompilers(this._compilers);
        this._emitInsertedEvent();
        await Promise.all(this._compilePromises);
        return this._root;
    }
    _emitCompileEvent() {
        up.emit(this._root, 'up:compilers:before', { log: false });
    }
    _emitInsertedEvent() {
        if (this._insertedEvent) {
            up.fragment.emitInserted(this._root, this._meta);
        }
    }
    _assignDataToElements() {
        if (this._data) {
            this._dataRoot.upCompileData = this._data;
        }
        if (this._dataMap) {
            for (let selector in this._dataMap) {
                for (let match of this._select(selector)) {
                    match.upCompileData = this._dataMap[selector];
                }
            }
        }
    }
    _runCompilers(compilers) {
        this._layer.asCurrent(() => {
            for (let compiler of compilers) {
                this._runCompiler(compiler);
            }
        });
    }
    _runCompiler(compiler) {
        const matches = this._selectOnce(compiler);
        if (!matches.length) {
            return;
        }
        if (!compiler.isDefault) {
            up.puts('up.hello()', 'Compiling %d× "%s" on %s', matches.length, compiler.selector, this._layer);
        }
        if (compiler.batch) {
            this._compileBatch(compiler, matches);
        }
        else {
            for (let match of matches) {
                this._compileOneElement(compiler, match);
            }
        }
        up.migrate.postCompile?.(matches, compiler);
    }
    _compileOneElement(compiler, element) {
        const compileArgs = [element];
        if (compiler.length !== 1) {
            const data = up.script.data(element);
            compileArgs.push(data, this._meta);
        }
        let onDestructor = (destructor) => up.destructor(element, destructor);
        this._applyCompilerFunction(compiler, element, compileArgs, onDestructor);
    }
    _compileBatch(compiler, elements) {
        const compileArgs = [elements];
        if (compiler.length !== 1) {
            const dataList = u.map(elements, up.script.data);
            compileArgs.push(dataList, this._meta);
        }
        let onDestructor = () => this._reportBatchCompilerWithDestructor(compiler);
        this._applyCompilerFunction(compiler, elements, compileArgs, onDestructor);
    }
    async _applyCompilerFunction(compiler, elementOrElements, compileArgs, onDestructor) {
        let maybeDestructor = up.error.guard(() => compiler.apply(elementOrElements, compileArgs));
        if (u.isPromise(maybeDestructor)) {
            let guardedPromise = up.error.guardPromise(maybeDestructor);
            this._compilePromises.push(guardedPromise);
            maybeDestructor = await guardedPromise;
        }
        if (maybeDestructor)
            onDestructor(maybeDestructor);
    }
    _reportBatchCompilerWithDestructor(compiler) {
        let error = new up.Error(['Batch compiler (%s) cannot return a destructor', compiler.selector]);
        reportError(error);
    }
    _select(selector) {
        return up.fragment.subtree(this._root, u.evalOption(selector), { layer: this._layer });
    }
    _selectOnce(compiler) {
        let matches = this._select(compiler.selector);
        if (!compiler.rerun) {
            matches = u.filter(matches, (element) => {
                let appliedCompilers = (element.upAppliedCompilers ||= new Set());
                if (!appliedCompilers.has(compiler)) {
                    appliedCompilers.add(compiler);
                    return true;
                }
            });
        }
        return matches;
    }
};


/***/ }),
/* 38 */
/***/ (() => {

const u = up.util;
up.DestructorPass = class DestructorPass {
    constructor(fragment, options) {
        this._fragment = fragment;
        this._options = options;
    }
    run() {
        for (let cleanable of this._selectCleanables()) {
            let registry = u.pluckKey(cleanable, 'upDestructors');
            registry?.clean(cleanable);
        }
    }
    _selectCleanables() {
        const selectOptions = { ...this._options, destroying: true };
        return up.fragment.subtree(this._fragment, '.up-can-clean', selectOptions);
    }
};


/***/ }),
/* 39 */
/***/ (() => {

const u = up.util;
const e = up.element;
up.EventEmitter = class EventEmitter extends up.Record {
    keys() {
        return [
            'target',
            'event',
            'baseLayer',
            'callback',
            'log',
            'ensureBubbles',
        ];
    }
    emit() {
        this._logEmission();
        if (this.baseLayer) {
            this.baseLayer.asCurrent(() => this._dispatchEvent());
        }
        else {
            this._dispatchEvent();
        }
        return this.event;
    }
    _dispatchEvent() {
        this.target.dispatchEvent(this.event);
        if (this.ensureBubbles && !this.target.isConnected) {
            document.dispatchEvent(this.event);
        }
        up.error.guard(() => this.callback?.(this.event));
    }
    assertEmitted() {
        const event = this.emit();
        if (event.defaultPrevented) {
            throw new up.Aborted(`Event ${event.type} was prevented`);
        }
    }
    _logEmission() {
        if (!up.log.config.enabled) {
            return;
        }
        let message = this.log;
        let messageArgs;
        if (u.isArray(message)) {
            [message, ...messageArgs] = message;
        }
        else {
            messageArgs = [];
        }
        const { type } = this.event;
        if (u.isString(message)) {
            up.puts(type, message, ...messageArgs);
        }
        else if (message !== false) {
            up.puts(type, `Event ${type}`);
        }
    }
    static fromEmitArgs(args, defaults = {}) {
        let options = u.extractOptions(args);
        options = u.merge(defaults, options);
        if (u.isElementLike(args[0])) {
            options.target = e.get(args.shift());
        }
        else if (args[0] instanceof up.Layer) {
            options.layer = args.shift();
        }
        let layer;
        if (u.isGiven(options.layer)) {
            layer = up.layer.get(options.layer);
            options.target ||= layer.element;
            options.baseLayer ||= layer;
        }
        if (options.baseLayer) {
            options.baseLayer = up.layer.get(options.baseLayer);
        }
        if (u.isString(options.target)) {
            options.target = up.fragment.get(options.target, { layer: options.layer });
        }
        else if (!options.target) {
            options.target = document;
        }
        if (args[0]?.preventDefault) {
            options.event = args[0];
            options.log ??= args[0].log;
        }
        else if (u.isString(args[0])) {
            options.event = up.event.build(args[0], options);
        }
        else {
            options.event = up.event.build(options);
        }
        return new (this)(options);
    }
};


/***/ }),
/* 40 */
/***/ (() => {

const u = up.util;
up.EventListener = class EventListener extends up.Record {
    keys() {
        return [
            'element',
            'eventType',
            'selector',
            'callback',
            'guard',
            'baseLayer',
            'passive',
            'once',
            'capture',
            'beforeBoot',
        ];
    }
    constructor(attributes) {
        super(attributes);
        this._key = this.constructor._buildKey(attributes);
        this.isDefault = up.framework.evaling;
        this.beforeBoot ??= (this.eventType.indexOf('up:framework:') === 0);
        this.nativeCallback = this.nativeCallback.bind(this);
    }
    bind() {
        const map = (this.element.upEventListeners ||= {});
        if (map[this._key]) {
            up.fail('up.on(): The %o callback %o cannot be registered more than once', this.eventType, this.callback);
        }
        map[this._key] = this;
        this.element.addEventListener(...this._addListenerArg());
    }
    _addListenerArg() {
        let options = u.compactObject(u.pick(this, ['once', 'passive', 'capture']));
        return [this.eventType, this.nativeCallback, options];
    }
    unbind() {
        let map = this.element.upEventListeners;
        if (map) {
            delete map[this._key];
        }
        this.element.removeEventListener(...this._addListenerArg());
    }
    nativeCallback(event) {
        if (up.framework.beforeBoot && !this.beforeBoot) {
            return;
        }
        let element = event.target;
        if (this.selector) {
            let selector = u.evalOption(this.selector);
            element = element.closest(selector);
        }
        if (this.guard && !this.guard(event)) {
            return;
        }
        if (element) {
            const args = [event, element];
            const expectedArgCount = this.callback.length;
            if (expectedArgCount !== 1 && expectedArgCount !== 2) {
                const data = up.script.data(element);
                args.push(data);
            }
            if (this.eventType === 'click' && element.disabled) {
                return;
            }
            const applyCallback = this.callback.bind(element, ...args);
            if (this.baseLayer) {
                this.baseLayer.asCurrent(applyCallback);
            }
            else {
                applyCallback();
            }
        }
    }
    static fromElement(attributes) {
        let map = attributes.element.upEventListeners;
        if (map) {
            const key = this._buildKey(attributes);
            return map[key];
        }
    }
    static _buildKey(attributes) {
        attributes.callback.upUid ||= u.uid();
        return [
            attributes.eventType,
            attributes.selector,
            attributes.callback.upUid
        ].join('|');
    }
    static allNonDefault(element) {
        let map = element.upEventListeners;
        if (map) {
            const listeners = Object.values(map);
            return u.reject(listeners, 'isDefault');
        }
        else {
            return [];
        }
    }
};


/***/ }),
/* 41 */
/***/ (() => {

const u = up.util;
up.EventListenerGroup = class EventListenerGroup extends up.Record {
    keys() {
        return [
            'elements',
            'eventTypes',
            'selector',
            'callback',
            'guard',
            'baseLayer',
            'passive',
            'once',
            'capture',
            'beforeBoot',
        ];
    }
    bind() {
        const cleaner = u.cleaner();
        this._eachListenerAttributes(function (attrs) {
            const listener = new up.EventListener(attrs);
            listener.bind();
            return cleaner(listener.unbind.bind(listener));
        });
        return cleaner.clean;
    }
    _eachListenerAttributes(fn) {
        for (let element of this.elements) {
            for (let eventType of this.eventTypes) {
                fn(this._listenerAttributes(element, eventType));
            }
        }
    }
    _listenerAttributes(element, eventType) {
        return { ...this.attributes(), element, eventType };
    }
    unbind() {
        this._eachListenerAttributes(function (attrs) {
            let listener = up.EventListener.fromElement(attrs);
            if (listener) {
                listener.unbind();
            }
        });
    }
    static fromBindArgs(args, overrides) {
        args = u.copy(args);
        const callback = args.pop();
        let elements;
        if (args[0].addEventListener) {
            elements = [args.shift()];
        }
        else if (u.isJQuery(args[0]) || (u.isList(args[0]) && args[0][0].addEventListener)) {
            elements = args.shift();
        }
        else {
            elements = [document];
        }
        let eventTypes = u.getSimpleTokens(args.shift());
        let fixTypes = up.migrate.fixEventTypes;
        if (fixTypes) {
            eventTypes = fixTypes(eventTypes);
        }
        const options = u.extractOptions(args);
        const selector = args[0];
        const attributes = { elements, eventTypes, selector, callback, ...options, ...overrides };
        return new (this)(attributes);
    }
};


/***/ }),
/* 42 */
/***/ (() => {

const u = up.util;
up.SelectorTracker = class SelectorTracker {
    constructor(selector, options, addCallback) {
        this._selector = selector;
        this._addCallback = addCallback;
        this._layer = options.layer || 'any';
        this._filter = options.filter || u.identity;
        this._knownMatches = new Map();
        this._syncScheduled = false;
    }
    start() {
        this._sync();
        return u.sequence(this._trackFragments(), () => this._removeAllMatches());
    }
    _trackFragments() {
        return up.on('up:fragment:inserted up:fragment:destroyed', () => this._scheduleSync());
    }
    _scheduleSync() {
        if (!this._syncScheduled) {
            this._syncScheduled = true;
            up.fragment.afterMutate(() => this._sync());
        }
    }
    _sync() {
        this._syncScheduled = false;
        let removeMap = new Map(this._knownMatches);
        this._knownMatches.clear();
        for (let newMatch of this._currentMatches) {
            let knownRemoveCallback = removeMap.get(newMatch);
            removeMap.delete(newMatch);
            let removeCallback = knownRemoveCallback || this._addCallback(newMatch) || u.noop;
            this._knownMatches.set(newMatch, removeCallback);
        }
        this._runRemoveCallbacks(removeMap);
    }
    get _currentMatches() {
        let allMatches = up.fragment.all(this._selector, { layer: this._layer });
        return this._filter(allMatches);
    }
    _removeAllMatches() {
        this._runRemoveCallbacks(this._knownMatches);
    }
    _runRemoveCallbacks(map) {
        for (let [element, removeCallback] of map) {
            removeCallback(element);
        }
    }
};


/***/ }),
/* 43 */
/***/ (() => {

const u = up.util;
up.FieldWatcher = class FieldWatcher {
    constructor(root, options, callback) {
        this._options = options;
        this._root = root;
        this._callback = callback;
        this._batch = options.batch;
        this._logPrefix = options.logPrefix ?? 'up.watch()';
        this._includeDisabled = options.includeDisabled;
        this._ensureWatchable();
    }
    start() {
        this._scheduledValues = null;
        this._processedValues = this._readFieldValues();
        this._currentTimer = null;
        this._callbackRunning = false;
        return u.sequence(this._trackFields(), this._trackAbort(), this._trackReset(), () => this._abort());
    }
    _ensureWatchable() {
        const fail = (message) => up.fail(message, this._logPrefix, this._root);
        if (!this._callback) {
            fail('No callback provided for %s (%o)');
        }
        if (this._root.matches('input[type=radio]')) {
            fail('Use %s with the container of a radio group, not with an individual radio button (%o)');
        }
        if (up.form.isField(this._root) && !this._root.name) {
            fail('%s can only watch fields with a name (%o)');
        }
    }
    _trackFields() {
        if (up.form.isField(this._root)) {
            return this._watchField(this._root);
        }
        else {
            return up.form.trackFields(this._root, (field) => this._watchField(field));
        }
    }
    _trackAbort() {
        let guard = ({ target }) => target.contains(this._region);
        return up.on('up:fragment:aborted', { guard }, () => this._abort());
    }
    _trackReset() {
        let guard = ({ target }) => target === this._region;
        return up.on('reset', { guard }, (event) => this._onFormReset(event));
    }
    get _region() {
        return up.form.getRegion(this._root);
    }
    _fieldOptions(field) {
        let rootOptions = u.copy(this._options);
        return up.form.watchOptions(field, rootOptions, { defaults: { event: 'input' } });
    }
    _watchField(field) {
        let fieldOptions = this._fieldOptions(field);
        let eventType = fieldOptions.event;
        return up.on(field, eventType, (event) => this._check(event, fieldOptions));
    }
    _abort() {
        this._scheduledValues = null;
    }
    _scheduleValues(values, fieldOptions) {
        this._scheduledValues = values;
        this._scheduledFieldOptions = fieldOptions;
        let delay = fieldOptions.delay || 0;
        clearTimeout(this._currentTimer);
        this._currentTimer = u.timer(delay, () => {
            this._currentTimer = null;
            this._requestCallback();
        });
    }
    _isNewValues(values) {
        return !u.isEqual(values, this._processedValues) && !u.isEqual(this._scheduledValues, values);
    }
    async _requestCallback() {
        if (!this._scheduledValues)
            return;
        if (this._callbackRunning)
            return;
        if (this._currentTimer)
            return;
        if (!up.fragment.isAlive(this._region))
            return;
        let callbackOptions = u.omit(this._scheduledFieldOptions, ['event', 'delay']);
        const diff = this._changedValues(this._processedValues, this._scheduledValues);
        this._processedValues = this._scheduledValues;
        this._scheduledValues = null;
        this._callbackRunning = true;
        this._scheduledFieldOptions = null;
        const callbackReturnValues = [];
        if (this._batch) {
            callbackReturnValues.push(this._runCallback(diff, callbackOptions));
        }
        else {
            for (let name in diff) {
                const value = diff[name];
                callbackReturnValues.push(this._runCallback(value, name, callbackOptions));
            }
        }
        if (u.some(callbackReturnValues, u.isPromise)) {
            let callbackDone = Promise.allSettled(callbackReturnValues);
            await callbackDone;
        }
        this._callbackRunning = false;
        this._requestCallback();
    }
    _runCallback(...args) {
        return up.error.guard(this._callback, ...args);
    }
    _changedValues(previous, next) {
        const changes = {};
        let keys = Object.keys(previous);
        keys = keys.concat(Object.keys(next));
        keys = u.uniq(keys);
        for (let key of keys) {
            const previousValue = previous[key];
            const nextValue = next[key];
            if (!u.isEqual(previousValue, nextValue)) {
                changes[key] = nextValue;
            }
        }
        return changes;
    }
    _readFieldValues() {
        return up.Params.fromContainer(this._root, { includeDisabled: this._includeDisabled }).toObject();
    }
    _check(event, fieldOptions = {}) {
        const values = this._readFieldValues();
        if (this._isNewValues(values)) {
            up.log.putsEvent(event);
            this._scheduleValues(values, fieldOptions);
        }
    }
    _onFormReset(event) {
        u.task(() => this._check(event));
    }
};


/***/ }),
/* 44 */
/***/ (() => {

const u = up.util;
const e = up.element;
const BUILTIN_SWITCH_EFFECTS = [
    { attr: 'up-hide-for', toggle(target, active) { e.toggle(target, !active); } },
    { attr: 'up-show-for', toggle(target, active) { e.toggle(target, active); } },
    { attr: 'up-disable-for', toggle(target, active) { up.form.setDisabled(target, active); } },
    { attr: 'up-enable-for', toggle(target, active) { up.form.setDisabled(target, !active); } },
];
up.Switcher = class Switcher {
    constructor(root) {
        this._root = root;
        this._switcheeSelector = root.getAttribute('up-switch') || up.fail("No switch target given for %o", root);
        this._regionSelector = root.getAttribute('up-switch-region');
    }
    start() {
        this._switchRegion();
        return u.sequence(this._trackFieldChanges(), this._trackNewSwitchees());
    }
    _trackFieldChanges() {
        let callback = () => this._onFieldChanged();
        return up.migrate.watchForSwitch?.(this._root, callback)
            || up.watch(this._root, { logPrefix: '[up-switch]', includeDisabled: true }, callback);
    }
    _trackNewSwitchees() {
        let filter = (matches) => {
            let scope = this._scope;
            return u.filter(matches, (match) => scope?.contains(match));
        };
        let onSwitcheeAdded = (switchee) => this._switchSwitchee(switchee);
        return up.fragment.trackSelector(this._switcheeSelector, { filter }, onSwitcheeAdded);
    }
    _onFieldChanged() {
        this._switchRegion();
    }
    _switchRegion() {
        const fieldTokens = this._buildFieldTokens();
        for (let switchee of this._findSwitchees()) {
            this._switchSwitchee(switchee, fieldTokens);
        }
    }
    _switchSwitchee(switchee, fieldTokens = this._buildFieldTokens()) {
        let previousValues = switchee.upSwitchValues;
        if (!u.isEqual(previousValues, fieldTokens)) {
            switchee.upSwitchValues = fieldTokens;
            this._switchSwitcheeNow(switchee, fieldTokens);
        }
    }
    _switchSwitcheeNow(switchee, fieldTokens) {
        for (let { attr, toggle } of BUILTIN_SWITCH_EFFECTS) {
            let attrValue = switchee.getAttribute(attr);
            if (attrValue) {
                let activeTokens = this._parseSwitcheeTokens(attrValue);
                let isActive = u.intersect(fieldTokens, activeTokens).length > 0;
                toggle(switchee, isActive);
            }
        }
        let log = ['Switching %o', switchee];
        up.emit(switchee, 'up:form:switch', { field: this._root, fieldTokens, log });
    }
    _findSwitchees() {
        let scope = this._scope;
        return scope ? up.fragment.subtree(scope, this._switcheeSelector) : [];
    }
    get _scope() {
        if (this._regionSelector) {
            return up.fragment.get(this._regionSelector, { origin: this._root });
        }
        else {
            return up.form.getRegion(this._root);
        }
    }
    _parseSwitcheeTokens(str) {
        return u.getSimpleTokens(str, { json: true });
    }
    _buildFieldTokens() {
        let values = up.Params.fromContainer(this._root, { includeDisabled: true }).values();
        let tokens = [...values];
        let anyPresent = u.some(values, u.isPresent);
        tokens.push(anyPresent ? ':present' : ':blank');
        let fields = up.form.fields(this._root);
        if (fields[0]?.matches('[type=radio], [type=checkbox]')) {
            let anyChecked = u.some(fields, 'checked');
            tokens.push(anyChecked ? ':checked' : ':unchecked');
        }
        return tokens;
    }
};


/***/ }),
/* 45 */
/***/ (() => {

const u = up.util;
const e = up.element;
up.FormValidator = class FormValidator {
    constructor(form) {
        this._form = form;
        this._dirtySolutions = [];
        this._nextRenderTimer = null;
        this._rendering = false;
        this._honorAbort();
    }
    start() {
        let guard = (field) => this._isValidatingField(field);
        let callback = (field) => this._onFieldAdded(field);
        return up.form.trackFields(this._form, { guard }, callback);
    }
    _isValidatingField(field) {
        return field.closest('[up-validate]:not([up-validate=false])');
    }
    _onFieldAdded(field) {
        let eventType = up.form.validateOptions(field).event;
        return up.on(field, eventType, (event) => {
            if (!field.closest('.up-keeping')) {
                up.log.putsEvent(event);
                up.error.muteUncriticalRejection(this.validate({ origin: field }));
            }
        });
    }
    _honorAbort() {
        up.fragment.onAborted(this._form, (event) => this._onAborted(event));
    }
    _onAborted(event) {
        let abortedError = new up.Aborted(event.reason);
        let solution;
        while (solution = this._dirtySolutions.shift()) {
            solution.deferred.reject(abortedError);
        }
    }
    validate(options = {}) {
        let newSolutions = this._getSolutions(options);
        this._dirtySolutions.push(...newSolutions);
        this._scheduleNextRender();
        return newSolutions[0]?.deferred;
    }
    _getSolutions(options) {
        let solutions = this._getTargetSelectorSolutions(options)
            || this._getFieldSolutions(options)
            || this._getElementSolutions(options.origin);
        let deferred = u.newDeferred();
        for (let solution of solutions) {
            let renderOptions = up.form.validateOptions(solution.origin, options);
            solution.batch = u.pluckKey(renderOptions, 'batch');
            solution.renderOptions = renderOptions;
            solution.destination = `${renderOptions.method} ${renderOptions.url}`;
            solution.target = up.fragment.resolveOrigin(solution.target, solution);
            solution.deferred = deferred;
        }
        return solutions;
    }
    _getFieldSolutions({ origin, ...options }) {
        if (up.form.isField(origin)) {
            return this._getValidateAttrSolutions(origin) || this._getFormGroupSolutions(origin, options);
        }
    }
    _getFormGroupSolutions(field, { formGroup = true }) {
        if (!formGroup)
            return;
        let solution = up.form.groupSolution(field);
        if (solution) {
            up.puts('up.validate()', 'Validating form group of field %o', field);
            return [solution];
        }
    }
    _getTargetSelectorSolutions({ target, origin }) {
        if (u.isString(target)) {
            up.puts('up.validate()', 'Validating target "%s"', target);
            let simpleSelectors = up.fragment.splitTarget(target);
            return u.compact(simpleSelectors.map(function (simpleSelector) {
                let element = up.fragment.get(simpleSelector, { origin });
                if (element) {
                    return {
                        element,
                        target: simpleSelector,
                        origin
                    };
                }
                else {
                    up.fail('Validation target "%s" does not match an element', simpleSelector);
                }
            }));
        }
    }
    _getElementSolutions(element) {
        up.puts('up.validate()', 'Validating element %o', element);
        return [{
                element,
                target: up.fragment.toTarget(element),
                origin: element
            }];
    }
    _getValidateAttrSolutions(field) {
        let containerWithAttr = field.closest('[up-validate]');
        if (containerWithAttr) {
            let target = e.booleanOrStringAttr(containerWithAttr, 'up-validate');
            return this._getTargetSelectorSolutions({ target, origin: field });
        }
    }
    _scheduleNextRender() {
        let solutionDelays = this._dirtySolutions.map((solution) => solution.renderOptions.delay);
        let shortestDelay = Math.min(...solutionDelays) || 0;
        clearTimeout(this._nextRenderTimer);
        this._nextRenderTimer = u.timer(shortestDelay, () => {
            this._nextRenderTimer = null;
            this._renderDirtySolutions();
        });
    }
    _renderDirtySolutions() {
        up.error.muteUncriticalRejection(this._doRenderDirtySolutions());
    }
    async _doRenderDirtySolutions() {
        if (!this._dirtySolutions.length)
            return;
        if (this._rendering)
            return;
        if (this._nextRenderTimer)
            return;
        let solutionsBatch = this._selectDirtySolutionsBatch();
        let renderOptions = this._mergeRenderOptions(solutionsBatch);
        this._rendering = true;
        try {
            let renderPromise = up.render(renderOptions);
            for (let solution of solutionsBatch) {
                solution.deferred.resolve(renderPromise);
            }
            await renderPromise;
        }
        finally {
            this._rendering = false;
            this._renderDirtySolutions();
        }
    }
    _selectDirtySolutionsBatch() {
        let batch = [];
        let i = 0;
        while (i < this._dirtySolutions.length) {
            let solution = this._dirtySolutions[i];
            if (batch.length === 0 || this._canBatchSolutions(batch[0], solution)) {
                batch.push(solution);
                this._dirtySolutions.splice(i, 1);
            }
            else {
                i++;
            }
        }
        return batch;
    }
    _canBatchSolutions(s1, s2) {
        return s1.destination === s2.destination && s1.batch && s2.batch;
    }
    _mergeRenderOptions(dirtySolutions) {
        let dirtyOrigins = u.map(dirtySolutions, 'origin');
        let dirtyFields = u.flatMap(dirtyOrigins, up.form.fields);
        let dirtyNames = u.uniq(u.map(dirtyFields, 'name'));
        let dirtyRenderOptionsList = u.map(dirtySolutions, 'renderOptions');
        let formDestinationOptions = up.form.destinationOptions(this._form);
        let options = u.mergeDefined(formDestinationOptions, ...dirtyRenderOptionsList);
        options.target = u.map(dirtySolutions, 'target').join(', ');
        options.origin = this._form;
        options.focus ??= 'keep';
        options.failOptions = false;
        options.defaultMaybe = true;
        options.params = up.Params.merge(formDestinationOptions.params, ...u.map(dirtyRenderOptionsList, 'params'));
        options.headers = u.merge(formDestinationOptions.headers, ...u.map(dirtyRenderOptionsList, 'headers'));
        this._addValidateHeader(options.headers, dirtyNames);
        options.feedback = u.some(dirtyRenderOptionsList, 'feedback');
        options.data = undefined;
        options.dataMap = u.mapObject(dirtySolutions, ({ target, element, renderOptions: { data, keepData } }) => [
            target,
            keepData ? up.data(element) : data
        ]);
        options.preview = undefined;
        options.previewMap = u.mapObject(dirtySolutions, ({ target, renderOptions: { preview } }) => [target, preview]);
        options.placeholder = undefined;
        options.placeholderMap = u.mapObject(dirtySolutions, ({ target, renderOptions: { placeholder } }) => [target, placeholder]);
        options.disable = dirtySolutions.map((solution) => up.fragment.resolveOrigin(solution.renderOptions.disable, solution));
        options.guardEvent = up.event.build('up:form:validate', {
            fields: dirtyFields,
            log: 'Validating form',
            params: options.params,
            form: this._form,
        });
        return options;
    }
    _addValidateHeader(headers, names) {
        let key = up.protocol.headerize('validate');
        let value = names.join(' ');
        if (!value || value.length > up.protocol.config.maxHeaderSize)
            value = ':unknown';
        headers[key] = value;
    }
};


/***/ }),
/* 46 */
/***/ (() => {

up.FocusCapsule = class FocusCapsule {
    constructor(element, target) {
        this._element = element;
        this._target = target;
        this._cursorProps = up.viewport.copyCursorProps(this._element);
    }
    wasLost() {
        return document.activeElement !== this._element && !this._voided;
    }
    autoVoid() {
        up.on('focusin', { once: true }, () => this._voided = true);
    }
    restore(layer, focusOptions) {
        if (!this.wasLost()) {
            return false;
        }
        let rediscoveredElement = up.fragment.get(this._target, { layer });
        if (rediscoveredElement) {
            up.viewport.copyCursorProps(this._cursorProps, rediscoveredElement);
            up.focus(rediscoveredElement, focusOptions);
            return true;
        }
    }
    static preserve(layer) {
        let focusedElement = up.viewport.focusedElementWithin(layer.element);
        if (!focusedElement)
            return;
        let target = up.fragment.tryToTarget(focusedElement);
        if (!target)
            return;
        return new this(focusedElement, target);
    }
};


/***/ }),
/* 47 */
/***/ (() => {

const u = up.util;
up.FragmentProcessor = class FragmentProcessor extends up.Record {
    keys() {
        return [
            'fragment',
            'autoMeans',
            'origin',
            'layer'
        ];
    }
    process(opt) {
        let preprocessed = this.preprocessOnce(opt);
        return this.tryProcess(preprocessed);
    }
    preprocessOnce(opt) {
        return u.getComplexTokens(opt);
    }
    tryProcess(opt) {
        if (u.isArray(opt)) {
            return this.processArray(opt);
        }
        if (u.isOptions(opt)) {
            return this.processSelectorMap(opt);
        }
        if (u.isFunction(opt)) {
            let result = up.error.guard(opt, this.fragment, this.attributes());
            return this.tryProcess(result);
        }
        if (u.isElement(opt)) {
            return this.processElement(opt);
        }
        if (u.isString(opt)) {
            if (opt === 'auto') {
                return this.tryProcess(this.autoMeans);
            }
            let match = opt.match(/^(.+?)-if-(.+?)$/);
            if (match) {
                return this.resolveCondition(match[2]) && this.tryProcess(match[1]);
            }
        }
        return this.processPrimitive(opt);
    }
    processSelectorMap(map) {
        return Object.keys(map).filter((selector) => {
            let match = this.findSelector(selector);
            if (match) {
                let matchProcessor = new this.constructor({ ...this.attributes(), fragment: match });
                let opt = map[selector];
                return matchProcessor.process(opt);
            }
        });
    }
    processArray(array) {
        return u.find(array, (opt) => this.tryProcess(opt));
    }
    resolveCondition(condition) {
        if (condition === 'main') {
            return this.fragment && up.fragment.contains(this.fragment, ':main');
        }
    }
    findSelector(selector) {
        const lookupOpts = { layer: this.layer, origin: this.origin };
        let matchWithinFragment = this.fragment && up.fragment.get(this.fragment, selector, lookupOpts);
        let match = matchWithinFragment || up.fragment.get(selector, lookupOpts);
        if (match) {
            return match;
        }
        else {
            up.warn('up.render()', 'Could not find an element matching "%s"', selector);
        }
    }
};


/***/ }),
/* 48 */
/***/ (() => {

const u = up.util;
const DESCENDANT_SELECTOR = /^([^ >+(]+) (.+)$/;
up.FragmentFinder = class FragmentFinder {
    constructor(options) {
        this._options = options;
        this._origin = options.origin;
        this._selector = options.selector;
        this._document = options.document || window.document;
        this._match = options.match ?? up.fragment.config.match;
        this._preferOldElements = options.preferOldElements;
    }
    find() {
        return this._findInPreferredElements() || this._findInRegion() || this._findFirst();
    }
    _findInPreferredElements() {
        if (this._preferOldElements) {
            return this._preferOldElements.find((preferOldElement) => this._document.contains(preferOldElement) && up.fragment.matches(preferOldElement, this._selector));
        }
    }
    _findInRegion() {
        if (this._match === 'region' && !up.fragment.containsMainPseudo(this._selector) && this._origin?.isConnected) {
            return this._findClosest() || this._findDescendantInRegion();
        }
    }
    _findClosest() {
        return up.fragment.closest(this._origin, this._selector, this._options);
    }
    _findDescendantInRegion() {
        let simpleSelectors = up.fragment.splitTarget(this._selector);
        return u.findResult(simpleSelectors, (simpleSelector) => {
            let parts = simpleSelector.match(DESCENDANT_SELECTOR);
            if (parts) {
                let parent = up.fragment.closest(this._origin, parts[1], this._options);
                if (parent) {
                    return up.fragment.getFirstDescendant(parent, parts[2]);
                }
            }
        });
    }
    _findFirst() {
        return up.fragment.getFirstDescendant(this._document, this._selector, this._options);
    }
};


/***/ }),
/* 49 */
/***/ (() => {

const u = up.util;
const e = up.element;
const PREVENT_SCROLL_OPTIONS = { preventScroll: true };
up.FragmentFocus = class FragmentFocus extends up.FragmentProcessor {
    keys() {
        return super.keys().concat([
            'hash',
            'focusVisible',
            'focusCapsule',
            'inputDevice',
        ]);
    }
    processPrimitive(opt) {
        switch (opt) {
            case 'keep':
                return this._restoreLostFocus();
            case 'restore':
                return this._restorePreviousFocusForLocation();
            case 'target':
            case true:
                return this._focusElement(this.fragment);
            case 'layer':
                return this._focusElement(this.layer.getFocusElement());
            case 'main':
                return this._focusSelector(':main');
            case 'hash':
                return this._focusHash();
            case 'autofocus':
                return this._autofocus();
            default:
                if (u.isString(opt)) {
                    return this._focusSelector(opt);
                }
        }
    }
    processElement(element) {
        return this._focusElement(element);
    }
    resolveCondition(condition) {
        if (condition === 'lost') {
            return this._wasFocusLost();
        }
        else {
            return super.resolveCondition(condition);
        }
    }
    _focusSelector(selector) {
        let match = this.findSelector(selector);
        return this._focusElement(match);
    }
    _restoreLostFocus() {
        return this.focusCapsule?.restore(this.layer, PREVENT_SCROLL_OPTIONS);
    }
    _restorePreviousFocusForLocation() {
        return up.viewport.restoreFocus({ layer: this.layer });
    }
    _autofocus() {
        let autofocusElement = this.fragment && e.subtreeFirst(this.fragment, '[autofocus]');
        if (autofocusElement) {
            return this._focusElement(autofocusElement);
        }
    }
    _focusElement(element) {
        if (element) {
            up.focus(element, {
                force: true,
                ...PREVENT_SCROLL_OPTIONS,
                inputDevice: this.inputDevice,
                focusVisible: this.focusVisible,
            });
            return true;
        }
    }
    _focusHash() {
        let hashTarget = up.viewport.firstHashTarget(this.hash, { layer: this.layer });
        if (hashTarget) {
            return this._focusElement(hashTarget);
        }
    }
    _wasFocusLost() {
        return this.focusCapsule?.wasLost();
    }
};


/***/ }),
/* 50 */
/***/ (() => {

const e = up.element;
const u = up.util;
up.FragmentPolling = class FragmentPolling {
    static forFragment(fragment) {
        return fragment.upPolling ||= new this(fragment);
    }
    constructor(fragment) {
        this._options = up.radio.pollOptions(fragment);
        this._fragment = fragment;
        up.destructor(fragment, this._onFragmentDestroyed.bind(this));
        this._state = 'stopped';
        this._forceIntent = null;
        this._reloadJID = u.uid();
        this._loading = false;
        this._satisfyInterval();
    }
    onPollAttributeObserved() {
        this._start();
    }
    _onFragmentAborted({ newLayer, jid }) {
        const isOurAbort = (jid === this._reloadJID);
        if (isOurAbort || newLayer)
            return;
        this._stop();
    }
    _onFragmentKept() {
        if (this._forceIntent !== 'stop') {
            this._start();
        }
    }
    _onFragmentDestroyed() {
        this._stop();
    }
    _start(options) {
        Object.assign(this._options, options);
        if (this._state === 'stopped') {
            if (!up.fragment.isTargetable(this._fragment)) {
                up.warn('[up-poll]', 'Cannot poll untargetable fragment %o', this._fragment);
                return;
            }
            this._state = 'started';
            this._bindEvents();
            this._scheduleRemainingTime();
        }
    }
    _stop() {
        if (this._state === 'started') {
            this._clearReloadTimer();
            this._state = 'stopped';
        }
    }
    forceStart(options) {
        Object.assign(this._options, options);
        this._forceIntent = 'start';
        this._start();
    }
    forceStop() {
        this._forceIntent = 'stop';
        this._stop();
    }
    _bindEvents() {
        if (this._eventsBound)
            return;
        this._eventsBound = true;
        up.destructor(this._fragment, up.on('visibilitychange up:layer:opened up:layer:dismissed up:layer:accepted', this._onVisibilityChange.bind(this)));
        up.fragment.onAborted(this._fragment, this._onFragmentAborted.bind(this));
        up.fragment.onKept(this._fragment, this._onFragmentKept.bind(this));
    }
    _onVisibilityChange() {
        if (this._isFragmentVisible()) {
            this._scheduleRemainingTime();
        }
        else {
            this._clearReloadTimer();
        }
    }
    _isFragmentVisible() {
        return (!document.hidden) &&
            (this._options.ifLayer === 'any' || this._isOnFrontLayer());
    }
    _clearReloadTimer() {
        clearTimeout(this._reloadTimer);
        this._reloadTimer = null;
    }
    _scheduleRemainingTime() {
        if (this._reloadTimer || this._loading || this._state === 'stopped')
            return;
        this._clearReloadTimer();
        this._reloadTimer = setTimeout(this._onTimerReached.bind(this), this._getRemainingDelay());
    }
    _onTimerReached() {
        this._reloadTimer = null;
        this._tryReload();
    }
    _tryReload() {
        if (this._state === 'stopped') {
            return;
        }
        if (!up.fragment.isAlive(this._fragment)) {
            this._stop();
            up.puts('[up-poll]', 'Stopped polling a detached fragment');
            return;
        }
        if (!this._isFragmentVisible()) {
            up.puts('[up-poll]', 'Will not poll hidden fragment');
            return;
        }
        this._reloadNow();
    }
    _getFullDelay() {
        return this._options.interval ?? e.numberAttr(this._fragment, 'up-interval') ?? up.radio.config.pollInterval;
    }
    _getRemainingDelay() {
        return Math.max(this._getFullDelay() - this._getFragmentAge(), 0);
    }
    _getFragmentAge() {
        return new Date() - this._lastAttempt;
    }
    _isOnFrontLayer() {
        this.layer ||= up.layer.get(this._fragment);
        return this.layer?.isFront?.();
    }
    _reloadNow() {
        this._clearReloadTimer();
        this._loading = true;
        let guardEvent = up.event.build('up:fragment:poll', { log: ['Polling fragment', this._fragment] });
        let reloadOptions = { ...this._options, guardEvent, jid: this._reloadJID };
        up.reload(this._fragment, reloadOptions).then(this._onReloadSuccess.bind(this), this._onReloadFailure.bind(this));
    }
    _onReloadSuccess({ fragment }) {
        this._loading = false;
        this._satisfyInterval();
        if (fragment) {
            this._onFragmentSwapped(fragment);
        }
        else {
            this._scheduleRemainingTime();
        }
    }
    _onFragmentSwapped(newFragment) {
        if (this._forceIntent === 'start' && up.fragment.matches(this._fragment, newFragment)) {
            this.constructor.forFragment(newFragment).forceStart(this._options);
        }
    }
    _onReloadFailure(reason) {
        this._loading = false;
        this._satisfyInterval();
        this._scheduleRemainingTime();
        up.error.throwCritical(reason);
    }
    _satisfyInterval() {
        this._lastAttempt = new Date();
    }
};


/***/ }),
/* 51 */
/***/ (() => {

const u = up.util;
up.FragmentScrolling = class FragmentScrolling extends up.FragmentProcessor {
    keys() {
        return super.keys().concat([
            'hash',
            'mode',
            'revealTop',
            'revealMax',
            'revealSnap',
            'scrollBehavior',
            'oldScrollTops',
        ]);
    }
    processPrimitive(opt) {
        switch (opt) {
            case 'top':
                return this._scrollTo(0);
            case 'bottom':
                return this._scrollTo(-0);
            case 'layer':
                return this._revealLayer();
            case 'main':
                return this._revealSelector(':main');
            case 'keep':
                return this._restoreOld();
            case 'restore':
                return this._restoreSaved();
            case 'hash':
                return this.hash && up.viewport.revealHash(this.hash, this.attributes());
            case 'target':
            case 'reveal':
            case true:
                return this._revealElement(this.fragment);
            default:
                if (u.isNumber(opt)) {
                    return this._scrollTo(opt);
                }
                else if (u.isString(opt)) {
                    return this._revealSelector(opt);
                }
        }
    }
    processElement(element) {
        return this._revealElement(element);
    }
    _revealElement(element) {
        if (element) {
            up.reveal(element, this.attributes());
            return true;
        }
    }
    _revealSelector(selector) {
        let match = this.findSelector(selector);
        return this._revealElement(match);
    }
    _revealLayer() {
        return this._revealElement(this.layer.getBoxElement());
    }
    _scrollTo(position) {
        return up.viewport.scrollTo(position, { ...this.attributes(), around: this.fragment });
    }
    _restoreOld() {
        if (this.oldScrollTops) {
            return this._restoreSaved({ scrollTops: this.oldScrollTops });
        }
    }
    _restoreSaved(extraOptions) {
        return up.viewport.restoreScroll({ ...this.attributes(), around: this.fragment, ...extraOptions });
    }
};


/***/ }),
/* 52 */
/***/ (() => {

const e = up.element;
const u = up.util;
up.Layer = class Layer extends up.Record {
    keys() {
        return [
            'element',
            'stack',
            'history',
            'mode',
            'context',
            'lastScrollTops',
            'lastFocusCapsules',
        ];
    }
    defaults() {
        return {
            context: {},
            lastScrollTops: up.viewport.newStateCache(),
            lastFocusCapsules: up.viewport.newStateCache()
        };
    }
    constructor(options = {}) {
        super(options);
        u.assert(this.mode);
    }
    setupHandlers() {
        up.link.convertClicks(this);
        this._unbindLocationChanged = up.on('up:location:changed', (event) => this._onBrowserLocationChanged(event));
    }
    teardownHandlers() {
        this._unbindLocationChanged?.();
    }
    mainTargets() {
        return up.layer.mainTargets(this.mode);
    }
    sync() {
    }
    accept() {
        throw new up.NotImplemented();
    }
    dismiss() {
        throw new up.NotImplemented();
    }
    peel(options) {
        this.stack.peel(this, options);
    }
    evalOption(option) {
        return u.evalOption(option, this);
    }
    isCurrent() {
        return this.stack.isCurrent(this);
    }
    isFront() {
        return this.stack.isFront(this);
    }
    isRoot() {
        return this.stack.isRoot(this);
    }
    isOverlay() {
        return this.stack.isOverlay(this);
    }
    isAlive() {
        throw new up.NotImplemented();
    }
    assertAlive() {
        if (!this.isAlive()) {
            throw new up.Aborted("Layer is no longer alive");
        }
    }
    get parent() {
        return this.stack.parentOf(this);
    }
    get child() {
        return this.stack.childOf(this);
    }
    get ancestors() {
        return this.stack.ancestorsOf(this);
    }
    get descendants() {
        return this.stack.descendantsOf(this);
    }
    get subtree() {
        return [this, ...this.descendants];
    }
    get index() {
        return this._index ??= this.stack.indexOf(this);
    }
    getContentElement() {
        return this.contentElement || this.element;
    }
    getBoxElement() {
        return this.boxElement || this.element;
    }
    getFocusElement() {
        return this.getBoxElement();
    }
    getFirstSwappableElement() {
        throw new up.NotImplemented();
    }
    contains(element) {
        return element.closest(up.layer.anySelector()) === this.element;
    }
    on(...args) {
        return this._buildEventListenerGroup(args).bind();
    }
    off(...args) {
        return this._buildEventListenerGroup(args).unbind();
    }
    _buildEventListenerGroup(args) {
        return up.EventListenerGroup.fromBindArgs(args, {
            guard: (event) => this._containsEventTarget(event),
            elements: [this.element],
            baseLayer: this
        });
    }
    _containsEventTarget(event) {
        return this.contains(event.target);
    }
    wasHitByMouseEvent({ clientX, clientY }) {
        const hittableElement = document.elementFromPoint(clientX, clientY);
        return !hittableElement || this.contains(hittableElement);
    }
    _buildEventEmitter(args) {
        return up.EventEmitter.fromEmitArgs(args, { layer: this });
    }
    emit(...args) {
        return this._buildEventEmitter(args).emit();
    }
    saveHistory() {
        u.assert(this.isFront());
        if (!this.showsLiveHistory())
            return;
        this._savedTitle = this.title;
        this._savedMetaTags = this.metaTags;
        this._savedLocation = this.location;
        this._savedLang = this.lang;
    }
    restoreHistory() {
        if (!this.showsLiveHistory())
            return;
        if (this._savedLocation) {
            up.history.push(this._savedLocation);
        }
        if (this._savedTitle) {
            document.title = this._savedTitle;
        }
        if (this._savedMetaTags) {
            up.history.updateMetaTags(this._savedMetaTags);
        }
        if (u.isString(this._savedLang)) {
            up.history.updateLang(this._savedLang);
        }
    }
    asCurrent(fn) {
        return this.stack.asCurrent(this, fn);
    }
    updateHistory(options) {
        if (u.isString(options.location)) {
            this._updateLocation(options.location, { push: true });
        }
        if (up.history.config.updateMetaTags && u.isList(options.metaTags)) {
            up.migrate?.warnOfHungryMetaTags?.(options.metaTags);
            this._updateMetaTags(options.metaTags);
        }
        if (u.isString(options.title)) {
            this._updateTitle(options.title);
        }
        if (u.isString(options.lang)) {
            this._updateLang(options.lang);
        }
    }
    showsLiveHistory() {
        return this.history && this.isFront();
    }
    _onBrowserLocationChanged({ location }) {
        if (this.showsLiveHistory()) {
            this._updateLocation(location, { push: false });
        }
    }
    get title() {
        if (this.showsLiveHistory()) {
            return document.title;
        }
        else {
            return this._savedTitle;
        }
    }
    _updateTitle(title) {
        this._savedTitle = title;
        if (this.showsLiveHistory()) {
            document.title = title;
        }
    }
    get metaTags() {
        if (this.showsLiveHistory()) {
            return up.history.findMetaTags();
        }
        else {
            return this._savedMetaTags;
        }
    }
    _updateMetaTags(metaTags) {
        this._savedMetaTags = metaTags;
        if (this.showsLiveHistory()) {
            up.history.updateMetaTags(metaTags);
        }
    }
    get lang() {
        if (this.showsLiveHistory()) {
            return up.history.getLang();
        }
        else {
            return this._savedLang;
        }
    }
    _updateLang(lang) {
        this._savedLang = lang;
        if (this.showsLiveHistory()) {
            up.history.updateLang(lang);
        }
    }
    get location() {
        if (this.showsLiveHistory()) {
            return up.history.location;
        }
        else {
            return this._savedLocation;
        }
    }
    _updateLocation(newLocation, { push }) {
        let prevSavedLocation = this._savedLocation;
        let liveLocation = up.history.location;
        this._savedLocation = newLocation;
        if (newLocation !== liveLocation && this.showsLiveHistory() && push) {
            up.history.push(newLocation);
        }
        if (newLocation !== prevSavedLocation && this.state !== 'opening') {
            this.emit('up:layer:location:changed', { location: newLocation, previousLocation: prevSavedLocation, log: false });
        }
    }
    selector(part) {
        return this.constructor.selector(part);
    }
    static selector(_part) {
        throw new up.NotImplemented();
    }
    toString() {
        throw new up.NotImplemented();
    }
    affix(...args) {
        return e.affix(this.getFirstSwappableElement(), ...args);
    }
    [u.isEqual.key](other) {
        return (this.constructor === other.constructor) && (this.element === other.element);
    }
    hasFocus() {
        let focusedElement = document.activeElement;
        return focusedElement !== document.body && this.element.contains(focusedElement);
    }
    reset() {
        Object.assign(this, this.defaults());
    }
};


/***/ }),
/* 53 */
/***/ (() => {

var _a;
const e = up.element;
const u = up.util;
up.Layer.Overlay = (_a = class Overlay extends up.Layer {
        keys() {
            return [
                ...super.keys(),
                ...this.constructor.VISUAL_KEYS,
                'onOpened',
                'onAccept',
                'onAccepted',
                'onDismiss',
                'onDismissed',
                'acceptEvent',
                'dismissEvent',
                'acceptLocation',
                'dismissLocation',
                'acceptFragment',
                'dismissFragment',
            ];
        }
        constructor(options) {
            super(options);
            this.state = 'opening';
            if (this.dismissible === true) {
                this.dismissible = ['button', 'key', 'outside'];
            }
            else if (this.dismissible === false) {
                this.dismissible = [];
            }
            else {
                this.dismissible = u.getSimpleTokens(this.dismissible);
            }
            if (this.acceptLocation) {
                this.acceptLocation = new up.URLPattern(this.acceptLocation);
            }
            if (this.dismissLocation) {
                this.dismissLocation = new up.URLPattern(this.dismissLocation);
            }
        }
        callback(name) {
            let fn = this[name];
            if (fn) {
                return fn.bind(this);
            }
        }
        createElement(parentElement) {
            this.nesting ||= this._suggestVisualNesting();
            const elementAttrs = u.compactObject(u.pick(this, ['align', 'position', 'size', 'class', 'nesting']));
            this.element = this.affixPart(parentElement, null, elementAttrs);
        }
        createBackdropElement(parentElement) {
            this.backdropElement = this.affixPart(parentElement, 'backdrop');
        }
        createViewportElement(parentElement) {
            this.viewportElement = this.affixPart(parentElement, 'viewport', { 'up-viewport': '' });
        }
        createBoxElement(parentElement) {
            this.boxElement = this.affixPart(parentElement, 'box');
        }
        createContentElement(parentElement) {
            this.contentElement = this.affixPart(parentElement, 'content');
        }
        setContent(content) {
            this.contentElement.append(content);
            this.onContentSet();
        }
        onContentSet() {
        }
        createDismissElement(parentElement) {
            this.dismissElement = this.affixPart(parentElement, 'dismiss', {
                'up-dismiss': '":button"',
                'aria-label': this.dismissARIALabel
            });
            return e.affix(this.dismissElement, 'span[aria-hidden="true"]', { text: this.dismissLabel });
        }
        affixPart(parentElement, part, options = {}) {
            return e.affix(parentElement, this.selector(part), options);
        }
        static selector(part) {
            return u.compact(['up', this.mode, part]).join('-');
        }
        _suggestVisualNesting() {
            const { parent } = this;
            if (this.mode === parent.mode) {
                return 1 + parent._suggestVisualNesting();
            }
            else {
                return 0;
            }
        }
        setupHandlers() {
            super.setupHandlers();
            this.overlayFocus = new up.OverlayFocus(this);
            if (this._supportsDismissMethod('button')) {
                this.createDismissElement(this.getBoxElement());
            }
            if (this._supportsDismissMethod('outside')) {
                if (this.viewportElement) {
                    up.on(this.viewportElement, 'up:click', (event) => {
                        if (event.target === this.viewportElement) {
                            this._onOutsideClicked(event, true);
                        }
                    });
                }
                else {
                    this._unbindParentClicked = this.parent.on('up:click', (event, element) => {
                        if (!up.layer.isWithinForeignOverlay(element)) {
                            const originClicked = this.origin && this.origin.contains(element);
                            this._onOutsideClicked(event, originClicked);
                        }
                    });
                }
            }
            if (this._supportsDismissMethod('key')) {
                this._unbindEscapePressed = up.event.onEscape((event) => this.onEscapePressed(event));
            }
            this.registerAttrCloser('up-accept', (value, closeOptions) => {
                this.accept(value, closeOptions);
            });
            this.registerAttrCloser('up-dismiss', (value, closeOptions) => {
                this.dismiss(value, closeOptions);
            });
            up.migrate.registerLayerCloser?.(this);
            this._registerExternalEventCloser(this.acceptEvent, this.accept);
            this._registerExternalEventCloser(this.dismissEvent, this.dismiss);
            this.on('up:click', 'label[for]', (event, label) => this._onLabelForClicked(event, label));
        }
        _onLabelForClicked(event, label) {
            let id = label.getAttribute('for');
            let fieldSelector = up.form.fieldSelector(e.idSelector(id));
            let fieldsAnywhere = up.fragment.all(fieldSelector, { layer: 'any' });
            let fieldsInLayer = up.fragment.all(fieldSelector, { layer: this });
            if (fieldsAnywhere.length > 1 && fieldsInLayer[0] !== fieldsAnywhere[0]) {
                event.preventDefault();
                const field = fieldsInLayer[0];
                field.focus();
                if (field.matches('input[type=checkbox], input[type=radio]')) {
                    field.click();
                }
            }
        }
        _onOutsideClicked(event, halt) {
            up.log.putsEvent(event);
            if (halt)
                up.event.halt(event);
            up.error.muteUncriticalSync(() => this.dismiss(':outside', { origin: event.target }));
        }
        onEscapePressed(event) {
            if (this.isFront()) {
                let field = up.form.focusedField();
                if (field) {
                    field.blur();
                }
                else if (this._supportsDismissMethod('key')) {
                    up.event.halt(event, { log: true });
                    up.error.muteUncriticalSync(() => this.dismiss(':key'));
                }
            }
        }
        registerAttrCloser(attribute, closeFn) {
            this._registerClickCloser(attribute, closeFn);
            this._registerSubmitCloser(attribute, closeFn);
        }
        _registerClickCloser(attribute, closeFn) {
            this.on('up:click', `[${attribute}]:not(form)`, (event, link) => {
                up.event.halt(event, { log: true });
                const value = e.jsonAttr(link, attribute);
                this._onAttrCloserActivated(link, value, closeFn);
            });
        }
        _registerSubmitCloser(attribute, closeFn) {
            this.on('submit', `[${attribute}]`, (event, form) => {
                up.event.halt(event, { log: true });
                const value = up.Params.fromForm(form);
                this._onAttrCloserActivated(form, value, closeFn);
            });
        }
        _onAttrCloserActivated(origin, value, closeFn) {
            const closeOptions = { origin };
            const parser = new up.OptionsParser(origin, closeOptions);
            parser.booleanOrString('animation');
            parser.string('easing');
            parser.number('duration');
            parser.string('confirm');
            up.error.muteUncriticalSync(() => closeFn(value, closeOptions));
        }
        _registerExternalEventCloser(eventTypes, closeFn) {
            if (!eventTypes) {
                return;
            }
            return this.on(eventTypes, (event) => {
                event.preventDefault();
                up.error.muteUncriticalSync(() => closeFn.call(this, event, { response: event.response }));
            });
        }
        tryAcceptForElements(newElements, response) {
            this._tryCloseForElements(this.acceptFragment, this.accept, newElements, response);
        }
        tryDismissForElements(newElements, response) {
            this._tryCloseForElements(this.dismissFragment, this.dismiss, newElements, response);
        }
        _tryCloseForElements(selector, closeFn, newElements, response) {
            let match = u.findResult(newElements, (element) => e.subtreeFirst(element, selector));
            if (match) {
                const closeValue = up.data(match);
                up.error.muteUncriticalSync(() => closeFn.call(this, closeValue, { response }));
            }
        }
        tryAcceptForLocation(newLocation, response) {
            this._tryCloseForLocation(newLocation, this.acceptLocation, this.accept, response);
        }
        tryDismissForLocation(newLocation, response) {
            this._tryCloseForLocation(newLocation, this.dismissLocation, this.dismiss, response);
        }
        _tryCloseForLocation(newLocation, urlPattern, closeFn, response) {
            let resolution = newLocation && urlPattern?.recognize(newLocation);
            if (resolution) {
                const closeValue = { ...resolution, location: newLocation };
                up.error.muteUncriticalSync(() => closeFn.call(this, closeValue, { response }));
            }
        }
        teardownHandlers() {
            super.teardownHandlers();
            this._unbindParentClicked?.();
            this._unbindEscapePressed?.();
        }
        destroyElements(options) {
            const animationProps = this.closeAnimationProps(options);
            const onFinished = () => {
                this.onElementsRemoved();
                options.onFinished?.();
            };
            up.destroy(this.element, {
                ...options,
                ...animationProps,
                onFinished,
                log: false,
            });
        }
        onElementsRemoved() {
        }
        _animationFn(boxAnimation, backdropAnimation) {
            if (up.motion.isNone(boxAnimation))
                return false;
            backdropAnimation = this.backdrop && backdropAnimation;
            return (_element, animateOptions) => {
                const boxDone = up.animate(this.getBoxElement(), boxAnimation, animateOptions);
                const backdropDone = up.animate(this.backdropElement, backdropAnimation, animateOptions);
                return Promise.all([boxDone, backdropDone]);
            };
        }
        startOpenAnimation(options = {}) {
            const animationProps = this.openAnimationProps(options);
            const onFinished = () => {
                this.wasEverVisible = true;
                options.onFinished?.();
            };
            return up.animate(this.element, animationProps.animation, { ...animationProps, onFinished });
        }
        openAnimationProps(options = {}) {
            let boxAnimation = options.animation ?? this.evalOption(this.openAnimation);
            let backdropAnimation = 'fade-in';
            let animationFn = this._animationFn(boxAnimation, backdropAnimation);
            return {
                animation: animationFn,
                easing: options.easing || this.openEasing,
                duration: options.duration || this.openDuration,
            };
        }
        closeAnimationProps(options = {}) {
            let boxAnimation = this.wasEverVisible && (options.animation ?? this.evalOption(this.closeAnimation));
            let backdropAnimation = 'fade-out';
            let animationFn = this._animationFn(boxAnimation, backdropAnimation);
            return {
                animation: animationFn,
                easing: options.easing || this.closeEasing,
                duration: options.duration ?? this.closeDuration,
            };
        }
        isAlive() {
            return ['opening', 'opened'].includes(this.state);
        }
        accept(value = null, options = {}) {
            return this._executeCloseChange('accept', value, options);
        }
        dismiss(value = null, options = {}) {
            return this._executeCloseChange('dismiss', value, options);
        }
        _supportsDismissMethod(method) {
            return u.contains(this.dismissible, method);
        }
        _executeCloseChange(verb, value, options) {
            options = { ...options, verb, value, layer: this };
            return new up.Change.CloseLayer(options).execute();
        }
        getFirstSwappableElement() {
            return this.getContentElement().children[0];
        }
        toString() {
            return `${this.mode} overlay`;
        }
    },
    _a.VISUAL_KEYS = [
        'mode',
        'position',
        'align',
        'size',
        'origin',
        'class',
        'backdrop',
        'dismissible',
        'dismissLabel',
        'dismissARIALabel',
        'openAnimation',
        'closeAnimation',
        'openDuration',
        'closeDuration',
        'openEasing',
        'closeEasing',
        'trapFocus',
    ],
    _a.UNSET_VISUALS = u.spanObject(_a.VISUAL_KEYS, undefined),
    _a);


/***/ }),
/* 54 */
/***/ (() => {

up.Layer.OverlayWithTether = class OverlayWithTether extends up.Layer.Overlay {
    createElements() {
        if (!this.origin) {
            up.fail('Missing { origin } option');
        }
        this._tether = new up.Tether({
            anchor: this.origin,
            align: this.align,
            position: this.position
        });
        this.createElement(this._tether.parent);
        this.createContentElement(this.element);
    }
    onContentSet() {
        this._tether.start(this.element);
    }
    onElementsRemoved() {
        this._tether.stop();
    }
    sync() {
        if (!this.isAlive())
            return;
        if (up.fragment.isAlive(this.element) && this._tether.isAlive()) {
            this._tether.sync();
        }
        else {
            this.dismiss(':detached', {
                animation: false,
                preventable: false
            });
        }
    }
};


/***/ }),
/* 55 */
/***/ (() => {

up.Layer.OverlayWithViewport = class OverlayWithViewport extends up.Layer.Overlay {
    static getParentElement() {
        return document.body;
    }
    createElements() {
        up.viewport.bodyShifter.raiseStack();
        this.createElement(this.constructor.getParentElement());
        if (this.backdrop) {
            this.createBackdropElement(this.element);
        }
        this.createViewportElement(this.element);
        this.createBoxElement(this.viewportElement);
        this.createContentElement(this.boxElement);
    }
    onElementsRemoved() {
        up.viewport.bodyShifter.lowerStack();
    }
    sync() {
        if (this.isAlive() && !this.element.isConnected) {
            this.constructor.getParentElement().appendChild(this.element);
        }
    }
};


/***/ }),
/* 56 */
/***/ (() => {

var _a;
const e = up.element;
up.Layer.Root = (_a = class Root extends up.Layer {
        get element() {
            return e.root;
        }
        constructor(options) {
            super(options);
            this.setupHandlers();
        }
        getFirstSwappableElement() {
            return document.body;
        }
        static selector() {
            return 'html';
        }
        setupHandlers() {
            if (!this.element.upHandlersApplied) {
                this.element.upHandlersApplied = true;
                super.setupHandlers();
            }
        }
        sync() {
            this.setupHandlers();
        }
        isAlive() {
            return true;
        }
        accept() {
            this._cannotCloseRoot();
        }
        dismiss() {
            this._cannotCloseRoot();
        }
        _cannotCloseRoot() {
            up.fail('Cannot close the root layer');
        }
        toString() {
            return "root layer";
        }
    },
    _a.mode = 'root',
    _a);


/***/ }),
/* 57 */
/***/ (() => {

var _a;
up.Layer.Modal = (_a = class Modal extends up.Layer.OverlayWithViewport {
    },
    _a.mode = 'modal',
    _a);


/***/ }),
/* 58 */
/***/ (() => {

var _a;
up.Layer.Popup = (_a = class Popup extends up.Layer.OverlayWithTether {
    },
    _a.mode = 'popup',
    _a);


/***/ }),
/* 59 */
/***/ (() => {

var _a;
up.Layer.Drawer = (_a = class Drawer extends up.Layer.OverlayWithViewport {
    },
    _a.mode = 'drawer',
    _a);


/***/ }),
/* 60 */
/***/ (() => {

var _a;
up.Layer.Cover = (_a = class Cover extends up.Layer.OverlayWithViewport {
    },
    _a.mode = 'cover',
    _a);


/***/ }),
/* 61 */
/***/ (() => {

var _a;
const u = up.util;
const e = up.element;
up.LayerLookup = (_a = class LayerLookup {
        constructor(stack, options) {
            this._stack = stack;
            if (options.normalizeLayerOptions !== false) {
                up.layer.normalizeOptions(options);
            }
            this._options = options;
            this._values = u.getSimpleTokens(options.layer);
        }
        all() {
            let results = u.flatMap(this._values, (value) => this._resolveValue(value));
            results = u.compact(results);
            results = u.uniq(results);
            return results;
        }
        static all(stack, ...args) {
            const options = u.parseArgIntoOptions(args, 'layer');
            const { layer } = options;
            if (layer instanceof up.Layer) {
                return [layer];
            }
            return new this(stack, options).all();
        }
        _forElement(element) {
            element = e.get(element);
            return u.find(this._stack.reversed(), (layer) => layer.contains(element));
        }
        _forIndex(value) {
            return this._stack.at(value);
        }
        _resolveValue(value) {
            if (value instanceof up.Layer) {
                return value;
            }
            if (u.isNumber(value)) {
                return this._forIndex(value);
            }
            if (/^\d+$/.test(value)) {
                return this._forIndex(Number(value));
            }
            if (u.isElementLike(value)) {
                return this._forElement(value);
            }
            switch (value) {
                case 'any':
                    return [this._getBaseLayer(), ...this._stack.reversed()];
                case 'current':
                    return this._getBaseLayer();
                case 'closest':
                    return this._stack.selfAndAncestorsOf(this._getBaseLayer());
                case 'parent':
                    return this._getBaseLayer().parent;
                case 'ancestor':
                case 'ancestors':
                    return this._getBaseLayer().ancestors;
                case 'child':
                    return this._getBaseLayer().child;
                case 'descendant':
                case 'descendants':
                    return this._getBaseLayer().descendants;
                case 'subtree':
                    return this._getBaseLayer().subtree;
                case 'new':
                    return 'new';
                case 'root':
                    return this._stack.root;
                case 'overlay':
                case 'overlays':
                    return this._stack.overlays.toReversed();
                case 'front':
                    return this._stack.front;
                case 'origin':
                    return this._getOriginLayer();
                default:
                    return up.fail("Unknown { layer } option: %o", value);
            }
        }
        _getOriginLayer() {
            let { origin, originLayer } = this._options;
            if (originLayer) {
                return originLayer;
            }
            if (origin) {
                return this._forElement(origin);
            }
        }
        _getBaseLayer() {
            let { baseLayer } = this._options;
            if (u.isString(baseLayer)) {
                const recursiveOptions = { ...this._options, baseLayer: this._stack.current, normalizeLayerOptions: false, layer: baseLayer };
                return this.constructor.all(this._stack, recursiveOptions)[0];
            }
            else {
                return baseLayer || this._getOriginLayer() || this._stack.current;
            }
        }
    },
    (() => {
        u.memoizeMethod(_a.prototype, {
            _getBaseLayer: true,
            _getOriginLayer: true,
        });
    })(),
    _a);


/***/ }),
/* 62 */
/***/ (() => {

const u = up.util;
up.LayerStack = class LayerStack {
    constructor() {
        this._currentOverrides = [];
        this.layers = [this._buildRoot()];
    }
    _buildRoot() {
        return up.layer.build({ mode: 'root', stack: this });
    }
    remove(layer) {
        u.remove(this.layers, layer);
    }
    peel(layer, options = {}) {
        const descendants = layer.descendants.toReversed();
        const closeOptions = { ...options, preventable: false };
        const closeMethod = options.intent === 'accept' ? 'accept' : 'dismiss';
        const closeValue = options.value ?? ':peel';
        for (let descendant of descendants) {
            descendant[closeMethod](closeValue, closeOptions);
        }
    }
    reset() {
        this.peel(this.root, { animation: false });
        this._currentOverrides = [];
        this.root.reset();
    }
    parentOf(layer) {
        return this.layers[layer.index - 1];
    }
    childOf(layer) {
        return this.layers[layer.index + 1];
    }
    ancestorsOf(layer) {
        return this.layers.slice(0, layer.index).toReversed();
    }
    selfAndAncestorsOf(layer) {
        return [layer, ...layer.ancestors];
    }
    descendantsOf(layer) {
        return this.layers.slice(layer.index + 1);
    }
    isRoot(layer) {
        return this.root === layer;
    }
    isOverlay(layer) {
        return this.root !== layer;
    }
    isCurrent(layer) {
        return this.current === layer;
    }
    isFront(layer) {
        return this.front === layer;
    }
    get(...args) {
        return this.getAll(...args)[0];
    }
    getAll(...args) {
        return up.LayerLookup.all(this, ...args);
    }
    sync() {
        for (let layer of this.layers) {
            layer.sync();
        }
    }
    asCurrent(layer, fn) {
        try {
            this._currentOverrides.push(layer);
            return fn();
        }
        finally {
            this._currentOverrides.pop();
        }
    }
    reversed() {
        return this.layers.toReversed();
    }
    dismissOverlays(value = null, options = {}) {
        options.dismissible = false;
        for (let overlay of this.overlays.toReversed()) {
            overlay.dismiss(value, options);
        }
    }
    at(index) {
        return this.layers[index];
    }
    indexOf(layer) {
        return this.layers.indexOf(layer);
    }
    get count() {
        return this.layers.length;
    }
    get root() {
        return this.layers[0];
    }
    get overlays() {
        return this.root.descendants;
    }
    get current() {
        return u.last(this._currentOverrides) || this.front;
    }
    get front() {
        return u.last(this.layers);
    }
};


/***/ }),
/* 63 */
/***/ (() => {

const u = up.util;
up.LinkCurrentURLs = class LinkCurrentURLs {
    constructor(link) {
        this._isSafe = up.link.isSafe(link);
        if (this._isSafe) {
            const href = link.getAttribute('href');
            if (href && (href !== '#')) {
                this._href = u.matchableURL(href);
            }
            const upHREF = link.getAttribute('up-href');
            if (upHREF) {
                this._upHREF = u.matchableURL(upHREF);
            }
            const alias = link.getAttribute('up-alias');
            if (alias) {
                this._aliasPattern = new up.URLPattern(alias);
            }
        }
    }
    isCurrent(normalizedLocation) {
        if (!normalizedLocation) {
            return false;
        }
        return !!(this._href === normalizedLocation ||
            this._upHREF === normalizedLocation ||
            this._aliasPattern?.test?.(normalizedLocation, false));
    }
    isAnyCurrent(normalizedLocations) {
        return normalizedLocations.some((normalizedLocation) => (this._href === normalizedLocation ||
            this._upHREF === normalizedLocation ||
            this._aliasPattern?.test?.(normalizedLocation, false)));
    }
};


/***/ }),
/* 64 */
/***/ (() => {

const u = up.util;
const e = up.element;
up.LinkFollowIntent = class LinkFollowIntent {
    constructor(link, callback) {
        this._link = link;
        this._callback = callback;
        this._lastRequest = null;
        this._on('mouseenter mousedown touchstart', (event) => this._scheduleCallback(event));
        this._on('mouseleave', () => this._unscheduleCallback());
        up.fragment.onAborted(this._link, () => this._unscheduleCallback());
    }
    _on(eventType, fn) {
        up.on(this._link, eventType, { passive: true }, fn);
    }
    _scheduleCallback(event) {
        if (!up.link.shouldFollowEvent(event, this._link))
            return;
        this._unscheduleCallback();
        const applyDelay = (event.type === 'mouseenter');
        if (applyDelay) {
            let delay = this._parseDelay();
            this._timer = u.timer(delay, () => this._runCallback(event));
        }
        else {
            this._runCallback(event);
        }
    }
    _unscheduleCallback() {
        clearTimeout(this._timer);
        if (this._lastRequest?.background)
            this._lastRequest.abort();
        this._lastRequest = null;
    }
    _parseDelay() {
        return e.numberAttr(this._link, 'up-preload-delay') ?? up.link.config.preloadDelay;
    }
    _runCallback(event) {
        up.log.putsEvent(event);
        if (!up.fragment.isAlive(this._link))
            return;
        this._callback({ onRequestKnown: (request) => this._lastRequest = request });
    }
};


/***/ }),
/* 65 */
/***/ (() => {

const u = up.util;
up.MotionController = class MotionController {
    constructor(name) {
        this.finishEvent = `up:${name}:finish`;
        this._resetProps();
    }
    startFunction(newCluster, startMotionFn) {
        const nested = (this._startingCount > 0);
        if (!nested) {
            for (let newClusterElement of newCluster) {
                this.finish(newClusterElement);
            }
        }
        this._startingCount++;
        try {
            this._playingClusters.push(newCluster);
            let promise = up.error.muteUncriticalRejection(startMotionFn({ nested }));
            return promise.finally(() => u.remove(this._playingClusters, newCluster));
        }
        finally {
            this._startingCount--;
        }
    }
    finish(element = document.body) {
        for (let playingCluster of this._findPlayingClusters(element)) {
            u.remove(this._playingClusters, playingCluster);
            for (let playingElement of playingCluster) {
                this._emitFinishEvent(playingElement);
            }
        }
    }
    _findPlayingClusters(queryElement) {
        return this._playingClusters.filter((cluster) => {
            return u.some(cluster, (clusterElement) => queryElement.contains(clusterElement));
        });
    }
    _emitFinishEvent(element) {
        return up.emit(element, this.finishEvent, { log: false });
    }
    _resetProps() {
        this._startingCount = 0;
        this._playingClusters = [];
    }
    reset() {
        this.finish();
        this._resetProps();
    }
};


/***/ }),
/* 66 */
/***/ (() => {

const e = up.element;
up.NonceableCallback = class NonceableCallback {
    constructor(script, nonce) {
        this.script = script;
        this.nonce = nonce;
    }
    static fromString(string) {
        let match = string.match(/^(nonce-(\S+)\s)?(.*)$/);
        return new this(match[3], match[2]);
    }
    unsafeEval(evalEnv) {
        if (this.nonce) {
            return this._runAsScriptElement(evalEnv);
        }
        else {
            return this._runAsFunction(evalEnv);
        }
    }
    toString() {
        return `nonce-${this.nonce} ${this.script}`;
    }
    _runAsFunction({ argNames, argValues, thisContext }) {
        let fn = new Function(...argNames, this.script);
        return fn.apply(thisContext, argValues);
    }
    _runAsScriptElement(evalEnv) {
        let wrappedScript = `
      try {
        up.noncedEval.value = (function(${evalEnv.argNames.join()}) {
          ${this.script}
        }).apply(up.noncedEval.thisContext, up.noncedEval.argValues)
      } catch (error) {
        up.noncedEval.error = error
      }
    `;
        let scriptElement;
        try {
            up.noncedEval = { ...evalEnv };
            scriptElement = e.affix(document.body, 'script', { nonce: this.nonce, text: wrappedScript });
            if (up.noncedEval.error) {
                throw up.noncedEval.error;
            }
            else {
                return up.noncedEval.value;
            }
        }
        finally {
            up.noncedEval = undefined;
            scriptElement?.remove();
        }
    }
};


/***/ }),
/* 67 */
/***/ (() => {

const e = up.element;
up.OverlayFocus = class OverlayFocus {
    constructor(layer) {
        this._layer = layer;
        this._focusElement = this._layer.getFocusElement();
        this._trapFocus = this._layer.trapFocus;
    }
    moveToFront() {
        if (this._active) {
            return;
        }
        this._active = true;
        this._unsetAttrs = e.setAttrsTemp(this._focusElement, {
            'tabindex': '0',
            'role': 'dialog',
            'aria-modal': this._trapFocus.toString()
        });
        if (this._trapFocus) {
            this._untrapFocus = up.on('focusin', (event) => this._onFocus(event));
            this._focusTrapBefore = e.affix(this._focusElement, 'beforebegin', 'up-focus-trap[tabindex=0]');
            this._focusTrapAfter = e.affix(this._focusElement, 'afterend', 'up-focus-trap[tabindex=0]');
        }
    }
    moveToBack() {
        this.teardown();
    }
    teardown() {
        if (!this._active) {
            return;
        }
        this._active = false;
        this._unsetAttrs();
        if (this._trapFocus) {
            this._untrapFocus();
            this._focusTrapBefore.remove();
            this._focusTrapAfter.remove();
        }
    }
    _onFocus(event) {
        const { target } = event;
        if (this._processingFocusEvent || up.layer.isWithinForeignOverlay(target)) {
            return;
        }
        this._processingFocusEvent = true;
        if (target === this._focusTrapBefore) {
            this._focusEnd();
        }
        else if ((target === this._focusTrapAfter) || !this._layer.contains(target)) {
            this._focusStart();
        }
        this._processingFocusEvent = false;
    }
    _focusStart(focusOptions) {
        up.focus(this._focusElement, focusOptions);
    }
    _focusEnd() {
        this._focusLastDescendant(this._layer.getBoxElement()) || this._focusStart();
    }
    _focusLastDescendant(element) {
        for (let child of [...element.children].toReversed()) {
            if (up.viewport.tryFocus(child) || this._focusLastDescendant(child)) {
                return true;
            }
        }
    }
};


/***/ }),
/* 68 */
/***/ (() => {

const u = up.util;
const e = up.element;
up.Params = class Params {
    constructor(raw, options = {}) {
        this._options = options;
        this.clear();
        this.addAll(raw);
    }
    clear() {
        this.entries = [];
    }
    [u.copy.key]() {
        return new up.Params(this, this._options);
    }
    toObject() {
        const obj = {};
        for (let entry of this.entries) {
            const { name, value } = entry;
            if (!u.isBasicObjectProperty(name)) {
                if (this._isArrayKey(name)) {
                    obj[name] ||= [];
                    obj[name].push(value);
                }
                else {
                    obj[name] = value;
                }
            }
        }
        return obj;
    }
    toArray() {
        return this.entries;
    }
    toFormData() {
        const formData = new FormData();
        for (let entry of this.entries) {
            formData.append(entry.name, entry.value);
        }
        if (!formData.entries) {
            formData.originalArray = this.entries;
        }
        return formData;
    }
    toQuery() {
        let simpleEntries = this.withoutBinaryEntries().entries;
        let parts = simpleEntries.map(this._arrayEntryToQuery);
        return parts.join('&');
    }
    _arrayEntryToQuery(entry) {
        const { value } = entry;
        let query = encodeURIComponent(entry.name);
        if (u.isGiven(value)) {
            query += "=";
            query += encodeURIComponent(value);
        }
        return query;
    }
    _isBinaryEntry({ value }) {
        return value instanceof Blob;
    }
    hasBinaryEntries() {
        return u.some(this.entries, this._isBinaryEntry);
    }
    withoutBinaryEntries() {
        let simpleEntries = u.reject(this.entries, this._isBinaryEntry);
        return new this.constructor(simpleEntries, this._options);
    }
    toURL(base) {
        let parts = [base, this.toQuery()];
        parts = u.filter(parts, u.isPresent);
        const separator = u.contains(base, '?') ? '&' : '?';
        return parts.join(separator);
    }
    add(name, value) {
        this.entries.push({ name, value });
    }
    addAll(raw) {
        if (u.isMissing(raw)) {
        }
        else if (raw instanceof this.constructor) {
            this.entries.push(...raw.entries);
        }
        else if (u.isArray(raw)) {
            this.entries.push(...raw);
        }
        else if (u.isString(raw)) {
            this._addAllFromQuery(raw);
        }
        else if (u.isFormData(raw)) {
            this._addAllFromFormData(raw);
        }
        else if (u.isObject(raw)) {
            this._addAllFromObject(raw);
        }
        else {
            up.fail("Unsupported params type: %o", raw);
        }
    }
    keys() {
        return u.map(this.entries, 'name');
    }
    values() {
        return u.map(this.entries, 'value');
    }
    _addAllFromObject(object) {
        for (let key in object) {
            const value = object[key];
            const valueElements = u.isArray(value) ? value : [value];
            for (let valueElement of valueElements) {
                this.add(key, valueElement);
            }
        }
    }
    _addAllFromQuery(query) {
        for (let part of query.split('&')) {
            if (part) {
                let [name, value] = part.split('=');
                name = decodeURIComponent(name);
                if (u.isGiven(value)) {
                    value = decodeURIComponent(value);
                }
                else {
                    value = null;
                }
                this.add(name, value);
            }
        }
    }
    _addAllFromFormData(formData) {
        for (let value of formData.entries()) {
            this.add(...value);
        }
    }
    set(name, value) {
        this.delete(name);
        this.add(name, value);
    }
    delete(name) {
        this.entries = u.reject(this.entries, this._matchEntryFn(name));
    }
    _matchEntryFn(name) {
        return (entry) => entry.name === name;
    }
    get(name) {
        if (this._isArrayKey(name)) {
            return this.getAll(name);
        }
        else {
            return this.getFirst(name);
        }
    }
    getFirst(name) {
        const entry = u.find(this.entries, this._matchEntryFn(name));
        return entry?.value;
    }
    getAll(name) {
        const entries = u.filter(this.entries, this._matchEntryFn(name));
        return u.map(entries, 'value');
    }
    _isArrayKey(key) {
        return u.evalOption(up.form.config.arrayParam, key);
    }
    [u.isBlank.key]() {
        return this.entries.length === 0;
    }
    static fromForm(form, options) {
        return this.fromContainer(form, options);
    }
    static fromContainer(container, options) {
        let fields = up.form.fields(container);
        return this.fromFields(fields, options);
    }
    static fromFields(fields, options) {
        const params = new this(null, options);
        for (let field of u.wrapList(fields)) {
            params.addField(field);
        }
        return params;
    }
    addField(field) {
        field = e.get(field);
        let name = field.name;
        if (name && this._considerFieldEnabled(field)) {
            const { tagName } = field;
            const { type } = field;
            if (tagName === 'SELECT') {
                for (let option of field.querySelectorAll('option')) {
                    if (option.selected) {
                        this.add(name, option.value);
                    }
                }
            }
            else if ((type === 'checkbox') || (type === 'radio')) {
                if (field.checked) {
                    this.add(name, field.value);
                }
            }
            else if (type === 'file') {
                for (let file of field.files) {
                    this.add(name, file);
                }
            }
            else {
                return this.add(name, field.value);
            }
        }
    }
    _considerFieldEnabled(field) {
        return !field.disabled || this._options.includeDisabled;
    }
    [u.isEqual.key](other) {
        return (this.constructor === other.constructor) && u.isEqual(this.entries, other.entries);
    }
    static fromURL(url) {
        const params = new (this)();
        const urlParts = u.parseURL(url);
        let query = urlParts.search;
        if (query) {
            query = query.replace(/^\?/, '');
            params.addAll(query);
        }
        return params;
    }
    static stripURL(url) {
        return u.normalizeURL(url, { search: false });
    }
    static merge(start, ...objects) {
        let merged = u.copy(start);
        for (let object of objects) {
            let other = u.wrapValue(this, object);
            for (let key of other.keys())
                merged.delete(key);
            merged.addAll(other);
        }
        return merged;
    }
};


/***/ }),
/* 69 */
/***/ (() => {

const u = up.util;
const e = up.element;
up.Preview = class Preview {
    constructor({ fragment, request, renderOptions, cleaner }) {
        this.fragment = fragment;
        this.request = request;
        this.renderOptions = renderOptions;
        this._cleaner = cleaner;
    }
    undo(...args) {
        if (this.ended) {
            reportError(new up.Error('Preview used after end of request'));
        }
        else {
            this._cleaner.guard(...args);
        }
    }
    get origin() {
        return this.request.origin;
    }
    get params() {
        return this.request.params;
    }
    get layer() {
        return this.request.layer;
    }
    get ended() {
        return this.request.ended;
    }
    get expiredResponse() {
        return this.renderOptions.expiredResponse;
    }
    get revalidating() {
        return !!this.expiredResponse;
    }
    run(value, options = {}) {
        for (let fn of up.status.resolvePreviewFns(value)) {
            this.undo(up.error.guard(fn, this, options));
        }
    }
    revert() {
        this._cleaner.clean();
    }
    setAttrs(...args) {
        let [element, attrs] = this._parseMutatorArgs(args, 'val', 'val');
        this.undo(e.setAttrsTemp(element, attrs));
    }
    addClass(...args) {
        let [element, klass] = this._parseMutatorArgs(args, 'val', 'val');
        this.undo(e.addClassTemp(element, klass));
    }
    addClassBatch(elements, classes) {
        for (let element of elements) {
            for (let klass of classes) {
                this.addClass(element, klass);
            }
        }
    }
    removeClass(...args) {
        let [element, klass] = this._parseMutatorArgs(args, 'val', 'val');
        this.undo(e.removeClassTemp(element, klass));
    }
    setStyle(...args) {
        let [element, styles] = this._parseMutatorArgs(args, 'val', 'val');
        this.undo(e.setStyleTemp(element, styles));
    }
    disable(...args) {
        let [element] = this._parseMutatorArgs(args, 'val');
        this.undo(up.form.disableTemp(element));
    }
    insert(...args) {
        let [reference, position = 'beforeend', tempValue] = this._parseMutatorArgs(args, 'val', u.isAdjacentPosition, 'val');
        this.undo(up.fragment.insertTemp(reference, position, tempValue));
    }
    show(...args) {
        let [element] = this._parseMutatorArgs(args, 'val');
        this.undo(e.showTemp(element));
    }
    hide(...args) {
        let [element] = this._parseMutatorArgs(args, 'val');
        this.undo(e.hideTemp(element));
    }
    hideContent(...args) {
        let [parent] = this._parseMutatorArgs(args, 'val');
        let wrapper = e.wrapChildren(parent);
        e.hide(wrapper);
        this.undo(() => e.unwrap(wrapper));
    }
    showPlaceholder(...args) {
        let [parent, placeholderReference] = this._parseMutatorArgs(args, 'val', 'val');
        let placeholderNodes = up.fragment.provideNodes(placeholderReference, { origin: this.origin });
        up.puts('[up-placeholder]', 'Showing placeholder %o', placeholderReference);
        if (parent) {
            this.swapContent(parent, placeholderNodes);
        }
        else if (this.layer === 'new') {
            this.openLayer(placeholderNodes, { closeAnimation: false });
            this.renderOptions.openAnimation = false;
        }
    }
    swapContent(...args) {
        let [parent, newContent] = this._parseMutatorArgs(args, 'val', 'val');
        this.hideContent(parent);
        this.insert(parent, newContent);
    }
    openLayer(content, options = {}) {
        let undoDismissValue = ':undo-preview';
        let onDismiss = ({ value }) => {
            if (value !== undoDismissValue)
                this.request.abort({ reason: 'Preview overlay dismissed' });
        };
        up.layer.open({
            ...u.pick(this.renderOptions, [...up.Layer.Overlay.VISUAL_KEYS, 'target']),
            ...options,
            content,
            abort: false,
            onDismiss
        });
        let overlay = up.layer.front;
        this.undo(() => overlay.dismiss(undoDismissValue, { preventable: false }));
        return overlay;
    }
    _parseMutatorArgs(args, ...specs) {
        let [element, ...rest] = u.args(args, ...specs);
        element = up.fragment.get(element, { layer: this.layer, origin: this.origin }) || this.fragment;
        return [element, ...rest];
    }
};


/***/ }),
/* 70 */
/***/ (() => {

const e = up.element;
const TRANSITION_DELAY = 300;
up.ProgressBar = class ProgressBar {
    constructor() {
        this._step = 0;
        this._element = e.affix(document.body, 'up-progress-bar');
        this._element.style.transition = `width ${TRANSITION_DELAY}ms ease-out`;
        this._moveTo(0);
        e.paint(this._element);
        this._width = 31;
        this._nextStep();
    }
    _nextStep() {
        let diff;
        if (this._width < 80) {
            if (Math.random() < 0.15) {
                diff = 7 + (5 * Math.random());
            }
            else {
                diff = 1.5 + (0.5 * Math.random());
            }
        }
        else {
            diff = 0.13 * (100 - this._width) * Math.random();
        }
        this._moveTo(this._width + diff);
        this._step++;
        const nextStepDelay = TRANSITION_DELAY + (this._step * 40);
        this.timeout = setTimeout(this._nextStep.bind(this), nextStepDelay);
    }
    _moveTo(width) {
        this._width = width;
        this._element.style.width = `${width}vw`;
    }
    destroy() {
        clearTimeout(this.timeout);
        this._element.remove();
    }
    conclude() {
        clearTimeout(this.timeout);
        this._moveTo(100);
        setTimeout(this.destroy.bind(this), TRANSITION_DELAY);
    }
};


/***/ }),
/* 71 */
/***/ (() => {

const u = up.util;
up.RenderOptions = (function () {
    const NO_PREVIEWS = {
        preview: false,
        disable: false,
        placeholder: false,
        feedback: false,
    };
    const NO_INPUT_INTERFERENCE = {
        scroll: 'keep',
        focus: 'keep',
        confirm: false,
    };
    const NO_MOTION = {
        transition: false,
        animation: false,
        openAnimation: false,
        closeAnimation: false,
    };
    const PREFLIGHT_KEYS = [
        'url',
        'method',
        'origin',
        'headers',
        'params',
        'cache',
        'fallback',
        'abort',
        'abortable',
        'handleAbort',
        'confirm',
        'feedback',
        'disable',
        'placeholder',
        'preview',
        'origin',
        'originLayer',
        'baseLayer',
        'navigate',
        'fail',
        'onError',
    ];
    const SHARED_KEYS = PREFLIGHT_KEYS.concat([
        'keep',
        'hungry',
        'history',
        'source',
        'saveScroll',
    ]);
    const CONTENT_KEYS = [
        'url',
        'response',
        'content',
        'fragment',
        'document',
    ];
    const LATE_KEYS = [
        'history',
        'focus',
        'scroll',
    ];
    const EVENT_CALLBACK = {};
    const RESULT_CALLBACK = { argNames: ['result'] };
    const ERROR_CALLBACK = { argNames: ['error'] };
    const OPEN_LAYER_CALLBACK = { expandObject: ['layer'] };
    const CLOSE_LAYER_CALLBACK = { expandObject: ['layer', 'value', 'response'] };
    const CALLBACKS = {
        onLoaded: EVENT_CALLBACK,
        onRendered: RESULT_CALLBACK,
        onFinished: RESULT_CALLBACK,
        onOffline: ERROR_CALLBACK,
        onError: ERROR_CALLBACK,
        onOpened: OPEN_LAYER_CALLBACK,
        onDismissed: CLOSE_LAYER_CALLBACK,
        onAccepted: CLOSE_LAYER_CALLBACK,
    };
    function parseCallback(key, code) {
        return up.script.parseCallback(code, parseCallbackOptions(key));
    }
    function parseCallbackOptions(key) {
        return CALLBACKS[key] ?? up.fail(`Unknown callback { ${key} }`);
    }
    function callbackAttr(element, attrName, key) {
        return up.script.callbackAttr(element, attrName, parseCallbackOptions(key));
    }
    function navigateDefaults(options) {
        if (options.navigate) {
            return up.fragment.config.navigateOptions;
        }
    }
    function normalizeURL({ url }) {
        if (url) {
            return { url: u.normalizeURL(url) };
        }
    }
    function removeUsePrefix(options) {
        u.renameKey(options, 'useData', 'data');
        u.renameKey(options, 'useHungry', 'hungry');
        u.renameKey(options, 'useKeep', 'keep');
    }
    function preprocess(options) {
        up.migrate.preprocessRenderOptions?.(options);
        up.layer.normalizeOptions(options);
        removeUsePrefix(options);
        const defaults = u.merge(up.fragment.config.renderOptions, navigateDefaults(options));
        return u.merge(u.omit(defaults, LATE_KEYS), { defaults }, { inputDevice: up.event.inputDevice }, options, normalizeURL(options), rememberOriginLayer(options));
    }
    function rememberOriginLayer({ origin, originLayer }) {
        if (origin && !originLayer) {
            return {
                originLayer: up.layer.get(origin),
            };
        }
    }
    function finalize(preprocessedOptions, lateDefaults) {
        return u.merge(preprocessedOptions.defaults, lateDefaults, preprocessedOptions);
    }
    function assertContentGiven(options) {
        if (!u.some(CONTENT_KEYS, (contentKey) => u.isGiven(options[contentKey]))) {
            if (options.defaultToEmptyContent) {
                options.content = '';
            }
            else {
                up.fail('up.render() needs either { ' + CONTENT_KEYS.join(', ') + ' } option');
            }
        }
    }
    function failOverrides(options) {
        const overrides = {};
        for (let key in options) {
            const value = options[key];
            let unprefixed = up.fragment.successKey(key);
            if (unprefixed) {
                overrides[unprefixed] = value;
            }
        }
        return overrides;
    }
    function deriveFailOptions(preprocessedOptions) {
        let markFailure = { didFail: true };
        let overrides = failOverrides(preprocessedOptions);
        if (preprocessedOptions.failOptions) {
            return {
                ...preprocessedOptions.defaults,
                ...u.pick(preprocessedOptions, SHARED_KEYS),
                ...overrides,
                didForceFailOptions: true,
                ...markFailure,
            };
        }
        else {
            return {
                ...preprocessedOptions,
                ...overrides,
                ...markFailure,
            };
        }
    }
    return {
        preprocess,
        finalize,
        assertContentGiven,
        deriveFailOptions,
        parseCallback,
        callbackAttr,
        NO_PREVIEWS,
        NO_MOTION,
        NO_INPUT_INTERFERENCE,
    };
})();


/***/ }),
/* 72 */
/***/ (() => {

const u = up.util;
up.RenderResult = class RenderResult {
    constructor({ layer, target, renderOptions = {}, partialResults = [] } = {}) {
        this.layer = layer;
        this.target = target;
        this.renderOptions = renderOptions;
        this.fragments = this._partialPhase(partialResults, 'fragments').flat();
        this.finished = this._finish(partialResults);
    }
    _partialPhase(partialResults, phase, extraValue) {
        return u.compact([...u.map(partialResults, phase), extraValue]);
    }
    async _finish(partialResults) {
        let finishedPromises = this._partialPhase(partialResults, 'finished');
        let verifyFns = this._partialPhase(partialResults, 'verifyFinished', this.renderOptions.verifyFinished);
        await Promise.all(finishedPromises);
        let finishedResult = this;
        for (let verifyFn of verifyFns) {
            let verifyerResult = await verifyFn(finishedResult);
            finishedResult = verifyerResult || finishedResult;
        }
        return finishedResult;
    }
    get none() {
        return !this.fragments.length;
    }
    get fragment() {
        return this.fragments[0];
    }
    get ok() {
        return !this.renderOptions.didFail;
    }
};


/***/ }),
/* 73 */
/***/ (() => {

var _a;
const u = up.util;
up.Request = (_a = class Request extends up.Record {
        keys() {
            return [
                'method',
                'url',
                'hash',
                'params',
                'target',
                'failTarget',
                'headers',
                'timeout',
                'background',
                'cache',
                'expireCache',
                'evictCache',
                'layer',
                'mode',
                'context',
                'failLayer',
                'failMode',
                'failContext',
                'origin',
                'originLayer',
                'originMode',
                'builtAt',
                'wrapMethod',
                'contentType',
                'payload',
                'onLoading',
                'fail',
                'abortable',
                'lateDelay',
                'previews',
            ];
        }
        defaults() {
            let config = up.network.config;
            return {
                state: 'new',
                abortable: true,
                headers: {},
                timeout: config.timeout,
                builtAt: new Date(),
                previews: [],
                wrapMethod: config.wrapMethod,
            };
        }
        constructor(options) {
            super(options);
            this.params = new up.Params(this.params);
            this._normalize();
            if ((this.target || this.layer || this.origin) && !options.basic) {
                const layerLookupOptions = { origin: this.origin };
                this.layer = up.layer.get(this.layer, layerLookupOptions);
                this.context ||= this.layer.context || {};
                this.mode ||= this.layer.mode;
                this.failLayer = up.layer.get(this.failLayer, layerLookupOptions);
                this.failContext ||= this.failLayer?.context || {};
                this.failMode ||= this.failLayer?.mode;
                this.originLayer ||= up.layer.get(this.origin) || up.layer.current;
                this.originMode ||= this.originLayer?.mode;
            }
            this.bindLayer = options.bindLayer || this.layer;
            this._fragments = options.fragments;
            this._bindFragments = options.bindFragments;
            this._deferred = u.newDeferred();
            this._setAutoHeaders();
        }
        get effectiveLateTime() {
            if (this.background) {
                return false;
            }
            else {
                return this.lateDelay ?? u.evalOption(up.network.config.lateDelay, this);
            }
        }
        isTimed() {
            return u.isNumber(this.effectiveLateTime);
        }
        get xhr() {
            return this._xhr ??= new XMLHttpRequest();
        }
        get fragments() {
            return (this._fragments ||= this._findFragments());
        }
        _findFragments() {
            let steps = up.fragment.parseTargetSteps(this.target);
            let lookupOpts = { origin: this.origin, layer: this.layer };
            let matches = u.map(steps, (step) => up.fragment.get(step.selector, lookupOpts));
            return u.compact(matches);
        }
        get bindFragments() {
            return this._bindFragments || this.fragments;
        }
        get fragment() {
            return this.fragments?.[0];
        }
        _normalize() {
            this.method = u.normalizeMethod(this.method);
            this._extractHashFromURL();
            this._transferParamsToURL();
            this.url = u.normalizeURL(this.url);
        }
        _evictExpensiveAttrs() {
            u.task(() => {
                this.layer = undefined;
                this.failLayer = undefined;
                this.bindLayer = undefined;
                this.origin = undefined;
                this.originLayer = undefined;
                this._fragments = undefined;
                this._bindFragments = undefined;
            });
        }
        _extractHashFromURL() {
            let match = this.url?.match(/^([^#]*)(#.+)$/);
            if (match) {
                this.url = match[1];
                return this.hash = match[2];
            }
        }
        _transferParamsToURL() {
            if (!this.url || this.allowsPayload() || u.isBlank(this.params)) {
                return;
            }
            this.url = this.params.toURL(this.url);
            this.params.clear();
        }
        isSafe() {
            return up.network.isSafeMethod(this.method);
        }
        allowsPayload() {
            return u.methodAllowsPayload(this.method);
        }
        will302RedirectWithGET() {
            return this.isSafe() || (this.method === 'POST');
        }
        willCache() {
            return u.evalAutoOption(this.cache, up.network.config.autoCache, this);
        }
        runQueuedCallbacks() {
            u.always(this, () => this._evictExpensiveAttrs());
        }
        load() {
            if (this.state !== 'new')
                return;
            if (this._emitLoad()) {
                this.state = 'loading';
                this._normalize();
                this.onLoading?.();
                this.expired = false;
                new up.Request.XHRRenderer(this).buildAndSend({
                    onload: () => this._onXHRLoad(),
                    onerror: () => this._onXHRError(),
                    ontimeout: () => this._onXHRTimeout(),
                    onabort: () => this._onXHRAbort()
                });
                return true;
            }
            else {
                this.abort({ reason: 'Prevented by event listener' });
            }
        }
        runPreviews(renderOptions) {
            if (!this.ended && !this.fromCache) {
                this._revertPreviews = up.status.runPreviews(this, renderOptions);
            }
        }
        _emitLoad() {
            let event = this.emit('up:request:load', { log: ['Loading %s', this.description] });
            return !event.defaultPrevented;
        }
        loadPage() {
            up.network.abort();
            new up.Request.FormRenderer(this).buildAndSubmit();
        }
        _onXHRLoad() {
            const response = this._extractResponseFromXHR();
            const log = 'Loaded ' + response.description;
            this.emit('up:request:loaded', { request: response.request, response, log });
            this.respondWith(response);
        }
        _onXHRError() {
            this._setOfflineState('Network error');
        }
        _onXHRTimeout() {
            this._setOfflineState('Timeout');
        }
        _onXHRAbort() {
            this._setAbortedState();
        }
        abort({ reason } = {}) {
            if (this._setAbortedState(reason) && this._xhr) {
                this._xhr.abort();
            }
        }
        _setAbortedState(reason = 'Unknown reason') {
            if (this.ended)
                return;
            let log = ["Aborted request to %s: %s", this.description, reason];
            this.state = 'aborted';
            this._reject(new up.Aborted(log));
            this.emit('up:request:aborted', { log });
            return true;
        }
        _setOfflineState(reason = 'Unknown reason') {
            if (this.ended)
                return;
            let log = ['Cannot load request from %s: %s', this.description, reason];
            this.state = 'offline';
            this.emit('up:request:offline', { log });
            this._reject(new up.Offline(log, { reason, request: this }));
        }
        respondWith(response) {
            this.response = response;
            if (this.ended)
                return;
            this.state = 'loaded';
            if (response.ok) {
                this._resolve(response);
            }
            else {
                this._reject(response);
            }
        }
        _resolve(response) {
            this._onSettle();
            this._deferred.resolve(response);
        }
        _reject(responseOrError) {
            this._onSettle();
            this._deferred.reject(responseOrError);
        }
        _onSettle() {
            this._revertPreviews?.();
        }
        get ended() {
            return (this.state !== 'new') && (this.state !== 'loading') && (this.state !== 'tracking');
        }
        csrfHeader() {
            return up.protocol.csrfHeader();
        }
        csrfParam() {
            return up.protocol.csrfParam();
        }
        csrfToken() {
            if (!this.isSafe() && !this.isCrossOrigin()) {
                return up.protocol.csrfToken();
            }
        }
        isCrossOrigin() {
            return u.isCrossOrigin(this.url);
        }
        _extractResponseFromXHR() {
            const responseAttrs = {
                method: this.method,
                url: this.url,
                request: this,
                xhr: this.xhr,
                text: this.xhr.responseText,
                status: this.xhr.status,
                title: up.protocol.titleFromXHR(this.xhr),
                target: up.protocol.targetFromXHR(this.xhr),
                openLayer: up.protocol.openLayerFromXHR(this.xhr),
                acceptLayer: up.protocol.acceptLayerFromXHR(this.xhr),
                dismissLayer: up.protocol.dismissLayerFromXHR(this.xhr),
                eventPlans: up.protocol.eventPlansFromXHR(this.xhr),
                context: up.protocol.contextFromXHR(this.xhr),
                expireCache: up.protocol.expireCacheFromXHR(this.xhr),
                evictCache: up.protocol.evictCacheFromXHR(this.xhr),
                fail: this.fail,
            };
            let methodFromResponse = up.protocol.methodFromXHR(this.xhr);
            let urlFromResponse = up.protocol.locationFromXHR(this.xhr);
            if (urlFromResponse) {
                if (!u.matchURLs(this.url, urlFromResponse)) {
                    methodFromResponse ||= 'GET';
                }
                responseAttrs.url = urlFromResponse;
            }
            if (methodFromResponse) {
                responseAttrs.method = methodFromResponse;
            }
            return new up.Response(responseAttrs);
        }
        _buildEventEmitter(args) {
            return up.EventEmitter.fromEmitArgs(args, {
                layer: this.bindLayer,
                request: this,
                origin: this.origin
            });
        }
        emit(...args) {
            return this._buildEventEmitter(args).emit();
        }
        assertEmitted(...args) {
            this._buildEventEmitter(args).assertEmitted();
        }
        get description() {
            return this.method + ' ' + this.url;
        }
        isBoundToSubtrees(subtreeRoots) {
            subtreeRoots = u.wrapList(subtreeRoots);
            return u.some(this.bindFragments, function (fragment) {
                return u.some(subtreeRoots, (subtreeElement) => subtreeElement.contains(fragment));
            });
        }
        isBoundToLayers(layers) {
            return u.contains(layers, this.bindLayer);
        }
        get age() {
            return new Date() - this.builtAt;
        }
        header(name) {
            return this.headers[name];
        }
        _setAutoHeaders() {
            for (let key of ['target', 'failTarget', 'mode', 'failMode', 'context', 'failContext', 'originMode']) {
                this._setPropertyHeader(key);
            }
            let csrfHeader, csrfToken;
            if ((csrfHeader = this.csrfHeader()) && (csrfToken = this.csrfToken())) {
                this._setAutoHeader(csrfHeader, csrfToken);
            }
            this._setAutoHeader(up.protocol.headerize('version'), up.version);
        }
        _setPropertyHeader(key) {
            this._setAutoHeader(up.protocol.headerize(key), this[key]);
        }
        _setAutoHeader(name, value) {
            if (u.isMissing(value)) {
                return;
            }
            if (u.isOptions(value) || u.isArray(value)) {
                value = u.safeStringifyJSON(value);
            }
            this.headers[name] = value;
        }
        mergeIfUnsent(trackingRequest) {
            if (this.state !== 'new')
                return;
            if (!this.target || !trackingRequest.target)
                return;
            let targetAtoms = up.fragment.splitTarget(this.target + ',' + trackingRequest.target);
            this.target = u.uniq(targetAtoms).join(', ');
            this._setPropertyHeader('target');
            this._fragments = u.uniq([...this.fragments, ...trackingRequest.fragments]);
        }
        static tester(condition, { except } = {}) {
            let testFn;
            if (u.isFunction(condition)) {
                testFn = condition;
            }
            else if (condition instanceof this) {
                testFn = (request) => condition === request;
            }
            else if (u.isString(condition)) {
                let pattern = new up.URLPattern(condition);
                testFn = (request) => pattern.test(request.url);
            }
            else {
                testFn = (_request) => condition;
            }
            if (except) {
                return (request) => !up.cache.willHaveSameResponse(request, except) && testFn(request);
            }
            else {
                return testFn;
            }
        }
    },
    (() => {
        u.delegatePromise(_a.prototype, function () { return this._deferred; });
    })(),
    _a);


/***/ }),
/* 74 */
/***/ (() => {

const u = up.util;
class Route {
    constructor() {
        this.varyHeaders = new Set();
        this.requests = [];
    }
    matchBest(newRequest) {
        let matches = this.requests.filter((cachedRequest) => this.satisfies(cachedRequest, newRequest));
        return u.last(matches);
    }
    delete(request) {
        u.remove(this.requests, request);
    }
    put(request) {
        this.requests.push(request);
    }
    updateVary(response) {
        for (let headerName of response.varyHeaderNames) {
            this.varyHeaders.add(headerName);
        }
    }
    satisfies(cachedRequest, newRequest) {
        if (cachedRequest === newRequest)
            return true;
        return u.every(this.varyHeaders, (varyHeader) => {
            let cachedValue = cachedRequest.header(varyHeader);
            let newValue = newRequest.header(varyHeader);
            if (varyHeader === 'X-Up-Target' || varyHeader === 'X-Up-Fail-Target') {
                if (!cachedValue)
                    return true;
                if (!newValue)
                    return false;
                let cachedTokens = up.fragment.splitTarget(cachedValue);
                let newTokens = up.fragment.splitTarget(newValue);
                return u.containsAll(cachedTokens, newTokens);
            }
            else {
                return cachedValue === newValue;
            }
        });
    }
}
up.Request.Cache = class Cache {
    constructor() {
        this.reset();
    }
    reset() {
        this._routes = {};
        this._requests = [];
    }
    get(request) {
        request = this._wrap(request);
        let route = this._getRoute(request);
        let cachedRequest = route.matchBest(request);
        if (cachedRequest) {
            if (this._isUsable(cachedRequest)) {
                return cachedRequest;
            }
            else {
                this._delete(request, route);
            }
        }
    }
    async put(request) {
        request = this._wrap(request);
        let route = this._getRoute(request);
        let { response } = request;
        if (response)
            route.updateVary(response);
        let superseded = route.requests.filter((oldRequest) => route.satisfies(request, oldRequest));
        for (let r of superseded) {
            this._delete(r);
        }
        request.cacheRoute = route;
        route.put(request);
        this._requests.push(request);
        this._limitSize();
    }
    async track(existingRequest, newRequest, options = {}) {
        newRequest.trackedRequest = existingRequest;
        newRequest.state = 'tracking';
        let value;
        if (existingRequest.ended && existingRequest.response) {
            value = existingRequest.response;
        }
        else {
            value = await u.always(existingRequest);
        }
        if (value instanceof up.Response) {
            if (options.force || existingRequest.cacheRoute.satisfies(existingRequest, newRequest)) {
                newRequest.fromCache = true;
                value = u.variant(value, { request: newRequest });
                newRequest.respondWith(value);
                u.delegate(newRequest, ['expired', 'state'], () => existingRequest);
            }
            else {
                delete newRequest.trackedRequest;
                newRequest.state = 'new';
                options.onIncompatible?.(newRequest);
            }
        }
        else {
            newRequest.state = existingRequest.state;
            newRequest._reject(value);
        }
    }
    willHaveSameResponse(existingRequest, newRequest) {
        return existingRequest === newRequest || existingRequest === newRequest.trackedRequest;
    }
    evict(condition = true, testerOptions) {
        this._eachMatch(condition, testerOptions, (request) => this._delete(request));
    }
    expire(condition = true, testerOptions) {
        this._eachMatch(condition, testerOptions, (request) => request.expired = true);
    }
    reindex(request) {
        this._delete(request);
        delete request.cacheRoute;
        this.put(request);
    }
    _delete(request) {
        u.remove(this._requests, request);
        request.cacheRoute?.delete(request);
    }
    _getRoute(request) {
        return request.cacheRoute || (this._routes[request.description] ||= new Route());
    }
    _isUsable(request) {
        return request.age < up.network.config.cacheEvictAge;
    }
    get currentSize() {
        return this._requests.length;
    }
    get _capacity() {
        return up.network.config.cacheSize;
    }
    _limitSize() {
        for (let i = 0; i < (this.currentSize - this._capacity); i++) {
            this._delete(this._requests[0]);
        }
    }
    _eachMatch(condition = true, testerOptions, fn) {
        let tester = up.Request.tester(condition, testerOptions);
        let results = u.filter(this._requests, tester);
        u.each(results, fn);
    }
    _wrap(requestOrOptions) {
        return u.wrapValue(up.Request, requestOrOptions);
    }
};


/***/ }),
/* 75 */
/***/ (() => {

const u = up.util;
up.Request.Queue = class Queue {
    constructor() {
        this.reset();
    }
    reset() {
        this._queuedRequests = [];
        this._currentRequests = [];
        this._emittedLate = false;
    }
    get allRequests() {
        return this._currentRequests.concat(this._queuedRequests);
    }
    asap(request) {
        request.runQueuedCallbacks();
        u.always(request, () => this._onRequestSettled(request));
        this._scheduleSlowTimer(request);
        this._queueRequest(request);
        queueMicrotask(() => this._poke());
    }
    promoteToForeground(request) {
        if (request.background) {
            request.background = false;
            this._scheduleSlowTimer(request);
        }
    }
    _scheduleSlowTimer(request) {
        if (!request.isTimed())
            return;
        let timeUntilLate = Math.max(request.effectiveLateTime - request.age);
        u.timer(timeUntilLate, () => this._checkForLate());
    }
    _getMaxConcurrency() {
        return u.evalOption(up.network.config.concurrency);
    }
    _hasConcurrencyLeft() {
        const maxConcurrency = this._getMaxConcurrency();
        return (maxConcurrency === -1) || (this._currentRequests.length < maxConcurrency);
    }
    get size() {
        return this.allRequests.length;
    }
    isBusy() {
        return this.size > 0;
    }
    _queueRequest(request) {
        this._queuedRequests.push(request);
    }
    _pluckNextRequest() {
        let request = u.find(this._queuedRequests, (request) => !request.background);
        request ||= this._queuedRequests[0];
        return u.remove(this._queuedRequests, request);
    }
    _sendRequestNow(request) {
        if (request.load()) {
            this._currentRequests.push(request);
        }
    }
    _onRequestSettled(request) {
        u.remove(this._currentRequests, request) || u.remove(this._queuedRequests, request);
        queueMicrotask(() => this._poke());
        u.task(() => this._checkForRecover());
    }
    _poke() {
        let request;
        if (this._hasConcurrencyLeft() && (request = this._pluckNextRequest())) {
            return this._sendRequestNow(request);
        }
    }
    abort(...args) {
        let [conditions = true, { except, reason, logOnce }] = u.args(args, 'val', 'options');
        let tester = up.Request.tester(conditions, { except });
        for (let list of [this._currentRequests, this._queuedRequests]) {
            const abortableRequests = u.filter(list, tester);
            for (let abortableRequest of abortableRequests) {
                if (logOnce) {
                    up.puts(...logOnce);
                    logOnce = null;
                }
                abortableRequest.abort({ reason });
                u.remove(list, abortableRequest);
            }
        }
    }
    _checkForLate() {
        if (!this._emittedLate && this._hasLateTimedRequests()) {
            this._emittedLate = true;
            up.emit('up:network:late', { log: 'Server is slow to respond' });
        }
    }
    _checkForRecover() {
        if (this._emittedLate && !this._timedRequests.length) {
            this._emittedLate = false;
            up.emit('up:network:recover', { log: 'Slow requests were loaded' });
        }
    }
    get _timedRequests() {
        return this.allRequests.filter((request) => request.isTimed());
    }
    _hasLateTimedRequests() {
        const timerTolerance = 1;
        const isLate = (request) => request.age >= (request.effectiveLateTime - timerTolerance);
        return u.some(this._timedRequests, isLate);
    }
};


/***/ }),
/* 76 */
/***/ (() => {

const u = up.util;
const e = up.element;
const HTML_FORM_METHODS = ['GET', 'POST'];
up.Request.FormRenderer = class FormRenderer {
    constructor(request) {
        this._request = request;
    }
    buildAndSubmit() {
        this.params = this._request.params.withoutBinaryEntries();
        let action = this._request.url;
        let { method } = this._request;
        const paramsFromQuery = up.Params.fromURL(action);
        this.params.addAll(paramsFromQuery);
        action = up.Params.stripURL(action);
        if (!u.contains(HTML_FORM_METHODS, method)) {
            method = up.protocol.wrapMethod(method, this.params);
        }
        this._form = e.affix(document.body, 'form.up-request-loader', { method, action });
        let contentType = this._request.contentType;
        if (contentType) {
            this._form.setAttribute('enctype', contentType);
        }
        let csrfParam, csrfToken;
        if ((csrfParam = this._request.csrfParam()) && (csrfToken = this._request.csrfToken())) {
            this.params.add(csrfParam, csrfToken);
        }
        u.each(this.params.toArray(), this._addField.bind(this));
        up.browser.submitForm(this._form);
    }
    _addField(attrs) {
        e.affix(this._form, 'input[type=hidden]', attrs);
    }
};


/***/ }),
/* 77 */
/***/ (() => {

var _a;
const CONTENT_TYPE_URL_ENCODED = 'application/x-www-form-urlencoded';
const CONTENT_TYPE_FORM_DATA = 'multipart/form-data';
const u = up.util;
up.Request.XHRRenderer = (_a = class XHRRenderer {
        constructor(request) {
            this._request = request;
        }
        buildAndSend(handlers) {
            const xhr = this._request.xhr;
            this._params = u.copy(this._request.params);
            if (this._request.timeout) {
                xhr.timeout = this._request.timeout;
            }
            xhr.open(this._getMethod(), this._request.url);
            let contentType = this._getContentType();
            if (contentType) {
                xhr.setRequestHeader('Content-Type', contentType);
            }
            for (let headerName in this._request.headers) {
                let headerValue = this._request.headers[headerName];
                xhr.setRequestHeader(headerName, headerValue);
            }
            Object.assign(xhr, handlers);
            xhr.send(this._getPayload());
        }
        _getMethod() {
            let method = this._request.method;
            if (this._request.wrapMethod && !this._request.will302RedirectWithGET()) {
                method = up.protocol.wrapMethod(method, this._params);
            }
            return method;
        }
        _getContentType() {
            this._finalizePayload();
            return this._contentType;
        }
        _getPayload() {
            this._finalizePayload();
            return this._payload;
        }
        _finalizePayload() {
            this._payload = this._request.payload;
            this._contentType = this._request.contentType;
            if (!this._payload && this._request.allowsPayload()) {
                if (!this._contentType) {
                    this._contentType = this._params.hasBinaryEntries() ? CONTENT_TYPE_FORM_DATA : CONTENT_TYPE_URL_ENCODED;
                }
                if (this._contentType === CONTENT_TYPE_FORM_DATA) {
                    this._contentType = null;
                    this._payload = this._params.toFormData();
                }
                else {
                    this._payload = this._params.toQuery().replace(/%20/g, '+');
                }
            }
        }
    },
    (() => {
        u.memoizeMethod(_a.prototype, {
            _finalizePayload: true,
            _getMethod: true,
        });
    })(),
    _a);


/***/ }),
/* 78 */
/***/ (() => {

const u = up.util;
const HTML_CONTENT_TYPE = /^(text\/html|application\/xhtml\+xml) *(;|$)/i;
up.Response = class Response extends up.Record {
    keys() {
        return [
            'method',
            'url',
            'text',
            'status',
            'request',
            'xhr',
            'target',
            'title',
            'openLayer',
            'acceptLayer',
            'dismissLayer',
            'eventPlans',
            'context',
            'expireCache',
            'evictCache',
            'headers',
            'loadedAt',
            'fail',
        ];
    }
    defaults() {
        return {
            headers: {},
            loadedAt: new Date(),
        };
    }
    get ok() {
        return !u.evalOption(this.fail ?? up.network.config.fail, this);
    }
    get none() {
        return !this.text;
    }
    header(name) {
        return this.headers[name] || this.xhr?.getResponseHeader(name);
    }
    get varyHeaderNames() {
        let varyHeaderValue = this.header('Vary');
        return u.getSimpleTokens(varyHeaderValue, { separator: ',' });
    }
    get contentType() {
        return this.header('Content-Type');
    }
    isHTML() {
        return HTML_CONTENT_TYPE.test(this.contentType);
    }
    get cspInfo() {
        let policy = this.header('Content-Security-Policy') || this.header('Content-Security-Policy-Report-Only');
        return up.CSPInfo.fromHeader(policy);
    }
    get lastModified() {
        let header = this.header('Last-Modified');
        if (header) {
            return new Date(header);
        }
    }
    get etag() {
        return this.header('ETag');
    }
    get json() {
        return this.parsedJSON ||= JSON.parse(this.text);
    }
    get age() {
        let now = new Date();
        return now - this.loadedAt;
    }
    get expired() {
        return this.age > up.network.config.cacheExpireAge ||
            this.request.expired;
    }
    get description() {
        return `HTTP ${this.status} response to ${this.request.description}`;
    }
    get redirect() {
        return (this.url !== this.request.url) || (this.method !== this.request.method);
    }
    get redirectRequest() {
        if (!this.redirect)
            return;
        let finalRequest = u.variant(this.request, {
            method: this.method,
            url: this.url,
            cacheRoute: null,
        });
        up.cache.track(this.request, finalRequest, { force: true });
        return finalRequest;
    }
};


/***/ }),
/* 79 */
/***/ (() => {

var _a;
const u = up.util;
const e = up.element;
up.ResponseDoc = (_a = class ResponseDoc {
        constructor({ document, fragment, content, target, origin, data, cspInfo, match }) {
            if (document) {
                this._parseDocument(document, origin, data);
            }
            else if (fragment) {
                this._parseFragment(fragment, origin, data);
            }
            else {
                this._parseContent(content || '', origin, target, data);
            }
            this._cspInfo = cspInfo;
            up.script.warnOfUnsafeCSP(cspInfo);
            if (origin) {
                let originSelector = up.fragment.tryToTarget(origin);
                if (originSelector) {
                    this._rediscoveredOrigin = this.select(originSelector);
                }
            }
            this._match = match;
        }
        _parseDocument(value, origin, data) {
            if (value instanceof Document) {
                this._document = value;
                this._isFullDocument = true;
            }
            else if (u.isString(value)) {
                this._isFullDocument = e.isFullDocumentHTML(value);
                let htmlParser = (html) => [e.createBrokenDocumentFromHTML(html)];
                let nodes = up.fragment.provideNodes(value, { origin, data, htmlParser });
                if (nodes[0] instanceof Document) {
                    this._document = nodes[0];
                }
                else {
                    this._document = this._buildFauxDocument(nodes);
                }
            }
            else {
                this._document = this._buildFauxDocument(value);
            }
        }
        _parseFragment(value, origin, data) {
            let element = e.extractSingular(up.fragment.provideNodes(value, { origin, data }));
            this._document = this._buildFauxDocument(element);
        }
        _parseContent(value, origin, target, data) {
            if (!target)
                up.fail("must pass a { target } when passing { content }");
            let simplifiedTarget = u.map(up.fragment.parseTargetSteps(target), 'selector').join();
            let nodes = up.fragment.provideNodes(value, { origin, data });
            let matchingElement = e.createFromSelector(simplifiedTarget, { content: nodes });
            this._document = this._buildFauxDocument(matchingElement);
        }
        _buildFauxDocument(nodes) {
            nodes = u.wrapList(nodes);
            let fauxDocument = document.createElement('up-document');
            fauxDocument.append(...nodes);
            return fauxDocument;
        }
        rootSelector() {
            return up.fragment.toTarget(this._document.children[0]);
        }
        get title() {
            return this._fromHead(this._getTitleText);
        }
        _getHead() {
            if (this._isFullDocument) {
                return this._document.head;
            }
        }
        _fromHead(fn) {
            let head = this._getHead();
            return head && fn(head);
        }
        get metaTags() {
            return this._fromHead(up.history.findMetaTags);
        }
        get assets() {
            return this._fromHead((head) => {
                let assets = up.script.findAssets(head);
                return u.map(assets, (asset) => {
                    asset = e.revivedClone(asset);
                    up.script.adoptDetachedHeadAsset(asset, this._cspInfo);
                    return asset;
                });
            });
        }
        get lang() {
            if (this._isFullDocument) {
                return up.history.getLang(this._document);
            }
        }
        _getTitleText(head) {
            return head.querySelector('title')?.textContent;
        }
        select(selector) {
            let finder = new up.FragmentFinder({
                selector: selector,
                origin: this._rediscoveredOrigin,
                document: this._document,
                match: this._match,
            });
            return finder.find();
        }
        selectSteps(steps) {
            return steps.filter((step) => {
                return this._trySelectStep(step) || this._cannotMatchStep(step);
            });
        }
        commitSteps(steps) {
            return steps.filter((step) => this.commitElement(step.newElement));
        }
        _trySelectStep(step) {
            if (step.newElement) {
                return true;
            }
            let newElement = this.select(step.selector);
            if (!newElement) {
                return;
            }
            let { selectEvent } = step;
            if (selectEvent) {
                selectEvent.newFragment = newElement;
                selectEvent.renderOptions = step.originalRenderOptions;
                up.emit(step.oldElement, selectEvent, { callback: step.selectCallback });
                if (selectEvent.defaultPrevented) {
                    return;
                }
            }
            step.newElement = newElement;
            return true;
        }
        _cannotMatchStep(step) {
            if (!step.maybe) {
                throw new up.CannotMatch();
            }
        }
        commitElement(element) {
            if (this._document.contains(element)) {
                up.script.adoptNewFragment(element, this._cspInfo);
                element.remove();
                return true;
            }
        }
        finalizeElement(element) {
            if (this._document instanceof Document) {
                for (let brokenElement of e.subtree(element, ':is(noscript, script, audio, video):not(.up-keeping, .up-keeping *)')) {
                    let clone = e.revivedClone(brokenElement);
                    brokenElement.replaceWith(clone);
                }
            }
        }
    },
    (() => {
        u.memoizeMethod(_a.prototype, {
            _getHead: true,
        });
    })(),
    _a);


/***/ }),
/* 80 */
/***/ (() => {

const e = up.element;
const u = up.util;
up.RevealMotion = class RevealMotion {
    constructor(element, options = {}) {
        this._element = element;
        this._viewport = e.get(options.viewport) || up.viewport.get(this._element);
        this._obstructionsLayer = up.layer.get(this._viewport);
        this._behavior = options.scrollBehavior ?? options.behavior ?? 'instant';
        const viewportConfig = up.viewport.config;
        this._snap = options.snap ?? options.revealSnap ?? viewportConfig.revealSnap;
        this._padding = options.padding ?? options.revealPadding ?? viewportConfig.revealPadding;
        this._top = options.top ?? options.revealTop ?? viewportConfig.revealTop;
        this._max = options.max ?? options.revealMax ?? viewportConfig.revealMax;
        this._topObstructionSelector = viewportConfig.selector('fixedTopSelectors');
        this._bottomObstructionSelector = viewportConfig.selector('fixedBottomSelectors');
    }
    start() {
        const viewportRect = this._getViewportRect(this._viewport);
        const elementRect = up.Rect.fromElement(this._element);
        if (this._max) {
            const maxPixels = u.evalOption(this._max, this._element);
            elementRect.height = Math.min(elementRect.height, maxPixels);
        }
        elementRect.grow(this._padding);
        this._substractObstructions(viewportRect);
        if (viewportRect.height < 0) {
            up.fail('Viewport has no visible area');
        }
        const originalScrollTop = this._viewport.scrollTop;
        let newScrollTop = originalScrollTop;
        if (this._top || (elementRect.height > viewportRect.height)) {
            const diff = elementRect.top - viewportRect.top;
            newScrollTop += diff;
        }
        else if (elementRect.top < viewportRect.top) {
            newScrollTop -= (viewportRect.top - elementRect.top);
        }
        else if (elementRect.bottom > viewportRect.bottom) {
            newScrollTop += (elementRect.bottom - viewportRect.bottom);
        }
        else {
        }
        if (u.isNumber(this._snap) && (newScrollTop < this._snap) && (elementRect.top < (0.5 * viewportRect.height))) {
            newScrollTop = 0;
        }
        if (newScrollTop !== originalScrollTop) {
            this._viewport.scrollTo({ top: newScrollTop, behavior: this._behavior });
        }
    }
    _getViewportRect() {
        if (up.viewport.isRoot(this._viewport)) {
            return new up.Rect({
                left: 0,
                top: 0,
                width: up.viewport.rootWidth(),
                height: up.viewport.rootHeight()
            });
        }
        else {
            return up.Rect.fromElement(this._viewport);
        }
    }
    _computeObstructionRects(selector) {
        let elements = up.fragment.all(selector, { layer: this._obstructionsLayer });
        elements = u.filter(elements, e.isVisible);
        return u.map(elements, (element) => {
            if (e.style(element, 'position') === 'sticky') {
                return up.Rect.fromElementAsFixed(element);
            }
            else {
                return up.Rect.fromElement(element);
            }
        });
    }
    _substractObstructions(viewportRect) {
        for (let obstructionRect of this._computeObstructionRects(this._topObstructionSelector)) {
            let diff = obstructionRect.bottom - viewportRect.top;
            if (diff > 0) {
                viewportRect.top += diff;
                viewportRect.height -= diff;
            }
        }
        for (let obstructionRect of this._computeObstructionRects(this._bottomObstructionSelector)) {
            let diff = viewportRect.bottom - obstructionRect.top;
            if (diff > 0) {
                viewportRect.height -= diff;
            }
        }
    }
};


/***/ }),
/* 81 */
/***/ (() => {

const e = up.element;
const u = up.util;
up.ScriptGate = class ScriptGate {
    constructor(cspInfo = up.CSPInfo.none()) {
        let pageNonce = up.script.cspNonce();
        this._evalCallbackPolicy = new EvalCallbackPolicy(pageNonce, cspInfo);
        this._scriptElementPolicy = new BodyScriptElementPolicy(pageNonce, cspInfo);
        this._detachedAssetPolicy = new DetachedAssetPolicy(pageNonce, cspInfo);
    }
    warnOfUnsafeCSP() {
        if (up.script.config.cspWarnings) {
            this._evalCallbackPolicy.warnOfUnsafeCSP();
            this._scriptElementPolicy.warnOfUnsafeCSP();
        }
    }
    evalCallback(nonceableCallback, evalEnv) {
        const policy = this._evalCallbackPolicy;
        if (policy.passesItem(nonceableCallback.nonce)) {
            try {
                return nonceableCallback.unsafeEval(evalEnv);
            }
            catch (error) {
                if (error instanceof EvalError) {
                    throw new up.Blocked(error.message);
                }
                else {
                    throw error;
                }
            }
        }
        else {
            throw new up.Blocked('Blocked callback: ' + nonceableCallback.script);
        }
    }
    adoptNewFragment(fragment) {
        this._adoptScriptElements(fragment);
        this._adoptAttrCallbacks(fragment);
    }
    adoptDetachedHeadAsset(asset) {
        if (!up.script.isScript(asset))
            return;
        let item = new ScriptElementItem(asset);
        this._detachedAssetPolicy.processItem(item);
    }
    adoptRenderOptionsFromHeader(object) {
        let policy = this._evalCallbackPolicy;
        for (let key of Object.keys(object)) {
            let script = object[key];
            if (/^on[A-Z]/.test(key) && u.isString(script)) {
                let item = new ObjectPropertyItem(object, key);
                policy.processItem(item);
                object[key] = up.RenderOptions.parseCallback(key, object[key]);
            }
        }
    }
    _adoptScriptElements(root) {
        const policy = this._scriptElementPolicy;
        for (let script of up.script.findScripts(root)) {
            let item = new ScriptElementItem(script);
            policy.processItem(item);
        }
    }
    _adoptAttrCallbacks(root) {
        const policy = this._evalCallbackPolicy;
        for (let attribute of up.script.config.nonceableAttributes) {
            let matches = e.subtree(root, e.attrSelector(attribute));
            for (let element of matches) {
                let item = new AttributeItem(element, attribute, policy);
                policy.processItem(item);
            }
        }
    }
};
class Policy {
    constructor(pageNonce, cspInfo) {
        this.pageNonce = pageNonce;
        this.cspInfo = cspInfo;
        this._validNonces = new Set(cspInfo.nonces);
        if (pageNonce)
            this._validNonces.add(pageNonce);
    }
    isValidNonce(nonce) {
        return this._validNonces.has(nonce);
    }
    tryRewriteNonce(allowedItem, nonce = allowedItem.readNonce()) {
        if (this.pageNonce && this.isValidNonce(nonce)) {
            allowedItem.writeNonce(this.pageNonce);
        }
    }
    warnOfUnsafeCSP() {
        throw new up.NotImplemented();
    }
    processItem(item) {
        let nonce = item.readNonce();
        let blocked = !this.passesItem(nonce);
        if (blocked) {
            this.log(...item.logBlockedDescriptor());
            item.block();
        }
        else {
            this.tryRewriteNonce(item, nonce);
        }
    }
    passesItem(_itemNonce) {
        throw new up.NotImplemented();
    }
}
class DetachedAssetPolicy extends Policy {
    constructor(...args) {
        super(...args);
    }
    passesItem(_itemNonce) {
        return true;
    }
}
class ConfigurablePolicy extends Policy {
    constructor(configProp, pageNonce, cspInfo) {
        super(pageNonce, cspInfo);
        this._configProp = configProp;
        let policyString = up.script.config[configProp];
        if (policyString === 'auto')
            policyString = this.resolveAuto();
        if (policyString === 'nonce' && !this.pageNonce) {
            this.warn('Enforcing nonces requires a <meta name="csp-nonce">.');
            policyString = 'block';
        }
        this.policyString = policyString;
    }
    resolveAuto() {
        throw new up.NotImplemented();
    }
    passesItem(itemNonce) {
        switch (this.policyString) {
            case 'pass': return true;
            case 'block': return false;
            case 'nonce': return this.isValidNonce(itemNonce);
            default: up.fail('Unknown policy: %s = %o', this.configExpression(), this.policyString);
        }
    }
    log(...descriptorArgs) {
        up.puts(this.configExpression(), ...descriptorArgs);
    }
    warn(...descriptorArgs) {
        up.warn(this.configExpression(), ...descriptorArgs);
    }
    configExpression() {
        return 'up.script.config.' + this._configProp;
    }
}
class EvalCallbackPolicy extends ConfigurablePolicy {
    constructor(...args) {
        super('evalCallbackPolicy', ...args);
    }
    resolveAuto() {
        if (this.pageNonce) {
            return 'nonce';
        }
        else {
            return 'pass';
        }
    }
    warnOfUnsafeCSP() {
        if (this.policyString === 'pass' && this.cspInfo.isUnsafeEval()) {
            this.warn(`An 'unsafe-eval' CSP allows arbitrary [up-on...] callbacks. Consider setting ${this.configExpression()} = 'nonce'.`);
        }
    }
}
class BodyScriptElementPolicy extends ConfigurablePolicy {
    constructor(...args) {
        super('scriptElementPolicy', ...args);
    }
    resolveAuto() {
        if (this.cspInfo.isStrictDynamic()) {
            return 'nonce';
        }
        else {
            return 'pass';
        }
    }
    warnOfUnsafeCSP() {
        if (this.policyString === 'pass' && this.cspInfo.isStrictDynamic()) {
            this.warn(`A 'strict-dynamic' CSP allows arbitrary <script> elements in new fragments. Consider setting ${this.configExpression()} = 'nonce'.`);
        }
    }
}
class StringCallbackItem {
    readNonce() {
        return this._getCallback().nonce;
    }
    writeNonce(nonce) {
        let callback = this._getCallback();
        callback.nonce = nonce;
        this.writeCallbackString(callback.toString());
    }
    _getCallback() {
        return this._cacheCallback ||= up.NonceableCallback.fromString(this.readCallbackString());
    }
    logBlockedDescriptor() {
        throw new up.NotImplemented();
    }
    block() {
        this.writeCallbackString('/* blocked */');
    }
    readCallbackString() {
        throw new up.NotImplemented();
    }
    writeCallbackString(_newString) {
        throw new up.NotImplemented();
    }
}
class AttributeItem extends StringCallbackItem {
    constructor(element, attribute) {
        super();
        this._element = element;
        this._attribute = attribute;
    }
    logBlockedDescriptor() {
        return ['Blocked callback attribute: %s', e.attrSelector(this._attribute, this.readCallbackString())];
    }
    readCallbackString() {
        return this._element.getAttribute(this._attribute);
    }
    writeCallbackString(newString) {
        this._element.setAttribute(this._attribute, newString);
    }
}
class ObjectPropertyItem extends StringCallbackItem {
    constructor(object, key) {
        super();
        this._object = object;
        this._key = key;
    }
    logBlockedDescriptor() {
        return ['Blocked string callback: { %s: %o }', this._key, this.readCallbackString()];
    }
    readCallbackString() {
        return this._object[this._key];
    }
    writeCallbackString(newString) {
        this._object[this._key] = newString;
    }
}
class ScriptElementItem {
    constructor(element) {
        this._element = element;
    }
    readNonce() {
        return this._element.nonce;
    }
    writeNonce(nonce) {
        this._element.setAttribute('nonce', nonce);
    }
    logBlockedDescriptor() {
        return ['Blocked <script> element: %o', this._element];
    }
    block() {
        up.script.block(this._element);
    }
}


/***/ }),
/* 82 */
/***/ (() => {

const u = up.util;
const e = up.element;
up.Selector = class Selector {
    constructor(selector, elementOrDocument, options = {}) {
        this._filters = [];
        let matchingInExternalDocument = elementOrDocument && !document.contains(elementOrDocument);
        if (!matchingInExternalDocument && !options.destroying) {
            this._filters.push(up.fragment.isNotDestroying);
        }
        this._ignoreLayers = matchingInExternalDocument || options.layer === 'any' || up.layer.count === 1;
        let expandTargetLayer;
        if (this._ignoreLayers) {
            expandTargetLayer = up.layer.root;
        }
        else {
            options.layer ??= u.presence(elementOrDocument, u.isElement);
            this._layers = up.layer.getAll(options);
            if (!this._layers.length)
                throw new up.CannotMatch(["Unknown layer: %o", options.layer]);
            this._filters.push((match) => u.some(this._layers, (layer) => layer.contains(match)));
            expandTargetLayer = this._layers[0];
        }
        this._selectors = up.fragment.expandTargets(selector, { ...options, layer: expandTargetLayer });
        this._unionSelector = this._selectors.join() || 'match-none';
    }
    matches(element) {
        return e.elementLikeMatches(element, this._unionSelector) && this._passesFilter(element);
    }
    closest(element) {
        return this._filterOne(element.closest(this._unionSelector));
    }
    descendants(root = document) {
        return this._filterMany(root.querySelectorAll(this._unionSelector));
    }
    firstDescendant(root) {
        if (this._ignoreLayers) {
            root ||= document;
            return this._firstSelectorMatch((selector) => root.querySelectorAll(selector));
        }
        else {
            return u.findResult(this._layers, (layer) => {
                return this._firstSelectorMatch((selector) => e.subtree(layer.element, selector));
            });
        }
    }
    subtree(root) {
        return this._filterMany(e.subtree(root, this._unionSelector));
    }
    _firstSelectorMatch(fn) {
        return u.findResult(this._selectors, (selector) => {
            return this._filterMany(fn(selector))[0];
        });
    }
    _passesFilter(element) {
        return element && u.every(this._filters, (filter) => filter(element));
    }
    _filterOne(element) {
        return u.presence(element, this._passesFilter.bind(this));
    }
    _filterMany(elements) {
        return u.filter(elements, this._passesFilter.bind(this));
    }
};


/***/ }),
/* 83 */
/***/ (() => {

const u = up.util;
const e = up.element;
up.Tether = class Tether {
    constructor(options) {
        up.migrate.handleTetherOptions?.(options);
        this._anchor = options.anchor;
        this._align = options.align;
        this._position = options.position;
        this._alignAxis = (this._position === 'top') || (this._position === 'bottom') ? 'horizontal' : 'vertical';
        this._viewport = up.viewport.get(this._anchor);
        this.parent = this._viewport === e.root ? document.body : this._viewport;
        this._syncOnScroll = !this._viewport.contains(this._anchor.offsetParent);
    }
    start(element) {
        this._element = element;
        this._element.style.position = 'absolute';
        this._setOffset(0, 0);
        this.sync();
        this._changeEventSubscription('on');
    }
    stop() {
        this._changeEventSubscription('off');
    }
    _changeEventSubscription(fn) {
        let doScheduleSync = this._scheduleSync.bind(this);
        up[fn](window, 'resize', doScheduleSync);
        if (this._syncOnScroll) {
            up[fn](this._viewport, 'scroll', doScheduleSync);
        }
    }
    _scheduleSync() {
        clearTimeout(this.syncTimer);
        return this.syncTimer = u.task(this.sync.bind(this));
    }
    isAlive() {
        return up.fragment.isAlive(this.parent) && up.fragment.isAlive(this._anchor);
    }
    sync() {
        const elementBox = this._element.getBoundingClientRect();
        const elementMargin = {
            top: e.styleNumber(this._element, 'margin-top'),
            right: e.styleNumber(this._element, 'margin-right'),
            bottom: e.styleNumber(this._element, 'margin-bottom'),
            left: e.styleNumber(this._element, 'margin-left')
        };
        const anchorBox = this._anchor.getBoundingClientRect();
        let left;
        let top;
        switch (this._alignAxis) {
            case 'horizontal': {
                switch (this._position) {
                    case 'top':
                        top = anchorBox.top - elementMargin.bottom - elementBox.height;
                        break;
                    case 'bottom':
                        top = anchorBox.top + anchorBox.height + elementMargin.top;
                        break;
                }
                switch (this._align) {
                    case 'left':
                        left = anchorBox.left + elementMargin.left;
                        break;
                    case 'center':
                        left = anchorBox.left + (0.5 * (anchorBox.width - elementBox.width));
                        break;
                    case 'right':
                        left = (anchorBox.left + anchorBox.width) - elementBox.width - elementMargin.right;
                        break;
                }
                break;
            }
            case 'vertical': {
                switch (this._align) {
                    case 'top':
                        top = anchorBox.top + elementMargin.top;
                        break;
                    case 'center':
                        top = anchorBox.top + (0.5 * (anchorBox.height - elementBox.height));
                        break;
                    case 'bottom':
                        top = (anchorBox.top + anchorBox.height) - elementBox.height - elementMargin.bottom;
                        break;
                }
                switch (this._position) {
                    case 'left':
                        left = anchorBox.left - elementMargin.right - elementBox.width;
                        break;
                    case 'right':
                        left = anchorBox.left + anchorBox.width + elementMargin.left;
                        break;
                }
                break;
            }
        }
        if (u.isDefined(left) || u.isDefined(top)) {
            this._moveTo(left, top);
        }
        else {
            up.fail('Invalid tether constraints: %o', this._describeConstraints());
        }
    }
    _describeConstraints() {
        return { position: this._position, align: this._align };
    }
    _moveTo(targetLeft, targetTop) {
        const elementBox = this._element.getBoundingClientRect();
        this._setOffset((targetLeft - elementBox.left) + this.offsetLeft, (targetTop - elementBox.top) + this.offsetTop);
    }
    _setOffset(left, top) {
        this.offsetLeft = left;
        this.offsetTop = top;
        e.setStyle(this._element, { left, top }, 'px');
    }
};


/***/ }),
/* 84 */
/***/ (() => {

const u = up.util;
up.URLPattern = class URLPattern {
    constructor(fullPattern) {
        this._groups = [];
        const positiveList = [];
        const negativeList = [];
        for (let pattern of u.getSimpleTokens(fullPattern)) {
            if (pattern[0] === '-') {
                negativeList.push(pattern.substring(1));
            }
            else {
                positiveList.push(pattern);
            }
        }
        this._positiveRegexp = this._buildRegexp(positiveList, true);
        this._negativeRegexp = this._buildRegexp(negativeList, false);
    }
    _buildRegexp(list, capture) {
        if (!list.length) {
            return;
        }
        list = u.flatMap(list, u.matchableURLPatternAtom);
        list = list.map(u.escapeRegExp);
        let reCode = list.join('|');
        reCode = reCode.replace(/\\\*/g, '.*?');
        reCode = reCode.replace(/(:|\\\$)([a-z][\w-]*)/ig, (match, type, name) => {
            if (type === '\\$') {
                if (capture) {
                    this._groups.push({ name, cast: Number });
                }
                return '(\\d+)';
            }
            else {
                if (capture) {
                    this._groups.push({ name, cast: String });
                }
                return '([^/?#]+)';
            }
        });
        return new RegExp('^(?:' + reCode + ')$');
    }
    test(url, doNormalize = true) {
        if (doNormalize) {
            url = u.matchableURL(url);
        }
        return this._positiveRegexp.test(url) && !this._isExcluded(url);
    }
    recognize(url, doNormalize = true) {
        if (doNormalize) {
            url = u.matchableURL(url);
        }
        let match = this._positiveRegexp.exec(url);
        if (match && !this._isExcluded(url)) {
            const resolution = {};
            this._groups.forEach((group, groupIndex) => {
                let value = match[groupIndex + 1];
                if (value) {
                    return resolution[group.name] = group.cast(value);
                }
            });
            return resolution;
        }
    }
    _isExcluded(url) {
        return this._negativeRegexp?.test(url);
    }
};


/***/ }),
/* 85 */
/***/ (() => {

up.framework = (function () {
    let readyState = 'evaling';
    function emitReset() {
        up.emit('up:framework:reset', { log: false });
    }
    function boot({ mode = 'manual' } = {}) {
        if (readyState !== 'configuring') {
            console.error('Unpoly has already booted');
            return;
        }
        let issue = supportIssue();
        if (!issue) {
            readyState = 'booting';
            up.emit('up:framework:boot', { mode, log: false });
            readyState = 'booted';
            up.emit('up:framework:booted', { mode, log: false });
        }
        else {
            console.error("Unpoly cannot boot: %s", issue);
        }
    }
    function mustManualBoot() {
        if (document.currentScript?.async) {
            return true;
        }
        if (document.querySelector('[up-boot=manual]:is(html, script)')) {
            return true;
        }
        if (document.readyState === 'complete') {
            return true;
        }
    }
    function onEvaled() {
        up.emit('up:framework:evaled', { log: false });
        if (mustManualBoot()) {
            console.debug('Call up.boot() after you have configured Unpoly');
        }
        else {
            document.addEventListener('DOMContentLoaded', () => boot({ mode: 'auto' }));
        }
        readyState = 'configuring';
    }
    function startExtension() {
        if (readyState !== 'configuring') {
            throw new Error('Unpoly extensions must be loaded before booting');
        }
        readyState = 'evaling';
    }
    function stopExtension() {
        readyState = 'configuring';
    }
    function isSupported() {
        return !supportIssue();
    }
    function supportIssue() {
        for (let feature of ['Promise', 'DOMParser', 'FormData', 'reportError']) {
            if (!window[feature]) {
                return `Browser doesn't support the ${feature} API`;
            }
        }
        if (document.compatMode === 'BackCompat') {
            return 'Browser is in quirks mode (missing DOCTYPE?)';
        }
        for (let selector of [':is(*)', ':has(*)']) {
            if (!CSS.supports(`selector(${selector})`)) {
                return `Browser doesn't support the ${selector} selector`;
            }
        }
    }
    return {
        onEvaled,
        boot,
        startExtension,
        stopExtension,
        reset: emitReset,
        get evaling() { return readyState === 'evaling'; },
        get booted() { return readyState === 'booted'; },
        get beforeBoot() { return readyState !== 'booting' && readyState !== 'booted'; },
        isSupported,
    };
})();
up.boot = up.framework.boot;


/***/ }),
/* 86 */
/***/ (() => {

up.event = (function () {
    const u = up.util;
    const e = up.element;
    function reset() {
        for (let globalElement of [window, document, e.root, document.body]) {
            for (let listener of up.EventListener.allNonDefault(globalElement)) {
                listener.unbind();
            }
        }
    }
    function on(...args) {
        return buildListenerGroup(args).bind();
    }
    function onClosest(fragment, eventType, callback) {
        let guard = (event) => event.target.contains(fragment);
        let unsubscribe = up.on(eventType, { guard }, callback);
        up.destructor(fragment, unsubscribe);
        return unsubscribe;
    }
    function off(...args) {
        return buildListenerGroup(args).unbind();
    }
    function buildListenerGroup(args, options) {
        return up.EventListenerGroup.fromBindArgs(args, options);
    }
    function buildEmitter(args) {
        return up.EventEmitter.fromEmitArgs(args);
    }
    function emit(...args) {
        return buildEmitter(args).emit();
    }
    function build(...args) {
        const props = u.extractOptions(args);
        const type = args[0] || props.type || up.fail('Missing event type');
        const event = new Event(type, { bubbles: true, cancelable: true });
        Object.assign(event, u.omit(props, ['type', 'target']));
        return event;
    }
    function assertEmitted(...args) {
        return buildEmitter(args).assertEmitted();
    }
    function onEscape(listener) {
        return on('keydown', function (event) {
            if (event.key === 'Escape') {
                return listener(event);
            }
        });
    }
    function halt(event, options = {}) {
        if (options.log)
            up.log.putsEvent(event);
        event.stopImmediatePropagation();
        event.preventDefault();
    }
    const keyModifiers = ['metaKey', 'shiftKey', 'ctrlKey', 'altKey'];
    function isModified(event) {
        return (event.button > 0) || u.some(keyModifiers, (modifier) => event[modifier]);
    }
    function isSyntheticClick(event) {
        return u.isMissing(event.clientX);
    }
    function fork(originalEvent, newType, copyKeys = []) {
        const newEvent = build(newType, u.pick(originalEvent, copyKeys));
        newEvent.originalEvent = originalEvent;
        ['stopPropagation', 'stopImmediatePropagation', 'preventDefault'].forEach(function (key) {
            const originalMethod = newEvent[key];
            return newEvent[key] = function () {
                originalEvent[key]();
                return originalMethod.call(newEvent);
            };
        });
        if (originalEvent.defaultPrevented) {
            newEvent.preventDefault();
        }
        return newEvent;
    }
    function executeEmitAttr(event, element) {
        if (isModified(event)) {
            return;
        }
        const eventType = e.attr(element, 'up-emit');
        const eventProps = e.jsonAttr(element, 'up-emit-props');
        const forkedEvent = fork(event, eventType);
        Object.assign(forkedEvent, eventProps);
        up.emit(element, forkedEvent);
    }
    on('up:click', '[up-emit]', executeEmitAttr);
    let inputDevices = ['unknown'];
    function getInputDevice() {
        return u.last(inputDevices);
    }
    function observeInputDevice(newModality) {
        inputDevices.push(newModality);
        setTimeout(() => inputDevices.pop());
    }
    on('keydown keyup', { capture: true }, () => observeInputDevice('key'));
    on('pointerdown pointerup', { capture: true }, () => observeInputDevice('pointer'));
    on('up:framework:reset', reset);
    return {
        on,
        onClosest,
        off,
        build,
        emit,
        assertEmitted,
        onEscape,
        halt,
        isModified,
        isSyntheticClick,
        fork,
        keyModifiers,
        get inputDevice() { return getInputDevice(); }
    };
})();
up.on = up.event.on;
up.off = up.event.off;
up.emit = up.event.emit;


/***/ }),
/* 87 */
/***/ (() => {

up.protocol = (function () {
    const u = up.util;
    const e = up.element;
    const headerize = function (camel) {
        const header = camel.replace(/(^.|[A-Z])/g, (char) => '-' + char.toUpperCase());
        return 'X-Up' + header;
    };
    const extractHeader = function (xhr, shortHeader, parseFn = u.identity) {
        let value = xhr.getResponseHeader(headerize(shortHeader));
        if (value) {
            return parseFn(value);
        }
    };
    function targetFromXHR(xhr) {
        return extractHeader(xhr, 'target');
    }
    function parseModifyCacheValue(value) {
        if (value === 'false') {
            return false;
        }
        else {
            return value;
        }
    }
    function evictCacheFromXHR(xhr) {
        return extractHeader(xhr, 'evictCache', parseModifyCacheValue);
    }
    function expireCacheFromXHR(xhr) {
        return extractHeader(xhr, 'expireCache') || up.migrate.clearCacheFromXHR?.(xhr);
    }
    function contextFromXHR(xhr) {
        return extractHeader(xhr, 'context', u.parseRelaxedJSON);
    }
    function methodFromXHR(xhr) {
        return extractHeader(xhr, 'method', u.normalizeMethod);
    }
    function titleFromXHR(xhr) {
        return up.migrate.titleFromXHR?.(xhr) ?? extractHeader(xhr, 'title', u.parseRelaxedJSON);
    }
    function eventPlansFromXHR(xhr) {
        return extractHeader(xhr, 'events', u.parseRelaxedJSON);
    }
    function openLayerFromXHR(xhr) {
        return extractHeader(xhr, 'openLayer', u.parseRelaxedJSON);
    }
    function acceptLayerFromXHR(xhr) {
        return extractHeader(xhr, 'acceptLayer', u.parseRelaxedJSON);
    }
    function dismissLayerFromXHR(xhr) {
        return extractHeader(xhr, 'dismissLayer', u.parseRelaxedJSON);
    }
    const initialRequestMethod = u.memoize(function () {
        return u.normalizeMethod(up.browser.popCookie('_up_method'));
    });
    function locationFromXHR(xhr) {
        let location = extractHeader(xhr, 'location') || xhr.responseURL;
        if (location) {
            return u.normalizeURL(location);
        }
    }
    const config = new up.Config(() => ({
        methodParam: '_method',
        csrfParam() { return e.metaContent('csrf-param'); },
        csrfToken() { return e.metaContent('csrf-token'); },
        csrfHeader: 'X-CSRF-Token',
        maxHeaderSize: 2048,
    }));
    function csrfHeader() {
        return u.evalOption(config.csrfHeader);
    }
    function csrfParam() {
        return u.evalOption(config.csrfParam);
    }
    function csrfToken() {
        return u.evalOption(config.csrfToken);
    }
    function wrapMethod(method, params) {
        params.add(config.methodParam, method);
        return 'POST';
    }
    return {
        config,
        locationFromXHR,
        titleFromXHR,
        targetFromXHR,
        methodFromXHR,
        openLayerFromXHR,
        acceptLayerFromXHR,
        contextFromXHR,
        dismissLayerFromXHR,
        eventPlansFromXHR,
        expireCacheFromXHR,
        evictCacheFromXHR,
        csrfHeader,
        csrfParam,
        csrfToken,
        initialRequestMethod,
        headerize,
        wrapMethod,
    };
})();


/***/ }),
/* 88 */
/***/ (() => {

up.log = (function () {
    const u = up.util;
    const config = new up.LogConfig();
    function printToStandard(...args) {
        if (config.enabled) {
            printToStream('log', ...args);
        }
    }
    const printToWarn = (...args) => printToStream('warn', ...args);
    const printToError = (...args) => printToStream('error', ...args);
    function printToStream(stream, prefix, message, ...args) {
        printToStreamStyled(stream, prefix, '', message, ...args);
    }
    function printToStreamStyled(stream, prefix, customStyles, message, ...args) {
        if (message) {
            if (config.format) {
                console[stream](`%c${prefix}%c ${message}`, 'color: #666666; padding: 1px 3px; border: 1px solid #bbbbbb; border-radius: 2px; font-size: 90%; display: inline-block;' + customStyles, '', ...args);
            }
            else {
                console[stream](`[${prefix}] ${u.sprintf(message, ...args)}`);
            }
        }
    }
    let lastPrintedUserEvent;
    function printUserEvent(event) {
        if (config.enabled && lastPrintedUserEvent !== event) {
            lastPrintedUserEvent = event;
            let originalEvent = event.originalEvent || event;
            let color = '#5566cc';
            printToStreamStyled('log', originalEvent.type, `color: white; border-color: ${color}; background-color: ${color}`, 'Interaction on %o', originalEvent.target);
        }
    }
    function printBanner() {
        if (!config.banner) {
            return;
        }
        const logo = " __ _____  ___  ___  / /_ __\n" +
            `/ // / _ \\/ _ \\/ _ \\/ / // /  ${up.version}\n` +
            "\\___/_//_/ .__/\\___/_/\\_. / \n" +
            "        / /            / /\n\n";
        let text = "";
        if (!up.migrate.loaded) {
            text += "Load unpoly-migrate.js to polyfill deprecated APIs.\n\n";
        }
        if (config.enabled) {
            text += "Call `up.log.disable()` to disable logging for this session.";
        }
        else {
            text += "Call `up.log.enable()` to enable logging for this session.";
        }
        const color = 'color: #777777';
        if (config.format) {
            console.log('%c' + logo + '%c' + text, 'font-family: monospace;' + color, color);
        }
        else {
            console.log(logo + text);
        }
    }
    up.on('up:framework:boot', printBanner);
    function enable() {
        config.enabled = true;
    }
    function disable() {
        config.enabled = false;
    }
    return {
        puts: printToStandard,
        putsEvent: printUserEvent,
        error: printToError,
        warn: printToWarn,
        config,
        enable,
        disable,
    };
})();
up.puts = up.log.puts;
up.warn = up.log.warn;


/***/ }),
/* 89 */
/***/ (() => {

up.script = (function () {
    const u = up.util;
    const e = up.element;
    const config = new up.Config(() => ({
        cspNonce() { return e.metaContent('csp-nonce'); },
        cspWarnings: true,
        scriptElementPolicy: 'auto',
        evalCallbackPolicy: 'auto',
        assetSelectors: [
            'link[rel=stylesheet]',
            'script[src]',
            '[up-asset]'
        ],
        noAssetSelectors: [
            '[up-asset=false]',
        ],
        nonceableAttributes: [
            'up-watch',
            'up-on-keep',
            'up-on-hungry',
            'up-on-opened',
            'up-on-accepted',
            'up-on-dismissed',
            'up-on-loaded',
            'up-on-rendered',
            'up-on-finished',
            'up-on-error',
            'up-on-offline',
        ],
        scriptSelectors: [
            'script:not([type])',
            'script[type="text/javascript"]',
            'script[type="module"]',
            'script[type="importmap"]',
        ],
        noScriptSelectors: [
            'script[type="application/ld+json"]'
        ]
    }));
    const SYSTEM_MACRO_PRIORITIES = {
        '[up-back]': -100,
        '[up-clickable]': -200,
        '[up-drawer]': -200,
        '[up-modal]': -200,
        '[up-cover]': -200,
        '[up-popup]': -200,
        '[up-tooltip]': -200,
        '[up-dash]': -200,
        '[up-flashes]': -200,
        '[up-expand]': -300,
        '[data-method]': -400,
        '[data-confirm]': -400,
        '[up-keep]': 9999999999,
    };
    let registeredCompilers = [];
    let registeredMacros = [];
    function registerCompiler(...args) {
        registerProcessor(args);
    }
    function registerMacro(...args) {
        registerProcessor(args, { macro: true });
    }
    function registerAttrCompiler(...args) {
        let [attr, options, valueCallback] = parseProcessorArgs(args);
        let selector = `[${attr}]`;
        let { defaultValue } = options;
        let callback = (element) => {
            let value = e.booleanOrStringAttr(element, attr);
            if (value === false)
                return;
            if (u.isDefined(defaultValue) && value === true)
                value = defaultValue;
            return valueCallback(element, value);
        };
        registerProcessor([selector, options, callback]);
    }
    function detectSystemMacroPriority(macroSelector) {
        macroSelector = u.evalOption(macroSelector);
        for (let substr in SYSTEM_MACRO_PRIORITIES) {
            if (macroSelector.indexOf(substr) >= 0) {
                return SYSTEM_MACRO_PRIORITIES[substr];
            }
        }
        up.fail('Unregistered priority for system macro %o', macroSelector);
    }
    function registerProcessor(args, overrides = {}) {
        let processor = buildProcessor(args, overrides);
        if (processor.macro) {
            if (up.framework.evaling) {
                processor.priority ||= detectSystemMacroPriority(processor.selector);
            }
            insertProcessor(registeredMacros, processor);
        }
        else {
            insertProcessor(registeredCompilers, processor);
        }
    }
    const parseProcessorArgs = function (args) {
        return u.args(args, 'val', 'options', 'callback');
    };
    function buildProcessor(args, overrides) {
        let [selector, options, callback] = parseProcessorArgs(args);
        options = u.options(options, {
            selector,
            isDefault: up.framework.evaling,
            priority: 0,
            batch: false,
            rerun: false,
        });
        return Object.assign(callback, options, overrides);
    }
    function insertProcessor(queue, newCompiler) {
        let existingCompiler;
        let index = 0;
        while ((existingCompiler = queue[index]) && (existingCompiler.priority >= newCompiler.priority)) {
            index += 1;
        }
        queue.splice(index, 0, newCompiler);
        if (up.framework.booted) {
            if (newCompiler.priority === 0) {
                for (let layer of up.layer.stack) {
                    hello(layer.element, { layer, compilers: [newCompiler], macros: [], insertedEvent: false });
                }
            }
            else {
                up.puts('up.compiler()', 'Compiler with priority (%s) was registered after booting Unpoly. Compiler will run for future fragments only.', newCompiler.selector);
            }
        }
        return newCompiler;
    }
    function registerDestructor(element, value) {
        let fns = u.scanFunctions(value);
        if (!fns.length)
            return;
        if (element.isConnected) {
            let registry = (element.upDestructors ||= buildDestructorRegistry(element));
            registry.guard(fns);
        }
        else {
            up.puts('up.destructor()', 'Immediately calling destructor for detached element (%o)', element);
            for (let fn of fns)
                up.error.guard(fn, element);
        }
    }
    function buildDestructorRegistry(element) {
        let registry = u.cleaner();
        registry(e.addClassTemp(element, 'up-can-clean'));
        return registry;
    }
    function hello(element, options = {}) {
        element = up.fragment.get(element, options);
        let macros = options.macros ?? registeredMacros;
        let compilers = options.compilers ?? registeredCompilers;
        const pass = new up.HelloFragment(element, macros, compilers, options);
        return pass.run();
    }
    function clean(fragment, options = {}) {
        new up.DestructorPass(fragment, options).run();
    }
    function readData(element) {
        element = up.fragment.get(element);
        return element.upData ||= buildData(element);
    }
    function buildData(element) {
        let parsedJSON = e.jsonAttr(element, 'up-data') ?? {};
        if (!u.isOptions(parsedJSON)) {
            return parsedJSON;
        }
        return {
            ...element.upTemplateData,
            ...element.dataset,
            ...parsedJSON,
            ...element.upCompileData,
        };
    }
    function findAssets(head = document.head) {
        return head.querySelectorAll(config.selector('assetSelectors'));
    }
    function assertAssetsOK(newAssets, renderOptions) {
        let { response } = renderOptions;
        let oldAssets = findAssets();
        if (assetsIdentity(oldAssets) !== assetsIdentity(newAssets)) {
            up.event.assertEmitted('up:assets:changed', { oldAssets, newAssets, renderOptions, response });
        }
    }
    function assetsIdentity(assets) {
        return u.map(assets, assetIdentity).join();
    }
    function assetIdentity(assetElement) {
        return e.removeAttrsFromHTML(assetElement.outerHTML, ['nonce']);
    }
    function block(root) {
        for (let script of findScripts(root)) {
            script.type = 'up-blocked-script';
        }
    }
    function findScripts(root, condition = '') {
        let selector = config.selector('scriptSelectors', condition);
        return e.subtree(root, selector);
    }
    function isScript(value) {
        return config.matches(value, 'scriptSelectors');
    }
    function adoptNewFragment(fragment, cspInfo) {
        new up.ScriptGate(cspInfo).adoptNewFragment(fragment);
    }
    function adoptDetachedHeadAsset(script, cspInfo) {
        new up.ScriptGate(cspInfo).adoptDetachedHeadAsset(script);
    }
    function adoptRenderOptionsFromHeader(renderOptions, cspInfo) {
        new up.ScriptGate(cspInfo).adoptRenderOptionsFromHeader(renderOptions);
    }
    function callbackAttr(element, attrName, parseOpts) {
        return e.parseAttr(element, attrName, (code) => {
            let fn = parseCallback(code, parseOpts);
            return fn.bind(element);
        });
    }
    function parseCallback(code, { argNames = ['event'], expandObject = false } = {}) {
        return function (...argValues) {
            if (expandObject) {
                let object = argValues[0];
                argNames = [...argNames, ...expandObject];
                argValues = [object, ...Object.values(u.pick(object, expandObject))];
            }
            const nonceableCallback = up.NonceableCallback.fromString(code);
            const evalEnv = { thisContext: this, argNames, argValues };
            return new up.ScriptGate().evalCallback(nonceableCallback, evalEnv);
        };
    }
    function cspNonce() {
        return u.evalOption(config.cspNonce);
    }
    function warnOfUnsafeCSP(cspInfo) {
        new up.ScriptGate(cspInfo).warnOfUnsafeCSP();
    }
    function reset() {
        registeredCompilers = u.filter(registeredCompilers, 'isDefault');
        registeredMacros = u.filter(registeredMacros, 'isDefault');
    }
    up.on('up:framework:reset', reset);
    return {
        config,
        compiler: registerCompiler,
        macro: registerMacro,
        attrCompiler: registerAttrCompiler,
        destructor: registerDestructor,
        hello,
        clean,
        data: readData,
        findAssets,
        assertAssetsOK,
        block,
        adoptNewFragment,
        adoptRenderOptionsFromHeader,
        adoptDetachedHeadAsset,
        parseCallback,
        cspNonce,
        warnOfUnsafeCSP,
        callbackAttr,
        isScript,
        findScripts,
    };
})();
up.compiler = up.script.compiler;
up.destructor = up.script.destructor;
up.macro = up.script.macro;
up.data = up.script.data;
up.hello = up.script.hello;
up.attribute = up.script.attrCompiler;


/***/ }),
/* 90 */
/***/ (() => {

up.history = (function () {
    const u = up.util;
    const e = up.element;
    const config = new up.Config(() => ({
        enabled: true,
        updateMetaTags: true,
        restoreTargets: ['body'],
        metaTagSelectors: [
            'meta',
            'link[rel=alternate]',
            'link[rel=canonical]',
            'link[rel=icon]',
            '[up-meta]',
            'script[type="application/ld+json"]',
        ],
        noMetaTagSelectors: [
            'meta[http-equiv]',
            '[up-meta=false]',
            'meta[name=csp-nonce]',
        ],
    }));
    let previousLocation;
    let nextPreviousLocation;
    let nextTrackOptions;
    let adoptedBases = new up.FIFOCache({ capacity: 100, normalizeKey: getBase });
    function reset() {
        previousLocation = undefined;
        nextPreviousLocation = undefined;
        nextTrackOptions = undefined;
        adoptedBases.clear();
        trackCurrentLocation({ reason: null, alreadyHandled: true });
        adoptBase();
    }
    function refineOption(existingValue, newValue) {
        if ((existingValue === false) || u.isString(existingValue)) {
            return existingValue;
        }
        else {
            return newValue;
        }
    }
    function historyOptions(options) {
        return u.pick(options, [
            'location',
            'title',
            'metaTags',
            'lang'
        ]);
    }
    function currentLocation() {
        return u.normalizeURL(location.href);
    }
    function withTrackOptions(trackOptions, fn) {
        try {
            nextTrackOptions = trackOptions;
            fn();
        }
        finally {
            nextTrackOptions = undefined;
        }
    }
    function trackCurrentLocation(trackOptions) {
        let { reason, alreadyHandled, pauseTracking } = nextTrackOptions || trackOptions;
        if (pauseTracking)
            return;
        let location = currentLocation();
        if (isAdoptedState()) {
            adoptBase(location);
        }
        else if (isAdoptedBase(location)) {
            adoptState();
        }
        if (nextPreviousLocation !== location) {
            previousLocation = nextPreviousLocation;
            nextPreviousLocation = location;
            if (reason === 'detect') {
                reason = (getBase(location) === getBase(previousLocation)) ? 'hash' : 'pop';
            }
            let willHandle = !alreadyHandled && isAdoptedBase(location);
            let locationChangedEvent = up.event.build('up:location:changed', {
                reason,
                location,
                previousLocation,
                alreadyHandled,
                willHandle,
                log: `New location is ${location}`
            });
            up.migrate.prepareLocationChangedEvent?.(locationChangedEvent);
            if (reason) {
                up.emit(locationChangedEvent);
                reactToChange(locationChangedEvent);
            }
        }
    }
    function splitLocation(location) {
        return location?.split(/(?=#)/) || [];
    }
    function getBase(location) {
        return splitLocation(location)[0];
    }
    function isLocation(url, options) {
        return u.matchURLs(url, location.href, { hash: true, ...options });
    }
    function replace(location, trackOptions) {
        placeAdoptedHistoryEntry('replaceState', location, trackOptions);
    }
    function push(location, trackOptions) {
        if (isLocation(location))
            return;
        placeAdoptedHistoryEntry('pushState', location, trackOptions);
    }
    function placeAdoptedHistoryEntry(method, location, trackOptions) {
        adoptBase(location);
        if (config.enabled) {
            withTrackOptions(trackOptions, function () {
                history[method](null, { up: true }, location);
            });
        }
    }
    function isAdoptedBase(location) {
        return !!adoptedBases.get(location);
    }
    function adoptBase(location = currentLocation()) {
        location = u.normalizeURL(location);
        adoptedBases.set(location, true);
    }
    function isAdoptedState() {
        return history.state?.up;
    }
    function adoptState() {
        let { state } = history;
        if (isAdoptedState())
            return;
        if (u.isBlank(state) || u.isObject(state)) {
            withTrackOptions({ pauseTracking: true }, function () {
                history.replaceState({ ...state, up: true }, '');
            });
        }
    }
    function restoreLocation(location) {
        up.error.muteUncriticalRejection(up.render({
            guardEvent: up.event.build('up:location:restore', { location, log: `Restoring location ${location}` }),
            url: location,
            target: config.restoreTargets,
            fail: false,
            history: true,
            location,
            peel: true,
            layer: 'root',
            cache: 'auto',
            revalidate: 'auto',
            saveScroll: false,
            scroll: ['restore', 'auto'],
            saveFocus: false,
            focus: ['restore', 'auto'],
        }));
    }
    function reactToChange(event) {
        if (event.alreadyHandled) {
            return;
        }
        if (!event.willHandle) {
            up.puts('up.history', 'Ignoring history entry owned by foreign script');
            return;
        }
        if (event.reason === 'pop') {
            up.viewport.saveFocus({ location: event.previousLocation });
            up.viewport.saveScroll({ location: event.previousLocation });
            restoreLocation(event.location);
        }
        else if (event.reason === 'hash') {
            up.viewport.revealHash(location.hash, { strong: true });
        }
    }
    function findMetaTags(head = document.head) {
        return head.querySelectorAll(config.selector('metaTagSelectors'));
    }
    function updateMetaTags(newMetaTags) {
        let oldMetaTags = findMetaTags();
        for (let oldMetaTag of oldMetaTags) {
            oldMetaTag.remove();
        }
        for (let newMetaTag of newMetaTags) {
            document.head.append(newMetaTag);
        }
    }
    function getLang(doc = document) {
        let { documentElement } = doc;
        if (documentElement.matches('html')) {
            return doc.documentElement.lang;
        }
    }
    function updateLang(newLang) {
        e.setAttrPresence(e.root, 'lang', newLang, !!newLang);
    }
    function patchHistoryAPI() {
        const originalPushState = history.pushState;
        history.pushState = function (...args) {
            originalPushState.apply(this, args);
            trackCurrentLocation({ reason: 'push', alreadyHandled: true });
        };
        const originalReplaceState = history.replaceState;
        history.replaceState = function (...args) {
            originalReplaceState.apply(this, args);
            trackCurrentLocation({ reason: 'replace', alreadyHandled: true });
        };
    }
    function adoptInitialHistoryEntry() {
        if (up.protocol.initialRequestMethod() === 'GET') {
            adoptState();
            adoptBase();
        }
    }
    up.on('up:framework:boot', function ({ mode }) {
        trackCurrentLocation({ reason: null, alreadyHandled: true });
        patchHistoryAPI();
        adoptInitialHistoryEntry();
        if (mode === 'auto') {
            up.viewport.revealHash(location.hash, { strong: true, focus: true });
        }
    });
    up.on(window, 'hashchange, popstate', () => {
        trackCurrentLocation({ reason: 'detect', alreadyHandled: false });
    });
    function onJumpLinkClicked(event, link) {
        if (event.defaultPrevented)
            return;
        if (up.event.isModified(event))
            return;
        let [currentBase, currentHash] = splitLocation(up.layer.current.location);
        let [linkBase, linkHash] = splitLocation(u.normalizeURL(link));
        let verbatimHREF = link.getAttribute('href');
        let isJumpLink = (currentBase === linkBase) || verbatimHREF.startsWith('#');
        if (!isJumpLink)
            return;
        let behavior = link.getAttribute('up-scroll-behavior') ?? 'auto';
        let layer = up.layer.get(link);
        let revealFn = up.viewport.revealHashFn(linkHash, { layer, behavior, focus: true });
        if (revealFn) {
            up.event.halt(event);
            up.log.putsEvent(event);
            if (linkHash !== currentHash && layer.showsLiveHistory()) {
                let newHREF = currentBase + linkHash;
                push(newHREF, { reason: 'hash', alreadyHandled: true });
            }
            revealFn();
        }
        else {
        }
    }
    up.on('up:click', 'a[href*="#"]', onJumpLinkClicked);
    up.macro('[up-back]', function (link) {
        if (previousLocation) {
            e.setMissingAttrs(link, {
                'up-href': previousLocation,
                'up-scroll': 'restore'
            });
            link.removeAttribute('up-back');
            up.link.makeFollowable(link);
        }
    });
    up.on('up:framework:reset', reset);
    return {
        config,
        push,
        replace,
        get location() { return currentLocation(); },
        get previousLocation() { return previousLocation; },
        isLocation,
        findMetaTags,
        updateMetaTags,
        getLang,
        updateLang,
        refineOption,
        options: historyOptions,
    };
})();


/***/ }),
/* 91 */
/***/ ((__unused_webpack_module, __unused_webpack_exports, __webpack_require__) => {

__webpack_require__(92);
const u = up.util;
const e = up.element;
up.fragment = (function () {
    function upTagName(element) {
        let tagName = e.tagName(element);
        if (tagName.startsWith('up-')) {
            return tagName;
        }
    }
    const STRONG_TARGET_DERIVERS = [
        '[up-id]',
        '[id]',
        'html',
        'head',
        'body',
    ];
    const config = new up.Config(() => ({
        badTargetClasses: [/^up-/],
        strongTargetDerivers: STRONG_TARGET_DERIVERS,
        targetDerivers: [
            ...STRONG_TARGET_DERIVERS,
            'main',
            '[up-main]',
            upTagName,
            'link[rel][type]',
            'link[rel=preload][href]',
            'link[rel=preconnect][href]',
            'link[rel=prefetch][href]',
            'link[rel]',
            'meta[property]',
            '*[name]',
            'form[action]',
            'a[href]',
            '[class]',
            '[up-flashes]',
            'form',
        ],
        verifyDerivedTarget: true,
        renderOptions: {
            hungry: true,
            keep: true,
            saveScroll: true,
            saveFocus: true,
            focusVisible: 'auto',
            abort: 'target',
            failOptions: true,
            feedback: true,
        },
        navigateOptions: {
            cache: 'auto',
            revalidate: 'auto',
            fallback: true,
            focus: 'auto',
            scroll: 'auto',
            history: 'auto',
            peel: 'dismiss',
        },
        reloadOptions: {
            target: ':main',
            scroll: 'keep',
            focus: 'keep',
        },
        match: 'region',
        autoHistoryTargets: [':main'],
        autoFocus: ['hash', 'autofocus', 'main-if-main', 'keep', 'target-if-lost'],
        autoScroll: ['hash', 'layer-if-main'],
        autoRevalidate: (response) => response.expired,
        skipResponse: defaultSkipResponse,
        renderableResponse: (response) => response.isHTML(),
        normalizeKeepHTML: defaultNormalizeKeepHTML
    }));
    u.delegate(config, ['mainTargets'], () => up.layer.config.any);
    function defaultSkipResponse({ response, expiredResponse }) {
        return !response.text || response.text === expiredResponse?.text;
    }
    function sourceOf(element, options = {}) {
        element = getSmart(element, options);
        return e.closestAttr(element, 'up-source');
    }
    function normalizeSource(source) {
        return u.normalizeURL(source, { hash: false });
    }
    function timeOf(element) {
        let value = e.closestAttr(element, 'up-time');
        if (value && value !== 'false') {
            if (/^\d+$/.test(value)) {
                value = Number(value) * 1000;
            }
            return new Date(value);
        }
    }
    function etagOf(element) {
        let value = e.closestAttr(element, 'up-etag');
        if (value && value !== 'false') {
            return value;
        }
    }
    const render = up.mockable((...args) => {
        let options = parseTargetAndOptions(args);
        return new up.RenderJob(options).execute();
    });
    const navigate = up.mockable((...args) => {
        const options = parseTargetAndOptions(args);
        return render({ ...options, navigate: true });
    });
    function emitFragmentKeep({ oldElement, newElement: newFragment, newData, renderOptions }) {
        const log = ['Keeping fragment %o', oldElement];
        const callback = up.script.callbackAttr(oldElement, 'up-on-keep', { expandObject: ['newFragment', 'newData'] });
        return up.emit(oldElement, 'up:fragment:keep', { log, callback, newFragment, newData, renderOptions });
    }
    function emitFragmentKept({ oldElement, newElement: newFragment, newData }) {
        return up.emit(oldElement, 'up:fragment:kept', { log: false, newFragment, newData });
    }
    function findKeepPlan(options) {
        if (options.keep === false)
            return;
        const { oldElement, newElement } = options;
        let oldElementMode = keepMode(oldElement);
        if (!oldElementMode) {
            return;
        }
        let partner;
        let partnerSelector = up.fragment.tryToTarget(oldElement);
        if (!partnerSelector) {
            up.warn('[up-keep]', 'Cannot keep untargetable %o', oldElement);
        }
        const lookupOpts = { layer: options.layer };
        if (options.descendantsOnly) {
            partner = up.fragment.get(newElement, partnerSelector, lookupOpts);
        }
        else {
            partner = e.subtreeFirst(newElement, partnerSelector, lookupOpts);
        }
        if (!partner)
            return;
        let partnerMode = keepMode(partner);
        if (partnerMode === false)
            return;
        let oldIdentity = keepIdentity(oldElement, oldElementMode);
        let partnerIdentity = keepIdentity(partner, oldElementMode);
        if (!u.isEqual(oldIdentity, partnerIdentity))
            return;
        const plan = {
            oldElement,
            newElement: partner,
            newData: up.script.data(partner),
            renderOptions: options,
        };
        if (emitFragmentKeep(plan).defaultPrevented)
            return;
        return plan;
    }
    function keepIdentity(element, mode = keepMode(element)) {
        return element.upKeepIdentity ??= u.copy(buildKeepIdentity(element, mode));
    }
    function defaultNormalizeKeepHTML(html) {
        html = e.removeAttrsFromHTML(html, ['up-etag', 'up-source', 'up-time', 'nonce', ...up.script.config.nonceableAttributes]);
        html = html.replace(/^[ \t]+/mg, '');
        return html;
    }
    function buildKeepIdentity(element, mode) {
        if (mode === 'same-html') {
            return config.normalizeKeepHTML(element.outerHTML);
        }
        else if (mode === 'same-data') {
            return up.data(element);
        }
        else {
            return true;
        }
    }
    up.macro('[up-keep]', (element) => keepIdentity(element));
    function keepMode(element) {
        return e.booleanOrStringAttr(element, 'up-keep');
    }
    function emitFragmentInserted(element, meta) {
        if (element.upInserted)
            return;
        element.upInserted = true;
        const log = ['Inserted fragment %o', element];
        return mutate(() => up.emit(element, 'up:fragment:inserted', { ...meta, log }));
    }
    function emitFragmentDestroyed(fragment, options) {
        const log = options.log ?? ['Destroyed fragment %o', fragment];
        const parent = options.parent || document;
        return mutate(() => up.emit(parent, 'up:fragment:destroyed', { fragment, parent, log }));
    }
    function isNotDestroying(element) {
        return !element.closest('.up-destroying');
    }
    function isAlive(fragment) {
        return fragment.isConnected && isNotDestroying(fragment);
    }
    function getSmart(...args) {
        let [root, selector, options] = parseGetArgs(args);
        if (u.isElementLike(selector)) {
            return e.get(selector);
        }
        if (root) {
            return getFirstDescendant(root, selector, options);
        }
        return new up.FragmentFinder({
            selector,
            ...u.pick(options, ['layer', 'match', 'origin', 'destroying']),
        }).find();
    }
    function getFirstDescendant(...args) {
        let [root, selectorString, options] = parseGetArgs(args);
        let selector = new up.Selector(selectorString, root, options);
        return selector.firstDescendant(root);
    }
    function parseGetArgs(args) {
        return u.args(args, 'val', 'val', 'options');
    }
    function getAll(...args) {
        let [root, selectorString, options] = parseGetArgs(args);
        if (u.isElement(selectorString)) {
            return [selectorString];
        }
        if (u.isList(selectorString)) {
            return selectorString;
        }
        let selector = new up.Selector(selectorString, root, options);
        return selector.descendants(root);
    }
    function getSubtree(element, selector, options = {}) {
        return new up.Selector(selector, element, options).subtree(element);
    }
    function contains(root, selectorOrElement) {
        if (u.isElement(selectorOrElement)) {
            return e.contains(root, selectorOrElement) && up.layer.get(root).contains(selectorOrElement);
        }
        else {
            return getSubtree(root, selectorOrElement).length > 0;
        }
    }
    function closest(element, selector, options) {
        return new up.Selector(selector, element, options).closest(element);
    }
    function destroy(...args) {
        const options = parseTargetAndOptions(args);
        const element = getSmart(options.target, options);
        if (element) {
            new up.Change.DestroyFragment({ ...options, element }).execute();
        }
        return up.migrate.formerlyAsync?.('up.destroy()');
    }
    function parseTargetAndOptions(args) {
        const options = u.parseArgIntoOptions(args, 'target');
        if (u.isElement(options.target)) {
            options.origin ||= options.target;
        }
        return options;
    }
    function markFragmentAsDestroying(element) {
        element.classList.add('up-destroying');
        element.setAttribute('inert', '');
    }
    function reload(...args) {
        const options = { ...config.reloadOptions, ...parseTargetAndOptions(args) };
        options.target ||= ':main';
        const element = getSmart(options.target, options);
        options.url ||= sourceOf(element);
        options.headers = u.merge(options.headers, conditionalHeaders(element));
        if (options.keepData || e.booleanAttr(element, 'up-keep-data')) {
            options.data = up.data(element);
        }
        up.migrate.postprocessReloadOptions?.(options);
        return render(options);
    }
    function conditionalHeaders(element) {
        let headers = {};
        let time = timeOf(element);
        if (time) {
            headers['If-Modified-Since'] = time.toUTCString();
        }
        let etag = etagOf(element);
        if (etag) {
            headers['If-None-Match'] = etag;
        }
        return headers;
    }
    function visit(url, options) {
        return navigate({ ...options, url });
    }
    const KEY_PATTERN = /^(onFail|on|fail)?(.+)$/;
    function successKey(key) {
        let match = KEY_PATTERN.exec(key);
        if (match) {
            let [_, prefix, suffix] = match;
            switch (prefix) {
                case 'onFail':
                    return 'on' + u.upperCaseFirst(suffix);
                case 'fail':
                    return u.lowerCaseFirst(suffix);
            }
        }
    }
    function failKey(key) {
        let match = KEY_PATTERN.exec(key);
        if (match) {
            let [_, prefix, suffix] = match;
            switch (prefix) {
                case 'on':
                    return 'onFail' + u.upperCaseFirst(suffix);
                case undefined:
                    return 'fail' + u.upperCaseFirst(suffix);
            }
        }
    }
    function toTarget(element, options) {
        return u.presence(element, u.isString) || tryToTarget(element, options) || cannotTarget(element);
    }
    function isTargetable(element, options) {
        return !!tryToTarget(element, options);
    }
    function untargetableMessage(element) {
        return `Cannot derive good target selector from a <${e.tagName(element)}> element without identifying attributes. Try setting an [id] or configure up.fragment.config.targetDerivers.`;
    }
    function cannotTarget(element) {
        throw new up.CannotTarget(untargetableMessage(element));
    }
    function tryToTarget(element, options = {}) {
        let derivers = options.strong ? config.strongTargetDerivers : config.targetDerivers;
        return u.findResult(derivers, function (deriver) {
            let target = deriveTarget(element, deriver);
            if (target && isGoodTarget(target, element, options)) {
                return target;
            }
        });
    }
    function deriveTarget(element, deriver) {
        if (u.isFunction(deriver)) {
            return deriver(element);
        }
        else if (element.matches(deriver)) {
            try {
                return deriveTargetFromPattern(element, deriver);
            }
            catch (e) {
                if (e instanceof up.CannotParse) {
                    return deriver;
                }
                else {
                    throw e;
                }
            }
        }
    }
    function deriveTargetFromPattern(element, deriver) {
        let { includePath, excludeRaw } = e.parseSelector(deriver);
        if (includePath.length !== 1) {
            throw new up.CannotParse(deriver);
        }
        let { tagName, id, classNames, attributes } = includePath[0];
        let result = '';
        if (tagName === '*') {
            result += e.tagName(element);
        }
        else if (tagName) {
            result += tagName;
        }
        for (let className of classNames) {
            result += e.classSelector(className);
        }
        if (id) {
            result += e.idSelector(id);
        }
        for (let attributeName in attributes) {
            let attributeValue = attributes[attributeName] || element.getAttribute(attributeName);
            if (attributeName === 'id') {
                result += e.idSelector(attributeValue);
            }
            else if (attributeName === 'class') {
                for (let goodClass of goodClassesForTarget(element)) {
                    result += e.classSelector(goodClass);
                }
            }
            else {
                result += e.attrSelector(attributeName, attributeValue);
            }
        }
        if (excludeRaw) {
            result += excludeRaw;
        }
        return result;
    }
    function isGoodTarget(target, element, options = {}) {
        let verify = options.verify ?? config.verifyDerivedTarget;
        return !isAlive(element) || !verify || up.fragment.get(target, { layer: element, ...options }) === element;
    }
    function matchesPattern(pattern, str) {
        if (u.isRegExp(pattern)) {
            return pattern.test(str);
        }
        else {
            return pattern === str;
        }
    }
    function goodClassesForTarget(element) {
        let isGood = (klass) => !u.some(config.badTargetClasses, (badTargetClass) => matchesPattern(badTargetClass, klass));
        return u.filter(element.classList, isGood);
    }
    const MAIN_PSEUDO = /:main\b/;
    const LAYER_PSEUDO = /:layer\b/;
    const ORIGIN_PSEUDO = /:origin\b/;
    function containsMainPseudo(target) {
        return MAIN_PSEUDO.test(target);
    }
    function expandTargets(targets, options = {}) {
        const { layer } = options;
        if (layer !== 'new' && !(layer instanceof up.Layer)) {
            up.fail('Must pass an up.Layer as { layer } option, but got %o', layer);
        }
        targets = u.copy(u.wrapList(targets));
        const expanded = [];
        while (targets.length) {
            let target = targets.shift();
            if (target === true)
                target = ':main';
            if (containsMainPseudo(target)) {
                let mode = resolveMode(options);
                let replaced = up.layer.mainTargets(mode).map((mainTarget) => target.replace(MAIN_PSEUDO, mainTarget));
                targets.unshift(...replaced);
            }
            else if (LAYER_PSEUDO.test(target)) {
                if (layer === 'new' || layer.state === 'opening')
                    continue;
                let firstSwappableTarget = toTarget(layer.getFirstSwappableElement(), options);
                targets.unshift(target.replace(LAYER_PSEUDO, firstSwappableTarget));
            }
            else if (u.isElementLike(target)) {
                expanded.push(toTarget(target, options));
            }
            else if (u.isString(target)) {
                expanded.push(resolveOrigin(target, options));
            }
        }
        return u.uniq(expanded);
    }
    function resolveMode({ layer, mode }) {
        if (layer === 'new') {
            return mode || up.fail('Must pass a { mode } option together with { layer: "new" }');
        }
        else {
            return layer.mode;
        }
    }
    function modernResolveOrigin(target, { origin } = {}) {
        return target.replace(ORIGIN_PSEUDO, function (match) {
            if (origin) {
                return toTarget(origin);
            }
            else {
                up.fail('Missing { origin } element to resolve "%s" reference (found in %s)', match, target);
            }
        });
    }
    function resolveOrigin(target, options) {
        if (!u.isString(target))
            return target;
        return (up.migrate.resolveOrigin || modernResolveOrigin)(target, options);
    }
    function splitTarget(target) {
        return u.getComplexTokens(target);
    }
    function parseTargetSteps(target, options = {}) {
        let defaultPlacement = options.defaultPlacement || 'swap';
        let defaultMaybe = options.defaultMaybe ?? false;
        let steps = [];
        let simpleSelectors = splitTarget(target);
        for (let selector of simpleSelectors) {
            if (selector === ':none')
                continue;
            let placement = defaultPlacement;
            let maybe = defaultMaybe;
            selector = selector.replace(/::?(before|after|content)\b/, (_match, customPlacement) => {
                placement = customPlacement;
                return '';
            });
            selector = selector.replace(/:maybe\b/, () => {
                maybe = true;
                return '';
            });
            const step = {
                ...options,
                selector,
                placement,
                maybe,
                originalRenderOptions: options,
            };
            steps.push(step);
        }
        return steps;
    }
    function hasAutoHistory(newFragments, layer) {
        let vanillaSelector = expandTargets(config.autoHistoryTargets, { layer }).join();
        for (let newFragment of newFragments) {
            if (e.subtree(newFragment, vanillaSelector).length) {
                return true;
            }
        }
        up.puts('up.render()', "Will not auto-update history because fragment doesn't contain a selector from up.fragment.config.autoHistoryTargets");
        return false;
    }
    function matches(element, selector, options = {}) {
        element = e.get(element);
        if (u.isElement(selector)) {
            let target = tryToTarget(selector);
            return target && element.matches(target);
        }
        else {
            return new up.Selector(selector, element, options).matches(element);
        }
    }
    function matchSelectorMap(element, selectorMap, { layer = element } = {}) {
        let hits = [];
        if (selectorMap && element) {
            for (let [selector, value] of Object.entries(selectorMap)) {
                if (u.isDefined(value) && matches(element, selector, { layer })) {
                    hits.push(value);
                }
            }
        }
        return hits;
    }
    function shouldRevalidate(request, response, options = {}) {
        return request.fromCache && u.evalAutoOption(options.revalidate, config.autoRevalidate, response);
    }
    function isContainedByRivalStep(steps, candidateStep) {
        return u.some(steps, function (rivalStep) {
            return (rivalStep !== candidateStep) &&
                ((rivalStep.placement === 'swap') || (rivalStep.placement === 'content')) &&
                rivalStep.oldElement.contains(candidateStep.oldElement);
        });
    }
    function compressNestedSteps(steps) {
        if (steps.length < 2)
            return steps;
        let compressed = u.uniqBy(steps, 'oldElement');
        compressed = u.reject(compressed, (step) => isContainedByRivalStep(compressed, step));
        return compressed;
    }
    function abort(...args) {
        let options = parseTargetAndOptions(args);
        let testFn;
        let { reason, newLayer, jid } = options;
        let elements;
        if (options.target) {
            elements = getAll(options.target, options);
            testFn = (request) => request.isBoundToSubtrees(elements);
            reason ||= 'Aborting requests within fragment';
        }
        else {
            let layers = up.layer.getAll(options);
            elements = u.map(layers, 'element');
            testFn = (request) => request.isBoundToLayers(layers);
            reason ||= 'Aborting requests within ' + layers.join(', ');
        }
        let testFnWithAbortable = (request) => request.abortable && testFn(request);
        up.network.abort(testFnWithAbortable, { ...options, reason });
        for (let element of elements) {
            up.emit(element, 'up:fragment:aborted', { reason, newLayer, jid, log: reason });
        }
    }
    function onAborted(fragment, callback) {
        return up.event.onClosest(fragment, 'up:fragment:aborted', callback);
    }
    function onKept(fragment, callback) {
        return up.event.onClosest(fragment, 'up:fragment:kept', callback);
    }
    function onFirstIntersect(element, callback, { margin = 0 } = {}) {
        if (e.isIntersectingWindow(element, { margin })) {
            callback();
            return;
        }
        function processIntersectEntries(entries) {
            for (let entry of entries) {
                if (entry.isIntersecting) {
                    disconnect();
                    callback();
                    return;
                }
            }
        }
        let observer = new IntersectionObserver(processIntersectEntries, { rootMargin: `${margin}px` });
        let disconnect = () => observer.disconnect();
        observer.observe(element);
        up.destructor(element, disconnect);
    }
    const STARTS_WITH_SELECTOR = /^([\w-]+|\*)?(#|\.|[:[][a-z-]{3,})/;
    function provideNodes(value, { origin, originLayer, data, htmlParser = e.createNodesFromHTML } = {}) {
        if (u.isString(value) && STARTS_WITH_SELECTOR.test(value)) {
            let [parsedValue, parsedData] = u.parseScalarJSONPairs(value)[0];
            data = { ...data, ...parsedData };
            value = up.fragment.get(parsedValue, { layer: 'closest', origin, originLayer }) || up.fail(`Cannot find template "%s"`, value);
        }
        if (u.isString(value)) {
            value = htmlParser(value);
        }
        if (isTemplate(value)) {
            value = cloneTemplate(value, data, { htmlParser });
        }
        return u.wrapList(value);
    }
    function isTemplate(value) {
        return u.isElement(value) && value.matches('template, script[type]') && !up.script.isScript(value);
    }
    function cloneTemplate(templateOrSelector, data = {}, { origin, htmlParser } = {}) {
        let template = getSmart(templateOrSelector, { origin }) || up.fail('Template not found: %o', templateOrSelector);
        let event = up.emit(template, 'up:template:clone', { data, nodes: null, log: ["Using template %o", templateOrSelector] });
        let nodes = event.nodes ?? defaultTemplateNodes(template, htmlParser);
        for (let node of nodes) {
            node.upTemplateData = data;
        }
        return nodes;
    }
    function defaultTemplateNodes(template, htmlParser = e.createNodesFromHTML) {
        let templateText = template.innerHTML;
        return htmlParser(templateText);
    }
    function insertTemp(...args) {
        let [reference, position = 'beforeend', tempValue] = u.args(args, 'val', u.isAdjacentPosition, 'val');
        let tempNodes = provideNodes(tempValue, { origin: reference });
        let tempElement = e.wrapIfRequired(tempNodes);
        let oldPosition = document.contains(tempElement) && e.documentPosition(tempElement);
        reference.insertAdjacentElement(position, tempElement);
        if (oldPosition) {
            return () => {
                oldPosition[0].insertAdjacentElement(oldPosition[1], tempElement);
            };
        }
        else {
            up.hello(tempElement);
            return () => up.destroy(tempElement);
        }
    }
    function trackSelector(...args) {
        let parsedArgs = u.args(args, 'val', 'options', 'callback');
        let tracker = new up.SelectorTracker(...parsedArgs);
        return tracker.start();
    }
    let mutateLevel = 0;
    let afterMutateCleaner = u.cleaner('fifo');
    function mutate(callback) {
        try {
            mutateLevel++;
            return callback();
        }
        finally {
            if (--mutateLevel === 0)
                afterMutateCleaner.clean();
        }
    }
    function afterMutate(callback) {
        if (mutateLevel === 0) {
            callback();
        }
        else {
            afterMutateCleaner(callback);
        }
    }
    up.on('up:framework:boot', function () {
        const { documentElement } = document;
        up.hello(documentElement);
        documentElement.setAttribute('up-source', normalizeSource(location.href));
        if (!up.browser.canPushState()) {
            return up.warn('Cannot push history changes. Next render pass with history will load a full page.');
        }
    });
    return {
        config,
        reload,
        destroy,
        render,
        navigate,
        get: getSmart,
        getFirstDescendant,
        all: getAll,
        subtree: getSubtree,
        contains,
        closest,
        source: sourceOf,
        normalizeSource,
        visit,
        markAsDestroying: markFragmentAsDestroying,
        emitInserted: emitFragmentInserted,
        emitDestroyed: emitFragmentDestroyed,
        emitKeep: emitFragmentKeep,
        emitKept: emitFragmentKept,
        keepPlan: findKeepPlan,
        defaultNormalizeKeepHTML,
        successKey,
        failKey,
        expandTargets,
        resolveOrigin,
        toTarget,
        tryToTarget,
        isTargetable,
        matches,
        matchSelectorMap,
        hasAutoHistory,
        time: timeOf,
        etag: etagOf,
        shouldRevalidate,
        abort,
        onAborted,
        onKept,
        onFirstIntersect,
        splitTarget,
        parseTargetSteps,
        isAlive,
        isNotDestroying,
        compressNestedSteps,
        containsMainPseudo,
        insertTemp,
        provideNodes,
        cloneTemplate,
        trackSelector,
        mutate,
        afterMutate,
    };
})();
up.reload = up.fragment.reload;
up.destroy = up.fragment.destroy;
up.render = up.fragment.render;
up.navigate = up.fragment.navigate;
up.visit = up.fragment.visit;
up.template = { clone: up.fragment.cloneTemplate };
u.delegate(up, ['context'], () => up.layer.current);


/***/ }),
/* 92 */
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
// extracted by mini-css-extract-plugin


/***/ }),
/* 93 */
/***/ ((__unused_webpack_module, __unused_webpack_exports, __webpack_require__) => {

__webpack_require__(94);
up.viewport = (function () {
    const u = up.util;
    const e = up.element;
    const f = up.fragment;
    const config = new up.Config(() => ({
        viewportSelectors: ['[up-viewport]', '[up-fixed]'],
        fixedTopSelectors: ['[up-fixed~=top]'],
        fixedBottomSelectors: ['[up-fixed~=bottom]'],
        anchoredRightSelectors: ['[up-anchored~=right]', '[up-fixed~=top]', '[up-fixed~=bottom]', '[up-fixed~=right]'],
        revealSnap: 200,
        revealPadding: 0,
        revealTop: false,
        revealMax() { return 0.5 * window.innerHeight; },
        autoFocusVisible({ element, inputDevice }) { return inputDevice === 'key' || up.form.isField(element); }
    }));
    const bodyShifter = new up.BodyShifter();
    up.compiler(config.selectorFn('anchoredRightSelectors'), function (element) {
        return bodyShifter.onAnchoredElementInserted(element);
    });
    const reveal = up.mockable(function (element, options) {
        options = u.options(options);
        element = f.get(element, options);
        if (!(options.layer = up.layer.get(element))) {
            up.fail('Cannot reveal a detached element');
        }
        if (options.peel) {
            options.layer.peel();
        }
        const motion = new up.RevealMotion(element, options);
        motion.start();
        if (options.focus) {
            tryFocus(element, { force: true, preventScroll: true });
        }
        return up.migrate.formerlyAsync?.('up.reveal()') || true;
    });
    function doFocus(element, { preventScroll, force, inputDevice, focusVisible } = {}) {
        if (force) {
            if (!element.hasAttribute('tabindex') && element.tabIndex === -1) {
                element.setAttribute('tabindex', '-1');
            }
        }
        inputDevice ??= up.event.inputDevice;
        focusVisible ??= 'auto';
        focusVisible = u.evalAutoOption(focusVisible, config.autoFocusVisible, { element, inputDevice });
        element.focus({
            preventScroll: true,
            focusVisible,
        });
        removeFocusClasses(element);
        element.classList.add(focusVisible ? 'up-focus-visible' : 'up-focus-hidden');
        if (!preventScroll) {
            return reveal(element);
        }
    }
    function removeFocusClasses(element) {
        element?.classList.remove('up-focus-hidden', 'up-focus-visible');
    }
    up.on('focusin', function ({ relatedTarget }) {
        removeFocusClasses(relatedTarget);
    });
    function tryFocus(element, options) {
        doFocus(element, options);
        return element === document.activeElement;
    }
    function revealHash(...args) {
        return revealHashFn(...args)?.();
    }
    function revealHashFn(hash, { strong, layer, origin, behavior = 'instant', focus = false } = {}) {
        if (!hash)
            return;
        let match = firstHashTarget(hash, { layer, origin });
        if (match) {
            return () => {
                let doReveal = () => reveal(match, { top: true, behavior, focus });
                if (strong)
                    u.fastTask(doReveal);
                return doReveal();
            };
        }
        else if (hash === '#top') {
            return () => {
                return scrollTo(0, { behavior });
            };
        }
    }
    function allSelector() {
        return [rootSelector(), ...config.viewportSelectors].join();
    }
    function closest(target, options = {}) {
        const element = f.get(target, options);
        return element.closest(allSelector());
    }
    function getSubtree(element, options = {}) {
        element = f.get(element, options);
        return e.subtree(element, allSelector());
    }
    function getAround(element, options = {}) {
        element = f.get(element, options);
        return e.around(element, allSelector());
    }
    function getAll(options = {}) {
        return f.all(allSelector(), options);
    }
    function rootSelector() {
        return getRoot().tagName;
    }
    function getRoot() {
        return document.scrollingElement;
    }
    function rootWidth() {
        return e.root.clientWidth;
    }
    function rootHeight() {
        return e.root.clientHeight;
    }
    function isRoot(element) {
        return element === getRoot();
    }
    function rootScrollbarWidth() {
        return window.innerWidth - rootWidth();
    }
    function scrollTopKey(viewport) {
        return up.fragment.tryToTarget(viewport);
    }
    function fixedElements(root = document) {
        const queryParts = ['[up-fixed]'].concat(config.fixedTopSelectors).concat(config.fixedBottomSelectors);
        return root.querySelectorAll(queryParts.join());
    }
    function saveScroll(...args) {
        const [viewports, options] = parseOptions(args);
        const location = options.location || options.layer.location;
        if (location) {
            const tops = getScrollTopsForViewportElements(viewports);
            options.layer.lastScrollTops.set(location, tops);
        }
    }
    function getScrollTopsForViewportElements(viewports) {
        let tops = {};
        for (let viewport of viewports) {
            let key = scrollTopKey(viewport);
            if (key) {
                tops[key] = viewport.scrollTop;
            }
            else {
                up.warn('up.viewport.saveScroll()', 'Cannot save scroll positions for untargetable viewport %o', viewport);
            }
        }
        return tops;
    }
    function getScrollTops(...args) {
        let viewports = getAll(...args);
        return getScrollTopsForViewportElements(viewports);
    }
    function restoreScroll(...args) {
        const [viewports, options] = parseOptions(args);
        const scrollTops = options.scrollTops ?? options.layer.lastScrollTops.get(options.layer.location);
        if (scrollTops) {
            setScrollPositions(viewports, scrollTops, 0);
            up.puts('up.viewport.restoreScroll()', 'Restored scroll positions to %o', scrollTops);
            return true;
        }
        else {
            return false;
        }
    }
    function saveFocus(options = {}) {
        const layer = up.layer.get(options);
        const location = options.location || layer.location;
        if (location) {
            const focusCapsule = up.FocusCapsule.preserve(layer);
            layer.lastFocusCapsules.set(location, focusCapsule);
        }
    }
    function restoreFocus(options = {}) {
        const layer = up.layer.get(options);
        const location = options.location || layer.location;
        const locationCapsule = options.layer.lastFocusCapsules.get(location);
        if (locationCapsule && locationCapsule.restore(layer)) {
            up.puts('up.viewport.restoreFocus()', 'Restored focus to "%s"', locationCapsule.target);
            return true;
        }
        else {
            return false;
        }
    }
    function newStateCache() {
        return new up.FIFOCache({ capacity: 30, normalizeKey: u.matchableURL });
    }
    function parseOptions(args) {
        const [reference, options] = u.args(args, 'val', 'options');
        options.layer = up.layer.get(options);
        let viewports;
        if (reference) {
            viewports = [closest(reference, options)];
        }
        else if (options.around) {
            viewports = getAround(options.around, options);
        }
        else {
            viewports = getAll(options);
        }
        return [viewports, options];
    }
    function scrollTo(position, ...args) {
        const [viewports, options] = parseOptions(args);
        setScrollPositions(viewports, {}, position, options.behavior);
        return true;
    }
    function setScrollPositions(viewports, tops, defaultTop, behavior = 'instant') {
        for (let viewport of viewports) {
            const key = scrollTopKey(viewport);
            let top = tops[key] || defaultTop;
            if (top < 0 || Object.is(top, -0)) {
                top += viewport.scrollHeight - viewport.clientHeight;
            }
            viewport.scrollTo({ top, behavior });
        }
    }
    function absolutize(element, options = {}) {
        const viewport = closest(element);
        const viewportRect = viewport.getBoundingClientRect();
        const originalRect = element.getBoundingClientRect();
        const boundsRect = new up.Rect({
            left: originalRect.left - viewportRect.left,
            top: originalRect.top - viewportRect.top,
            width: originalRect.width,
            height: originalRect.height
        });
        options.afterMeasure?.();
        e.setStyle(element, {
            position: element.style.position === 'static' ? 'static' : 'relative',
            top: 'auto',
            right: 'auto',
            bottom: 'auto',
            left: 'auto',
            width: '100%',
            height: '100%'
        });
        const bounds = e.createFromSelector('up-bounds');
        e.insertBefore(element, bounds);
        bounds.appendChild(element);
        const moveBounds = function (diffX, diffY) {
            boundsRect.left += diffX;
            boundsRect.top += diffY;
            return e.setStyle(bounds, boundsRect, 'px');
        };
        moveBounds(0, 0);
        const newElementRect = element.getBoundingClientRect();
        moveBounds(originalRect.left - newElementRect.left, originalRect.top - newElementRect.top);
        u.each(fixedElements(element), e.fixedToAbsolute);
        return {
            bounds,
            moveBounds
        };
    }
    function firstHashTarget(hash, options = {}) {
        hash = pureHash(hash);
        if (hash) {
            const selector = [
                e.idSelector(hash),
                'a' + e.attrSelector('name', hash)
            ].join();
            return f.get(selector, options);
        }
    }
    function pureHash(value) {
        return value?.replace(/^#/, '');
    }
    function focusedElementWithin(scopeElement) {
        const focusedElement = document.activeElement;
        if (up.fragment.contains(scopeElement, focusedElement)) {
            return focusedElement;
        }
    }
    const CURSOR_PROPS = ['selectionStart', 'selectionEnd', 'scrollLeft', 'scrollTop'];
    function copyCursorProps(from, to = {}) {
        for (let key of CURSOR_PROPS) {
            try {
                to[key] = from[key];
            }
            catch (_error) {
            }
        }
        return to;
    }
    return {
        reveal,
        revealHash,
        revealHashFn,
        firstHashTarget,
        config,
        get: closest,
        subtree: getSubtree,
        around: getAround,
        getScrollTops,
        get root() { return getRoot(); },
        rootWidth,
        rootHeight,
        isRoot,
        rootScrollbarWidth,
        saveScroll,
        restoreScroll,
        scrollTo,
        saveFocus,
        restoreFocus,
        absolutize,
        focus: doFocus,
        tryFocus,
        newStateCache,
        focusedElementWithin,
        copyCursorProps,
        bodyShifter,
    };
})();
up.focus = up.viewport.focus;
up.reveal = up.viewport.reveal;


/***/ }),
/* 94 */
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
// extracted by mini-css-extract-plugin


/***/ }),
/* 95 */
/***/ (() => {

up.motion = (function () {
    const u = up.util;
    const e = up.element;
    const motionController = new up.MotionController('motion');
    const config = new up.Config(() => ({
        duration: 175,
        easing: 'ease',
        enabled: !matchMedia('(prefers-reduced-motion: reduce)').matches
    }));
    let namedAnimations = new up.Registry('animation', findAnimationFn);
    let namedTransitions = new up.Registry('transition', findTransitionFn);
    function reset() {
        motionController.reset();
    }
    async function animate(element, animationValue, { duration, easing, onFinished } = {}) {
        element = up.fragment.get(element);
        const animationFn = up.error.guardFn(findAnimationFn(animationValue));
        const timingOptions = effectiveTimingOptions({ duration, easing });
        let trackable = async function () {
            if (animationFn && canAnimateElement(element)) {
                try {
                    await animationFn(element, timingOptions);
                }
                finally {
                    onFinished?.();
                }
            }
            else {
                onFinished?.();
            }
        };
        await motionController.startFunction([element], trackable);
    }
    function canAnimateElement(element) {
        return !e.isSingleton(element);
    }
    function effectiveTimingOptions({ duration, easing }) {
        return {
            duration: config.enabled ? (duration ?? config.duration) : 0,
            easing: easing ?? config.easing,
        };
    }
    async function animateNow(element, lastFrame, { duration, easing, finishedFrame }) {
        let camelizedLastFrame = u.withRenamedKeys(lastFrame, u.kebabToCamelCase);
        let animation = element.animate([camelizedLastFrame], { duration, easing, fill: 'forwards' });
        let offFinish;
        let conclude = () => {
            animation.finish();
            e.setStyle(element, finishedFrame ?? lastFrame);
            animation.cancel();
            offFinish();
        };
        offFinish = up.on(element, 'up:motion:finish', conclude);
        await animation.finished;
        conclude();
    }
    function finish(element) {
        element = up.fragment.get(element);
        motionController.finish(element);
        return up.migrate.formerlyAsync?.('up.motion.finish()');
    }
    async function morph(oldElement, newElement, transitionValue, { duration, easing, afterInsert, beforeRemove, afterRemove } = {}) {
        oldElement = up.fragment.get(oldElement);
        newElement = up.fragment.get(newElement);
        const transitionFn = up.error.guardFn(findTransitionFn(transitionValue));
        const timingOptions = effectiveTimingOptions({ duration, easing });
        const trackable = async function ({ nested }) {
            if (transitionFn && canAnimateElement(oldElement)) {
                if (nested) {
                    await transitionFn(oldElement, newElement, timingOptions);
                }
                else {
                    const viewport = up.viewport.get(oldElement);
                    const scrollTopBeforeScroll = viewport.scrollTop;
                    const oldRemote = up.viewport.absolutize(oldElement, {
                        afterMeasure: () => e.insertBefore(oldElement, newElement)
                    });
                    afterInsert?.();
                    const scrollTopAfterScroll = viewport.scrollTop;
                    oldRemote.moveBounds(0, scrollTopAfterScroll - scrollTopBeforeScroll);
                    await transitionFn(oldElement, newElement, timingOptions);
                    beforeRemove?.();
                    oldRemote.bounds.remove();
                    afterRemove?.();
                }
            }
            else {
                beforeRemove?.();
                swapElementsDirectly(oldElement, newElement);
                afterInsert?.();
                afterRemove?.();
            }
        };
        await motionController.startFunction([newElement, oldElement], trackable);
    }
    function findTransitionFn(value) {
        if (isNone(value)) {
            return undefined;
        }
        else if (u.isFunction(value)) {
            return value;
        }
        else if (u.isArray(value)) {
            return composeTransitionFn(...value);
        }
        else if (u.isString(value) && value.includes('/')) {
            return composeTransitionFn(...value.split('/'));
        }
        else {
            return namedTransitions.get(value);
        }
    }
    function composeTransitionFn(oldAnimation, newAnimation) {
        if (!isNone(oldAnimation) && !isNone(newAnimation)) {
            const oldAnimationFn = findAnimationFn(oldAnimation) || u.asyncNoop;
            const newAnimationFn = findAnimationFn(newAnimation) || u.asyncNoop;
            return (oldElement, newElement, options) => Promise.all([
                oldAnimationFn(oldElement, options),
                newAnimationFn(newElement, options)
            ]);
        }
    }
    function findAnimationFn(value) {
        if (isNone(value)) {
            return undefined;
        }
        else if (u.isFunction(value)) {
            return value;
        }
        else if (u.isOptions(value)) {
            return (element, options) => animateNow(element, value, options);
        }
        else {
            return namedAnimations.get(value);
        }
    }
    const swapElementsDirectly = up.mockable(function (oldElement, newElement) {
        oldElement.replaceWith(newElement);
    });
    function motionOptions(element, options, parserOptions) {
        options = u.options(options);
        let parser = new up.OptionsParser(element, options, parserOptions);
        parser.booleanOrString('animation');
        parser.booleanOrString('transition');
        parser.string('easing');
        parser.number('duration');
        return options;
    }
    up.on('up:framework:boot', function () {
        if (!config.enabled) {
            up.puts('up.motion', 'Animations are disabled');
        }
    });
    function isNone(motionValue) {
        return !motionValue || motionValue === 'none';
    }
    function registerOpacityAnimation(name, from, to) {
        namedAnimations.put(name, function (element, options) {
            element.style.opacity = u.evalOption(from, element);
            return animateNow(element, { opacity: to }, options);
        });
    }
    function currentOpacity(element) {
        return e.style(element, 'opacity');
    }
    registerOpacityAnimation('fade-in', 0, 1);
    registerOpacityAnimation('fade-out', currentOpacity, 0);
    function translateCSS(dx, dy) {
        return { transform: `translate(${dx}px, ${dy}px)` };
    }
    function zeroTranslateCSS() {
        return { transform: 'translate(0, 0)' };
    }
    function untranslatedBox(element) {
        e.setStyle(element, zeroTranslateCSS());
        return element.getBoundingClientRect();
    }
    function registerMoveAnimations(direction, boxToTransform) {
        const animationToName = `move-to-${direction}`;
        const animationFromName = `move-from-${direction}`;
        namedAnimations.put(animationToName, function (element, options) {
            const box = untranslatedBox(element);
            const transform = boxToTransform(box);
            return animateNow(element, transform, options);
        });
        namedAnimations.put(animationFromName, function (element, options) {
            const box = untranslatedBox(element);
            const transform = boxToTransform(box);
            e.setStyle(element, transform);
            return animateNow(element, zeroTranslateCSS(), { ...options, finishedFrame: { transform: '' } });
        });
    }
    registerMoveAnimations('top', function (box) {
        const travelDistance = box.top + box.height;
        return translateCSS(0, -travelDistance);
    });
    registerMoveAnimations('bottom', function (box) {
        const travelDistance = up.viewport.rootHeight() - box.top;
        return translateCSS(0, travelDistance);
    });
    registerMoveAnimations('left', function (box) {
        const travelDistance = box.left + box.width;
        return translateCSS(-travelDistance, 0);
    });
    registerMoveAnimations('right', function (box) {
        const travelDistance = up.viewport.rootWidth() - box.left;
        return translateCSS(travelDistance, 0);
    });
    namedTransitions.put('cross-fade', ['fade-out', 'fade-in']);
    namedTransitions.put('move-left', ['move-to-left', 'move-from-right']);
    namedTransitions.put('move-right', ['move-to-right', 'move-from-left']);
    namedTransitions.put('move-up', ['move-to-top', 'move-from-bottom']);
    namedTransitions.put('move-down', ['move-to-bottom', 'move-from-top']);
    up.on('up:framework:reset', reset);
    return {
        morph,
        animate,
        finish,
        transition: namedTransitions.put,
        animation: namedAnimations.put,
        config,
        isNone,
        swapElementsDirectly,
        motionOptions,
    };
})();
up.transition = up.motion.transition;
up.animation = up.motion.animation;
up.morph = up.motion.morph;
up.animate = up.motion.animate;


/***/ }),
/* 96 */
/***/ ((__unused_webpack_module, __unused_webpack_exports, __webpack_require__) => {

__webpack_require__(97);
const u = up.util;
up.network = (function () {
    const config = new up.Config(() => ({
        concurrency: 6,
        wrapMethod: true,
        cacheSize: 70,
        cacheExpireAge: 15 * 1000,
        cacheEvictAge: 90 * 60 * 1000,
        lateDelay: 400,
        fail(response) { return (response.status < 200 || response.status > 299) && response.status !== 304; },
        autoCache(request) { return request.isSafe(); },
        expireCache(request) { return !request.isSafe(); },
        evictCache: false,
        progressBar: true,
        timeout: 90_000,
    }));
    const queue = new up.Request.Queue();
    const cache = new up.Request.Cache();
    let progressBar = null;
    function reset() {
        abortRequests();
        queue.reset();
        cache.reset();
        progressBar?.destroy();
        progressBar = null;
    }
    function makeRequest(...args) {
        const options = parseRequestOptions(args);
        const request = new up.Request(options);
        processRequest(request);
        return request;
    }
    function parseRequestOptions(args) {
        let options = u.parseArgIntoOptions(args, 'url');
        up.migrate.handleRequestOptions?.(options);
        return options;
    }
    function processRequest(request) {
        cache.expire(request.expireCache ?? u.evalOption(config.expireCache, request) ?? false);
        cache.evict(request.evictCache ?? u.evalOption(config.evictCache, request) ?? false);
        useCachedRequest(request) || queueRequest(request);
    }
    function useCachedRequest(newRequest) {
        let cachedRequest;
        if (newRequest.willCache() && (cachedRequest = cache.get(newRequest))) {
            up.puts('up.request()', 'Re-using previous request to %s', newRequest.description);
            if (!newRequest.background) {
                queue.promoteToForeground(cachedRequest);
            }
            cachedRequest.mergeIfUnsent(newRequest);
            cache.track(cachedRequest, newRequest, { onIncompatible: processRequest });
            return true;
        }
    }
    function queueRequest(request) {
        handleCaching(request);
        queue.asap(request);
        return true;
    }
    function handleCaching(request) {
        if (request.willCache()) {
            cache.put(request);
            request.onLoading = () => cache.reindex(request);
        }
        u.always(request, function (responseOrError) {
            cache.expire(responseOrError.expireCache ?? false, { except: request });
            cache.evict(responseOrError.evictCache ?? false, { except: request });
            let isResponse = responseOrError instanceof up.Response;
            let isNetworkError = !isResponse;
            let isSuccessResponse = isResponse && responseOrError.ok;
            let isErrorResponse = isResponse && !responseOrError.ok;
            let isEmptyResponse = isResponse && responseOrError.none;
            let redirectRequest = isResponse && responseOrError.redirectRequest;
            if (isErrorResponse) {
                cache.evict(request.url);
            }
            else if (isNetworkError || isEmptyResponse) {
                cache.evict(request);
            }
            else if (isSuccessResponse) {
                if (cache.get(request)) {
                    cache.put(request);
                }
                if (redirectRequest && (redirectRequest.willCache() || cache.get(redirectRequest))) {
                    cache.put(redirectRequest);
                }
            }
        });
    }
    function isBusy() {
        return queue.isBusy();
    }
    function loadPage(requestsAttrs) {
        new up.Request(requestsAttrs).loadPage();
    }
    function abortRequests(...args) {
        up.migrate.preprocessAbortArgs?.(args);
        queue.abort(...args);
    }
    function isSafeMethod(method) {
        return u.contains(['GET', 'OPTIONS', 'HEAD'], u.normalizeMethod(method));
    }
    function onLate() {
        if (u.evalOption(config.progressBar)) {
            progressBar = new up.ProgressBar();
        }
    }
    function onRecover() {
        progressBar?.conclude();
    }
    up.on('up:network:late', onLate);
    up.on('up:network:recover', onRecover);
    up.on('up:framework:reset', reset);
    return {
        request: makeRequest,
        cache,
        isBusy,
        isSafeMethod,
        config,
        abort: abortRequests,
        queue,
        loadPage,
    };
})();
up.request = up.network.request;
up.cache = up.network.cache;


/***/ }),
/* 97 */
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
// extracted by mini-css-extract-plugin


/***/ }),
/* 98 */
/***/ ((__unused_webpack_module, __unused_webpack_exports, __webpack_require__) => {

__webpack_require__(99);
const u = up.util;
up.layer = (function () {
    const LAYER_CLASSES = [
        up.Layer.Root,
        up.Layer.Modal,
        up.Layer.Popup,
        up.Layer.Drawer,
        up.Layer.Cover
    ];
    const config = new up.Config(function () {
        const newConfig = {
            mode: 'modal',
            any: {
                mainTargets: [
                    "[up-main='']",
                    'main',
                    ':layer'
                ]
            },
            root: {
                mainTargets: ['[up-main~=root]'],
                history: true
            },
            overlay: {
                mainTargets: ['[up-main~=overlay]'],
                openAnimation: 'fade-in',
                closeAnimation: 'fade-out',
                dismissLabel: '×',
                dismissARIALabel: 'Dismiss dialog',
                dismissible: true,
                history: 'auto',
                trapFocus: true,
            },
            cover: {
                mainTargets: ['[up-main~=cover]']
            },
            drawer: {
                mainTargets: ['[up-main~=drawer]'],
                backdrop: true,
                position: 'left',
                size: 'medium',
                openAnimation(layer) {
                    switch (layer.position) {
                        case 'left': return 'move-from-left';
                        case 'right': return 'move-from-right';
                    }
                },
                closeAnimation(layer) {
                    switch (layer.position) {
                        case 'left': return 'move-to-left';
                        case 'right': return 'move-to-right';
                    }
                }
            },
            modal: {
                mainTargets: ['[up-main~=modal]'],
                backdrop: true,
                size: 'medium'
            },
            popup: {
                mainTargets: ['[up-main~=popup]'],
                position: 'bottom',
                size: 'medium',
                align: 'left',
                dismissible: 'outside key',
                trapFocus: false,
            },
            foreignOverlaySelectors: ['dialog']
        };
        for (let Class of LAYER_CLASSES) {
            newConfig[Class.mode].Class = Class;
        }
        return newConfig;
    });
    let stack = null;
    let handlers = [];
    function mainTargets(mode) {
        return u.flatMap(modeConfigs(mode), 'mainTargets');
    }
    function modeConfigs(mode) {
        if (mode === 'root') {
            return [config.root, config.any];
        }
        else {
            return [config[mode], config.overlay, config.any];
        }
    }
    function normalizeLayerOption(options) {
        if (options.layer instanceof up.Layer)
            return;
        up.migrate.handleLayerOptions?.(options);
        if (u.isGiven(options.layer)) {
            let match = String(options.layer).match(/^(new|shatter|swap)( (\w+))?/);
            if (match) {
                options.layer = 'new';
                const openMethod = match[1];
                const shorthandMode = match[3];
                options.mode ||= shorthandMode || config.mode;
                if (openMethod === 'swap') {
                    if (up.layer.isOverlay()) {
                        options.baseLayer = 'parent';
                    }
                }
                else if (openMethod === 'shatter') {
                    options.baseLayer = 'root';
                }
            }
        }
        else if (u.isElementLike(options.target)) {
            options.layer = stack.get(options.target, { normalizeLayerOptions: false });
        }
        else if (options.origin) {
            options.layer = 'origin';
        }
        else {
            options.layer = 'current';
        }
    }
    function setBaseLayerOption(options) {
        if (options.baseLayer instanceof up.Layer)
            return;
        options.baseLayer = stack.get('current', { ...options, normalizeLayerOptions: false });
    }
    function normalizeOptions(options) {
        normalizeLayerOption(options);
        options.context ??= {};
        setBaseLayerOption(options);
    }
    function build(options, beforeNew) {
        const { mode } = options;
        const { Class } = config[mode];
        const configs = modeConfigs(mode).toReversed();
        let handleDeprecatedConfig = up.migrate.handleLayerConfig;
        if (handleDeprecatedConfig) {
            configs.forEach(handleDeprecatedConfig);
        }
        options.openAnimation ??= u.pluckKey(options, 'animation');
        options = u.mergeDefined(...configs, { mode, stack }, options);
        if (beforeNew) {
            options = beforeNew(options);
        }
        return new Class(options);
    }
    function reset() {
        stack.reset();
        handlers = u.filter(handlers, 'isDefault');
    }
    async function open(options) {
        options = u.options(options, {
            layer: 'new',
            defaultToEmptyContent: true,
            navigate: true
        });
        let result = await up.render(options);
        return result.layer;
    }
    function ask(options) {
        return new Promise(function (resolve, reject) {
            options = {
                ...options,
                onAccepted: (event) => resolve(event.value),
                onDismissed: (event) => reject(event.value)
            };
            open(options);
        });
    }
    function anySelector() {
        return u.map(LAYER_CLASSES, (Class) => Class.selector()).join();
    }
    function optionToString(option) {
        if (u.isString(option)) {
            return `layer "${option}"`;
        }
        else {
            return option.toString();
        }
    }
    function isWithinForeignOverlay(element) {
        let selector = config.selector('foreignOverlaySelectors');
        return !!(selector && element.closest(selector));
    }
    up.on('up:fragment:destroyed', function () {
        stack.sync();
    });
    up.on('up:framework:evaled', function () {
        stack = new up.LayerStack();
    });
    up.on('up:framework:reset', reset);
    const api = {
        config,
        mainTargets,
        open,
        build,
        ask,
        normalizeOptions,
        anySelector,
        optionToString,
        get stack() { return stack.layers; },
        isWithinForeignOverlay
    };
    u.delegate(api, [
        'get',
        'getAll',
        'root',
        'overlays',
        'current',
        'front',
        'sync',
        'count',
        'dismissOverlays'
    ], () => stack);
    u.delegate(api, [
        'accept',
        'dismiss',
        'isRoot',
        'isOverlay',
        'isFront',
        'on',
        'off',
        'emit',
        'parent',
        'history',
        'location',
        'mode',
        'context',
        'element',
        'contains',
        'size',
        'affix'
    ], () => stack.current);
    return api;
})();


/***/ }),
/* 99 */
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
// extracted by mini-css-extract-plugin


/***/ }),
/* 100 */
/***/ ((__unused_webpack_module, __unused_webpack_exports, __webpack_require__) => {

__webpack_require__(101);
up.link = (function () {
    const u = up.util;
    const e = up.element;
    let lastTouchstartTarget = null;
    let lastMousedownTarget = null;
    let lastInstantTarget = null;
    const ATTRS_WITH_LOCAL_HTML = '[up-content], [up-fragment], [up-document]';
    const ATTRS_SUGGESTING_FOLLOW = `${ATTRS_WITH_LOCAL_HTML}, [up-target], [up-layer], [up-transition], [up-preload]`;
    const DEFAULT_INTERACTIVE_ELEMENT = 'a[href], button';
    const config = new up.Config(() => ({
        followSelectors: ['[up-follow]', `a:is(${ATTRS_SUGGESTING_FOLLOW})`],
        noFollowSelectors: ['[up-follow=false]', 'a[download]', 'a[target]', 'a[href^="javascript:"]', 'a[href^="mailto:"]', 'a[href^="tel:"]', `a[href^="#"]:not(${ATTRS_WITH_LOCAL_HTML})`, e.crossOriginSelector('href'), e.crossOriginSelector('up-href')],
        instantSelectors: ['[up-instant]'],
        noInstantSelectors: ['[up-instant=false]', '[onclick]'],
        preloadSelectors: ['[up-preload]'],
        noPreloadSelectors: ['[up-preload=false]'],
        clickableSelectors: ['[up-clickable]', '[up-follow]', '[up-emit]', '[up-accept]', '[up-dismiss]', `a:is(${ATTRS_SUGGESTING_FOLLOW})`],
        noClickableSelectors: ['[up-clickable=false]', DEFAULT_INTERACTIVE_ELEMENT],
        preloadDelay: 90,
    }));
    function isPreloadDisabled(link) {
        return !up.browser.canPushState() || !isFollowable(link) || !willCache(link);
    }
    function willCache(link) {
        const options = parseRequestOptions(link);
        if (options.url) {
            if (options.cache == null) {
                options.cache = 'auto';
            }
            options.basic = true;
            const request = new up.Request(options);
            return request.willCache();
        }
    }
    function reset() {
        lastTouchstartTarget = null;
        lastMousedownTarget = null;
        lastInstantTarget = null;
    }
    const follow = up.mockable(function (link, options, parserOptions) {
        return up.render(followOptions(link, options, parserOptions));
    });
    function parseRequestOptions(link, options, parserOptions) {
        options = u.options(options);
        const parser = new up.OptionsParser(link, options, { ...parserOptions, fail: false });
        options.url = followURL(link, options);
        options.method = followMethod(link, options);
        parser.json('headers');
        parser.json('params');
        parser.booleanOrString('cache');
        parser.booleanOrString('expireCache');
        parser.booleanOrString('evictCache');
        parser.booleanOrString('revalidate');
        parser.booleanOrString('abort');
        parser.boolean('abortable');
        parser.boolean('background');
        parser.string('contentType');
        parser.booleanOrNumber('lateDelay');
        parser.number('timeout');
        parser.booleanOrString('fail');
        return options;
    }
    function followOptions(link, options, parserOptions) {
        link = up.fragment.get(link);
        options = u.options(options);
        const parser = new up.OptionsParser(link, options, { fail: true, ...parserOptions });
        parser.include(parseRequestOptions);
        options.origin ||= link;
        parser.boolean('navigate', { default: true });
        parser.string('confirm', { attr: ['up-confirm', 'data-confirm'] });
        parser.string('target');
        parser.booleanOrString('fallback');
        parser.string('match');
        parser.string('document');
        parser.string('fragment');
        parser.string('content');
        parser.boolean('keep', { attr: 'up-use-keep' });
        parser.boolean('hungry', { attr: 'up-use-hungry' });
        parser.json('data', { attr: 'up-use-data' });
        parser.json('dataMap', { attr: 'up-use-data-map' });
        parser.renderCallback('onLoaded');
        parser.renderCallback('onRendered');
        parser.renderCallback('onFinished');
        parser.renderCallback('onOffline');
        parser.renderCallback('onError');
        parser.booleanOrString('peel');
        parser.string('layer');
        parser.string('baseLayer');
        parser.json('context');
        parser.string('mode');
        parser.string('align');
        parser.string('position');
        parser.string('class');
        parser.string('size');
        parser.booleanOrString('dismissible');
        parser.renderCallback('onOpened');
        parser.renderCallback('onAccepted');
        parser.renderCallback('onDismissed');
        parser.string('acceptEvent');
        parser.string('dismissEvent');
        parser.string('acceptFragment');
        parser.string('dismissFragment');
        parser.string('acceptLocation');
        parser.string('dismissLocation');
        parser.booleanOrString('closeAnimation');
        parser.string('closeEasing');
        parser.number('closeDuration');
        parser.include(up.status.statusOptions);
        parser.booleanOrString('focus');
        parser.booleanOrString('focusVisible');
        parser.boolean('saveScroll');
        parser.boolean('saveFocus');
        parser.booleanOrNumberOrString('scroll');
        parser.json('scrollMap');
        parser.boolean('revealTop');
        parser.number('revealMax');
        parser.number('revealPadding');
        parser.number('revealSnap');
        parser.string('scrollBehavior');
        parser.booleanOrString('history');
        parser.booleanOrString('location');
        parser.booleanOrString('title');
        parser.boolean('metaTags');
        parser.booleanOrString('lang');
        parser.include(up.motion.motionOptions);
        options.guardEvent ??= up.event.build('up:link:follow', { log: ['Following link %o', link] });
        return options;
    }
    function preload(link, options) {
        link = up.fragment.get(link);
        let issue = preloadIssue(link);
        if (issue) {
            return Promise.reject(new up.Error(issue));
        }
        const guardEvent = up.event.build('up:link:preload', { log: ['Preloading link %o', link] });
        return follow(link, {
            abort: false,
            abortable: false,
            background: true,
            cache: true,
            ...options,
            ...up.RenderOptions.NO_INPUT_INTERFERENCE,
            ...up.RenderOptions.NO_PREVIEWS,
            guardEvent,
            preload: true,
        });
    }
    function preloadIssue(link) {
        if (!isSafe(link)) {
            return 'Will not preload an unsafe link';
        }
    }
    function followMethod(link, options = {}) {
        return u.normalizeMethod(options.method || link.getAttribute('up-method') || link.getAttribute('data-method'));
    }
    function followURL(link, options = {}) {
        const url = options.url || link.getAttribute('up-href') || link.getAttribute('href');
        if (url !== '#') {
            return url;
        }
    }
    function isFollowable(link) {
        link = up.fragment.get(link);
        return config.matches(link, 'followSelectors');
    }
    function makeFollowable(link) {
        if (!isFollowable(link)) {
            link.setAttribute('up-follow', '');
        }
    }
    function makeClickable(element) {
        let role = element.matches('a, [up-follow]') ? 'link' : 'button';
        e.setMissingAttrs(element, {
            tabindex: '0',
            role,
            'up-clickable': ''
        });
        element.addEventListener('keydown', function (event) {
            if ((event.key === 'Enter') || (element.role === 'button' && event.key === 'Space')) {
                return forkEventAsUpClick(event);
            }
        });
    }
    up.macro(config.selectorFn('clickableSelectors'), makeClickable);
    function shouldFollowEvent(event, link) {
        if (event.defaultPrevented) {
            return false;
        }
        const betterTargetSelector = `a, [up-follow], ${up.form.fieldSelector()}`;
        const betterTarget = event.target.closest(betterTargetSelector);
        return !betterTarget || (betterTarget === link);
    }
    function isInstant(linkOrDescendant) {
        const element = linkOrDescendant.closest(config.selector('instantSelectors'));
        return element && !isInstantDisabled(element);
    }
    function isInstantDisabled(link) {
        return config.matches(link, 'noInstantSelectors') || config.matches(link, 'noFollowSelectors');
    }
    function convertClicks(layer) {
        layer.on('click', function (event, element) {
            if (up.event.isModified(event)) {
                return;
            }
            if (isInstant(element) && lastInstantTarget === element) {
                up.event.halt(event);
            }
            else if (up.event.inputDevice === 'key' || up.event.isSyntheticClick(event) || (layer.wasHitByMouseEvent(event) && !didUserDragAway(event))) {
                forkEventAsUpClick(event);
            }
            lastMousedownTarget = null;
            lastInstantTarget = null;
        });
        layer.on('touchstart', { passive: true }, function (event, element) {
            lastTouchstartTarget = element;
        });
        layer.on('mousedown', function (event, element) {
            if (up.event.isModified(event)) {
                return;
            }
            lastMousedownTarget = element;
            if (isInstant(element) && !isLongPressPossible(event)) {
                lastInstantTarget = element;
                forkEventAsUpClick(event);
            }
            lastTouchstartTarget = null;
        });
    }
    function isLongPressPossible(mousedownEvent) {
        let mousedownTarget = mousedownEvent.target;
        return (lastTouchstartTarget === mousedownTarget) && mousedownTarget.closest('[href]');
    }
    function didUserDragAway(clickEvent) {
        return lastMousedownTarget && (lastMousedownTarget !== clickEvent.target);
    }
    function forkEventAsUpClick(originalEvent) {
        let forwardedProps = ['clientX', 'clientY', 'button', ...up.event.keyModifiers];
        const newEvent = up.event.fork(originalEvent, 'up:click', forwardedProps);
        up.emit(originalEvent.target, newEvent, { log: false });
    }
    function isSafe(link) {
        const method = followMethod(link);
        return up.network.isSafeMethod(method);
    }
    function onLoadCondition(condition, link, callback) {
        switch (condition) {
            case 'insert':
                callback();
                break;
            case 'reveal': {
                let margin = e.numberAttr(link, 'up-intersect-margin');
                up.fragment.onFirstIntersect(link, callback, { margin });
                break;
            }
            case 'hover':
                new up.LinkFollowIntent(link, callback);
                break;
            case 'manual':
                break;
        }
    }
    function loadDeferred(link, options) {
        let guardEvent = up.event.build('up:deferred:load', { log: ['Loading deferred %o', link] });
        let forcedOptions = {
            navigate: false,
            guardEvent,
            ...options,
        };
        let defaults = {
            target: ':origin',
            cache: 'auto',
            revalidate: 'auto',
            feedback: true,
        };
        return follow(link, forcedOptions, { defaults });
    }
    up.attribute('up-defer', { defaultValue: 'insert' }, function (link, condition) {
        let doLoad = (options) => up.error.muteUncriticalRejection(loadDeferred(link, options));
        onLoadCondition(condition, link, doLoad);
    });
    up.on('up:click', config.selectorFn('followSelectors'), function (event, link) {
        if (shouldFollowEvent(event, link)) {
            up.event.halt(event, { log: true });
            up.focus(link, { preventScroll: true });
            up.error.muteUncriticalRejection(follow(link));
        }
    });
    up.attribute('up-expand', { defaultValue: 'a, [up-href]', macro: true }, function (area, childLinkSelector) {
        let childLink = e.get(area, childLinkSelector);
        if (childLink) {
            e.setMissingAttrs(area, {
                'up-href': e.attr(childLink, 'href'),
                ...e.upAttrs(childLink)
            });
            childLink.upExpandedPair = area.upExpandedPair = [area, childLink];
            e.addClasses(area, e.upClasses(childLink));
            makeFollowable(area);
        }
    });
    up.compiler(config.selectorFn('preloadSelectors'), function (link) {
        if (!isPreloadDisabled(link)) {
            let doPreload = (options) => up.error.muteUncriticalRejection(preload(link, options));
            let condition = e.booleanOrStringAttr(link, 'up-preload');
            if (condition === true || u.isUndefined(condition))
                condition = 'hover';
            onLoadCondition(condition, link, doPreload);
        }
    });
    up.on('up:framework:reset', reset);
    return {
        follow,
        followOptions,
        requestOptions: parseRequestOptions,
        preload,
        makeFollowable,
        isSafe,
        isFollowable,
        shouldFollowEvent,
        convertClicks,
        config,
        loadDeferred,
    };
})();
up.follow = up.link.follow;
up.deferred = { load: up.link.loadDeferred };


/***/ }),
/* 101 */
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
// extracted by mini-css-extract-plugin


/***/ }),
/* 102 */
/***/ (() => {

up.form = (function () {
    const u = up.util;
    const e = up.element;
    const config = new up.Config(() => ({
        groupSelectors: ['[up-form-group]', 'fieldset', 'label', 'form'],
        fieldSelectors: ['select', 'input:not([type=submit], [type=image], [type=button])', 'button[type]:not([type=submit], [type=button])', 'textarea'],
        submitSelectors: ['form:is([up-submit], [up-target], [up-layer], [up-transition])'],
        noSubmitSelectors: ['[up-submit=false]', '[target]', e.crossOriginSelector('action')],
        submitButtonSelectors: ['input[type=submit]', 'input[type=image]', 'button[type=submit]', 'button:not([type])'],
        genericButtonSelectors: ['input[type=button]', 'button[type=button]'],
        validateBatch: true,
        watchInputEvents: ['input', 'change'],
        watchInputDelay: 0,
        watchChangeEvents: ['change'],
        watchableEvents: ['input', 'change'],
        arrayParam: (name) => name.endsWith('[]'),
    }));
    function findFormElements(root, selectorFn) {
        root = e.get(root);
        let elements = e.subtree(root, selectorFn());
        if (root.matches('form[id]')) {
            const formReference = e.attrSelector('form', root.getAttribute('id'));
            const externalElementsSelector = selectorFn(formReference);
            const externalElements = up.fragment.all(externalElementsSelector, { layer: root });
            elements = u.uniq([...elements, ...externalElements]);
        }
        return elements;
    }
    const [fieldSelector, isField] = config.selectorFns('fieldSelectors');
    function findFields(root) {
        return findFormElements(root, fieldSelector);
    }
    function findFieldsAndButtons(container) {
        return [
            ...findFields(container),
            ...findSubmitButtons(container),
            ...findGenericButtons(container),
        ];
    }
    const [submitButtonSelector, isSubmitButton] = config.selectorFns('submitButtonSelectors');
    function findSubmitButtons(root) {
        return findFormElements(root, submitButtonSelector);
    }
    const genericButtonSelector = config.selectorFn('genericButtonSelectors');
    function findGenericButtons(root) {
        return findFormElements(root, genericButtonSelector);
    }
    const submit = up.mockable((form, options) => {
        return up.render(submitOptions(form, options));
    });
    function submitOptions(form, options, parserOptions) {
        form = up.fragment.get(form);
        form = getForm(form);
        options = u.options(options);
        let parser = new up.OptionsParser(form, options, parserOptions);
        parser.include(destinationOptions);
        parser.string('failTarget', { default: up.fragment.tryToTarget(form) });
        options.guardEvent ||= up.event.build('up:form:submit', {
            submitButton: options.submitButton,
            log: 'Submitting form',
            params: options.params,
            form,
        });
        options.origin ||= up.viewport.focusedElementWithin(form) || options.submitButton || form;
        options.activeElements = u.uniq([options.origin, options.submitButton, form].filter(u.isElement));
        parser.include(up.link.followOptions);
        Object.assign(options, submitButtonOverrides(options.submitButton));
        return options;
    }
    function watchOptions(field, options, parserOptions = {}) {
        options = u.options(options);
        parserOptions.closest ??= true;
        parserOptions.attrPrefix ??= 'up-watch-';
        let parser = new up.OptionsParser(field, options, parserOptions);
        parser.include(up.status.statusOptions, parserOptions);
        parser.string('event');
        parser.number('delay');
        let config = up.form.config;
        if (options.event === 'input') {
            options.event = u.evalOption(config.watchInputEvents, field);
            options.delay ??= config.watchInputDelay;
        }
        else if (options.event === 'change') {
            options.event = u.evalOption(config.watchChangeEvents, field);
        }
        options.origin ||= field;
        return options;
    }
    function validateOptions(field, options, parserOptions = {}) {
        options = u.options(options);
        let parser = new up.OptionsParser(field, options, { ...parserOptions, closest: true, attrPrefix: 'up-validate-' });
        parser.string('url');
        parser.string('method', { normalize: u.normalizeMethod });
        parser.boolean('batch', { default: config.validateBatch });
        parser.json('params');
        parser.json('headers');
        parser.include(watchOptions, { defaults: { event: 'change' } });
        return options;
    }
    function disableContainerTemp(container) {
        let controls = findFieldsAndButtons(container);
        return u.sequence(u.map(controls, disableControlTemp));
    }
    function disableControlTemp(control) {
        if (control.disabled)
            return;
        let focusFallback;
        if (document.activeElement === control) {
            focusFallback = findGroup(control);
            control.disabled = true;
            up.focus(focusFallback, { force: true, preventScroll: true });
        }
        else {
            control.disabled = true;
        }
        return () => { control.disabled = false; };
    }
    function getDisableContainers(disable, origin) {
        let originScope = () => getRegion(origin);
        if (disable === true) {
            return [originScope()];
        }
        else if (u.isElement(disable)) {
            return [disable];
        }
        else if (u.isString(disable)) {
            return up.fragment.subtree(originScope(), disable, { origin });
        }
        else if (u.isArray(disable)) {
            return u.flatMap(disable, (d) => getDisableContainers(d, origin));
        }
        else {
            return [];
        }
    }
    function getDisablePreviewFn(disable, origin) {
        return function (preview) {
            let containers = getDisableContainers(disable, origin);
            for (let container of containers) {
                preview.disable(container);
            }
        };
    }
    function setContainerDisabled(container, disabled) {
        for (let control of findFieldsAndButtons(container)) {
            control.disabled = disabled;
        }
    }
    function destinationOptions(form, options, parserOptions) {
        options = u.options(options);
        form = getForm(form);
        const parser = new up.OptionsParser(form, options, parserOptions);
        parser.string('contentType', { attr: 'enctype' });
        parser.json('headers');
        const paramParts = [
            up.Params.fromForm(form),
            e.jsonAttr(form, 'up-params'),
        ];
        const headerParts = [
            e.jsonAttr(form, 'up-headers'),
        ];
        const submitButton = (options.submitButton ??= findSubmitButtons(form)[0]);
        if (submitButton) {
            paramParts.push(up.Params.fromFields(submitButton), e.jsonAttr(submitButton, 'up-params'));
            headerParts.push(e.jsonAttr(submitButton, 'up-headers'));
            options.method ||= submitButton.getAttribute('formmethod');
            options.url ||= submitButton.getAttribute('formaction');
        }
        options.params = up.Params.merge(...paramParts, options.params);
        options.headers = u.merge(...headerParts, options.headers);
        parser.string('url', { attr: 'action', default: up.fragment.source(form) });
        parser.string('method', {
            attr: ['up-method', 'data-method', 'method'],
            default: 'GET',
            normalize: u.normalizeMethod
        });
        if (options.method === 'GET') {
            options.url = up.Params.stripURL(options.url);
        }
        return options;
    }
    function submitButtonOverrides(submitButton) {
        if (!submitButton)
            return {};
        let followOptions = up.link.followOptions(submitButton, {}, { defaults: false });
        return u.omit(followOptions, ['method', 'url', 'guardEvent', 'origin', 'params', 'headers']);
    }
    function watch(...args) {
        let [root, options, callback] = u.args(args, 'val', 'options', 'callback');
        root = up.element.get(root);
        callback ||= watchCallbackFromElement(root) || up.fail('No callback given for up.watch()');
        const watcher = new up.FieldWatcher(root, options, callback);
        return watcher.start();
    }
    function watchCallbackFromElement(element) {
        return up.script.callbackAttr(element, 'up-watch', { argNames: ['value', 'name', 'options'] });
    }
    function autosubmit(target, options = {}) {
        const onChange = (_diff, renderOptions) => submit(target, renderOptions);
        return watch(target, { logPrefix: 'up.autosubmit()', ...options, batch: true }, onChange);
    }
    function getGroupSelectors() {
        return up.migrate.migratedFormGroupSelectors?.() || config.groupSelectors;
    }
    function findGroup(field) {
        return findGroupSolution(field).element;
    }
    function findGroupSolution(field) {
        return u.findResult(getGroupSelectors(), function (groupSelector) {
            let group = field.closest(groupSelector);
            if (group) {
                let strongDerivedGroupTarget = up.fragment.tryToTarget(group, { strong: true });
                let goodDerivedFieldTarget = up.fragment.tryToTarget(field);
                let groupHasFieldTarget = goodDerivedFieldTarget && (group !== field) && `${groupSelector}:has(${goodDerivedFieldTarget})`;
                let target = strongDerivedGroupTarget || groupHasFieldTarget;
                if (target) {
                    return {
                        target,
                        element: group,
                        origin: field
                    };
                }
            }
        });
    }
    function validate(...args) {
        let options = parseValidateArgs(...args);
        let form = getForm(options.origin);
        let validator = getFormValidator(form);
        return validator.validate(options);
    }
    function parseValidateArgs(originOrTarget, ...args) {
        const options = u.extractOptions(args);
        if (options.origin) {
            options.target ||= up.fragment.toTarget(originOrTarget);
        }
        else {
            options.origin ||= up.fragment.get(originOrTarget);
        }
        return options;
    }
    function getForm(element) {
        return getLiteralForm(element) || getClosestForm(element) || getAssociatedForm(element);
    }
    function getLiteralForm(element) {
        if (element instanceof HTMLFormElement)
            return element;
    }
    function getClosestForm(element) {
        return element.closest('form');
    }
    function getAssociatedForm(element) {
        let formID = element.getAttribute('form');
        if (formID) {
            let selector = 'form' + e.idSelector(formID);
            return up.fragment.get(selector, { layer: element });
        }
    }
    function getFormValidator(form) {
        return form.upFormValidator ||= setupFormValidator(form);
    }
    function setupFormValidator(form) {
        const validator = new up.FormValidator(form);
        const stop = validator.start();
        up.destructor(form, stop);
        return validator;
    }
    function getRegion(origin) {
        return getOriginRegion(origin) || up.layer.current.element;
    }
    function getOriginRegion(origin) {
        if (origin) {
            return getForm(origin) || up.layer.get(origin)?.element;
        }
    }
    const trackFields = up.mockable(function (...args) {
        let [root, { guard }, callback] = u.args(args, 'val', 'options', 'callback');
        let filter = function (fields) {
            let region = getRegion(root);
            return u.filter(fields, function (field) {
                return (root === region || root.contains(field))
                    && (getRegion(field) === region)
                    && (!guard || guard(field));
            });
        };
        return up.fragment.trackSelector(fieldSelector(), { filter }, callback);
    });
    function focusedField() {
        return u.presence(document.activeElement, isField);
    }
    function isSubmittable(form) {
        form = up.fragment.get(form);
        return config.matches(form, 'submitSelectors');
    }
    up.on('submit', config.selectorFn('submitSelectors'), function (event, form) {
        const submitButton = u.presence(event.submitter, isSubmitButton);
        if (submitButton?.getAttribute('up-submit') === 'false')
            return;
        if (event.defaultPrevented)
            return;
        up.event.halt(event, { log: true });
        up.error.muteUncriticalRejection(submit(form, { submitButton }));
    });
    up.compiler('[up-switch]', (switcher) => {
        return new up.Switcher(switcher).start();
    });
    up.attribute('up-watch', (formOrField) => watch(formOrField));
    up.compiler('[up-validate]', { rerun: true }, function (element) {
        let form = getForm(element);
        if (form)
            getFormValidator(form);
    });
    up.attribute('up-autosubmit', (formOrField) => autosubmit(formOrField, { logPrefix: '[up-autosubmit]' }));
    return {
        config,
        submit,
        submitOptions,
        destinationOptions,
        submitButtonOverrides,
        watchOptions,
        validateOptions,
        isSubmittable,
        watch,
        validate,
        autosubmit,
        fieldSelector,
        fields: findFields,
        trackFields,
        isField,
        submitButtons: findSubmitButtons,
        focusedField,
        disableTemp: disableContainerTemp,
        setDisabled: setContainerDisabled,
        getDisablePreviewFn,
        group: findGroup,
        groupSolution: findGroupSolution,
        groupSelectors: getGroupSelectors,
        get: getForm,
        getRegion,
    };
})();
up.submit = up.form.submit;
up.watch = up.form.watch;
up.autosubmit = up.form.autosubmit;
up.validate = up.form.validate;


/***/ }),
/* 103 */
/***/ (() => {

up.status = (function () {
    const u = up.util;
    const e = up.element;
    const config = new up.Config(() => ({
        currentClasses: ['up-current'],
        activeClasses: ['up-active'],
        loadingClasses: ['up-loading'],
        revalidatingClasses: ['up-revalidating'],
        navSelectors: ['[up-nav]', 'nav'],
        noNavSelectors: ['[up-nav=false]'],
    }));
    let namedPreviewFns = new up.Registry('preview');
    const SELECTOR_LINK = 'a, [up-href]';
    function linkCurrentURLs(link) {
        return link.upCurrentURLs ||= new up.LinkCurrentURLs(link);
    }
    function getNavLocations(nav) {
        let layerRef = e.attr(nav, 'up-layer') || 'origin';
        let layers = up.layer.getAll(layerRef, { origin: nav });
        return u.compact(layers.map(getMatchableLayerLocation));
    }
    function updateNav(nav, links, { newLinks, anyLocationChanged }) {
        let currentLocations = (!anyLocationChanged && nav.upNavLocations) || getNavLocations(nav);
        if (newLinks || !u.isEqual(nav.upNavLocations, currentLocations)) {
            for (let link of links) {
                const isCurrent = linkCurrentURLs(link).isAnyCurrent(currentLocations);
                for (let currentClass of config.currentClasses) {
                    link.classList.toggle(currentClass, isCurrent);
                }
                e.setAttrPresence(link, 'aria-current', 'page', isCurrent);
            }
            nav.upNavLocations = currentLocations;
        }
    }
    function updateNavsAround(root, opts) {
        const navSelector = config.selector('navSelectors');
        const fullNavs = e.around(root, navSelector);
        for (let fullNav of fullNavs) {
            let links = e.subtree(fullNav, SELECTOR_LINK);
            updateNav(fullNav, links, opts);
        }
    }
    function getMatchableLayerLocation(layer) {
        return u.matchableURL(layer.location);
    }
    function findActivatableAreas(element) {
        return element.upExpandedPair || [element];
    }
    function runPreviews(request, renderOptions) {
        let { bindLayer } = request;
        let focusCapsule = up.FocusCapsule.preserve(bindLayer);
        let applyPreviews = () => doRunPreviews(request, renderOptions);
        let revertPreviews = bindLayer.asCurrent(applyPreviews);
        focusCapsule?.autoVoid();
        return () => {
            bindLayer.asCurrent(revertPreviews);
            focusCapsule?.restore(bindLayer, { preventScroll: true });
        };
    }
    function doRunPreviews(request, renderOptions) {
        let { fragment, fragments, origin } = request;
        let cleaner = u.cleaner();
        let previewForFragment = (fragment) => new up.Preview({ fragment, request, renderOptions, cleaner });
        let singlePreview = previewForFragment(fragment);
        singlePreview.run(resolvePreviewFns(renderOptions.preview));
        singlePreview.run(getPlaceholderPreviewFn(renderOptions.placeholder));
        singlePreview.run(getFeedbackClassesPreviewFn(renderOptions.feedback, fragments));
        singlePreview.run(up.form.getDisablePreviewFn(renderOptions.disable, origin));
        for (let fragment of fragments) {
            let eachPreview = previewForFragment(fragment);
            eachPreview.run(up.fragment.matchSelectorMap(fragment, renderOptions.previewMap));
            eachPreview.run(up.fragment.matchSelectorMap(fragment, renderOptions.placeholderMap).flatMap(getPlaceholderPreviewFn));
        }
        return cleaner.clean;
    }
    function getPlaceholderPreviewFn(placeholder) {
        if (!placeholder)
            return;
        return function (preview) {
            preview.showPlaceholder(placeholder);
        };
    }
    function resolvePreviewFns(value) {
        if (u.isFunction(value)) {
            return [value];
        }
        else if (u.isString(value)) {
            return resolvePreviewString(value);
        }
        else if (u.isArray(value)) {
            return value.flatMap(resolvePreviewFns);
        }
        else {
            return [];
        }
    }
    function resolvePreviewString(str) {
        return u.map(u.parseScalarJSONPairs(str), ([name, parsedOptions]) => {
            let previewFn = namedPreviewFns.get(name);
            return function (preview, runOptions) {
                up.puts('[up-preview]', 'Showing preview %o', name);
                return previewFn(preview, parsedOptions || runOptions);
            };
        });
    }
    function getActiveElements({ origin, activeElements }) {
        activeElements ||= u.wrapList(origin);
        return u.flatMap(activeElements, findActivatableAreas);
    }
    function getFeedbackClassesPreviewFn(feedbackOption, fragments) {
        if (!feedbackOption)
            return;
        return function (preview) {
            const { renderOptions } = preview;
            if (renderOptions.expiredResponse) {
                preview.addClassBatch(fragments, config.revalidatingClasses);
            }
            else {
                preview.addClassBatch(getActiveElements(renderOptions), config.activeClasses);
                preview.addClassBatch(fragments, config.loadingClasses);
            }
        };
    }
    function statusOptions(element, options, parserOptions) {
        options = u.options(options);
        const parser = new up.OptionsParser(element, options, parserOptions);
        parser.booleanOrString('disable');
        parser.boolean('feedback');
        parser.string('preview');
        parser.booleanOrString('revalidatePreview');
        parser.string('placeholder');
        return options;
    }
    up.on('up:compilers:before', (_event, newFragment) => {
        updateNavsAround(newFragment, { newLinks: true, anyLocationChanged: false });
    });
    up.on('up:layer:location:changed up:layer:opened up:layer:dismissed up:layer:accepted', () => {
        updateNavsAround(document.body, { newLinks: false, anyLocationChanged: true });
    });
    return {
        config,
        preview: namedPreviewFns.put,
        resolvePreviewFns,
        runPreviews,
        statusOptions,
    };
})();
up.preview = up.status.preview;


/***/ }),
/* 104 */
/***/ (() => {

up.radio = (function () {
    const e = up.element;
    const config = new up.Config(() => ({
        hungrySelectors: ['[up-hungry]'],
        noHungrySelectors: ['[up-hungry=false]'],
        pollInterval: 30000,
    }));
    function hungrySteps(renderOptions) {
        let { hungry, origin, layer: renderLayer, meta } = renderOptions;
        let steps = { current: [], other: [] };
        if (!hungry)
            return steps;
        let hungrySelector = config.selector('hungrySelectors');
        const layerPreference = [renderLayer, ...renderLayer.ancestors, ...renderLayer.descendants];
        for (let elementLayer of layerPreference) {
            let hungries = up.fragment.all(elementLayer.element, hungrySelector, { layer: elementLayer });
            for (let element of hungries) {
                let selector = up.fragment.tryToTarget(element, { origin });
                if (!selector) {
                    up.warn('[up-hungry]', 'Ignoring untargetable fragment %o', element);
                    continue;
                }
                let ifLayer = e.attr(element, 'up-if-layer');
                let applicableLayers = ifLayer ? up.layer.getAll(ifLayer, { baseLayer: elementLayer }) : [elementLayer];
                let motionOptions = up.motion.motionOptions(element);
                let selectEvent = up.event.build('up:fragment:hungry', { log: false });
                let selectCallback = up.script.callbackAttr(element, 'up-on-hungry', { expandObject: ['newFragment', 'renderOptions'] });
                let step = {
                    selector,
                    oldElement: element,
                    layer: elementLayer,
                    origin,
                    ...motionOptions,
                    placement: 'swap',
                    keep: true,
                    maybe: true,
                    meta,
                    selectEvent,
                    selectCallback,
                    originalRenderOptions: renderOptions,
                };
                if (applicableLayers.includes(renderLayer)) {
                    let list = renderLayer === elementLayer ? steps.current : steps.other;
                    list.push(step);
                }
            }
        }
        steps.other = up.fragment.compressNestedSteps(steps.other);
        return steps;
    }
    function startPolling(fragment, options = {}) {
        up.FragmentPolling.forFragment(fragment).forceStart(options);
    }
    function stopPolling(element) {
        up.FragmentPolling.forFragment(element).forceStop();
    }
    function pollOptions(fragment, options = {}) {
        const defaults = { background: true };
        const parser = new up.OptionsParser(fragment, options, { defaults });
        parser.number('interval', { default: config.pollInterval });
        parser.string('ifLayer', { default: 'front' });
        parser.include(up.link.requestOptions);
        parser.include(up.status.statusOptions);
        return options;
    }
    up.attribute('up-poll', function (fragment) {
        up.FragmentPolling.forFragment(fragment).onPollAttributeObserved();
    });
    up.macro('[up-flashes]', function (fragment) {
        e.setMissingAttrs(fragment, {
            'up-hungry': '',
            'up-if-layer': 'subtree',
            'up-keep': '',
            'role': 'alert',
        });
        fragment.addEventListener('up:fragment:keep', function (event) {
            if (!e.isEmpty(event.newFragment))
                event.preventDefault();
        });
    });
    return {
        config,
        hungrySteps,
        startPolling,
        stopPolling,
        pollOptions,
    };
})();


/***/ }),
/* 105 */
/***/ (() => {

(function () {
    function isRailsUJSLoaded() {
        return window.Rails ||
            window.jQuery?.rails;
    }
    function swapAttr(element, dataAttr, upAttr) {
        if (element.hasAttribute(dataAttr)) {
            let dataValue = element.getAttribute(dataAttr);
            up.element.setMissingAttr(element, upAttr, dataValue);
            element.removeAttribute(dataAttr);
        }
    }
    function defineMacro(elementSelector, relevantFn) {
        up.macro(`:is([data-confirm], [data-method]):is(${elementSelector})`, function (element) {
            if (isRailsUJSLoaded() && relevantFn(element)) {
                swapAttr(element, 'data-confirm', 'up-confirm');
                swapAttr(element, 'data-method', 'up-method');
            }
        });
    }
    defineMacro('a[href], [up-href]', (el) => up.link.isFollowable(el));
    defineMacro('form, input[type=submit], button[type=submit], button:not([type])', (el) => up.form.isSubmittable(up.form.get(el)));
})();


/***/ })
/******/ 	]);
/************************************************************************/
/******/ 	// The module cache
/******/ 	var __webpack_module_cache__ = {};
/******/ 	
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/ 		// Check if module is in cache
/******/ 		var cachedModule = __webpack_module_cache__[moduleId];
/******/ 		if (cachedModule !== undefined) {
/******/ 			return cachedModule.exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = __webpack_module_cache__[moduleId] = {
/******/ 			// no module.id needed
/******/ 			// no module.loaded needed
/******/ 			exports: {}
/******/ 		};
/******/ 	
/******/ 		// Execute the module function
/******/ 		__webpack_modules__[moduleId](module, module.exports, __webpack_require__);
/******/ 	
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/ 	
/************************************************************************/
/******/ 	/* webpack/runtime/make namespace object */
/******/ 	(() => {
/******/ 		// define __esModule on exports
/******/ 		__webpack_require__.r = (exports) => {
/******/ 			if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 				Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 			}
/******/ 			Object.defineProperty(exports, '__esModule', { value: true });
/******/ 		};
/******/ 	})();
/******/ 	
/************************************************************************/
var __webpack_exports__ = {};
// This entry needs to be wrapped in an IIFE because it needs to be isolated against other modules in the chunk.
(() => {
__webpack_require__(1);
__webpack_require__(2);
__webpack_require__(3);
__webpack_require__(4);
__webpack_require__(5);
__webpack_require__(6);
__webpack_require__(7);
__webpack_require__(9);
__webpack_require__(10);
__webpack_require__(11);
__webpack_require__(12);
__webpack_require__(13);
__webpack_require__(14);
__webpack_require__(15);
__webpack_require__(16);
__webpack_require__(17);
__webpack_require__(18);
__webpack_require__(19);
__webpack_require__(20);
__webpack_require__(21);
__webpack_require__(22);
__webpack_require__(23);
__webpack_require__(24);
__webpack_require__(25);
__webpack_require__(26);
__webpack_require__(27);
__webpack_require__(28);
__webpack_require__(29);
__webpack_require__(30);
__webpack_require__(31);
__webpack_require__(32);
__webpack_require__(33);
__webpack_require__(34);
__webpack_require__(35);
__webpack_require__(36);
__webpack_require__(37);
__webpack_require__(38);
__webpack_require__(39);
__webpack_require__(40);
__webpack_require__(41);
__webpack_require__(42);
__webpack_require__(43);
__webpack_require__(44);
__webpack_require__(45);
__webpack_require__(46);
__webpack_require__(47);
__webpack_require__(48);
__webpack_require__(49);
__webpack_require__(50);
__webpack_require__(51);
__webpack_require__(52);
__webpack_require__(53);
__webpack_require__(54);
__webpack_require__(55);
__webpack_require__(56);
__webpack_require__(57);
__webpack_require__(58);
__webpack_require__(59);
__webpack_require__(60);
__webpack_require__(61);
__webpack_require__(62);
__webpack_require__(63);
__webpack_require__(64);
__webpack_require__(65);
__webpack_require__(66);
__webpack_require__(67);
__webpack_require__(68);
__webpack_require__(69);
__webpack_require__(70);
__webpack_require__(71);
__webpack_require__(72);
__webpack_require__(73);
__webpack_require__(74);
__webpack_require__(75);
__webpack_require__(76);
__webpack_require__(77);
__webpack_require__(78);
__webpack_require__(79);
__webpack_require__(80);
__webpack_require__(81);
__webpack_require__(82);
__webpack_require__(83);
__webpack_require__(84);
__webpack_require__(85);
__webpack_require__(86);
__webpack_require__(87);
__webpack_require__(88);
__webpack_require__(89);
__webpack_require__(90);
__webpack_require__(91);
__webpack_require__(93);
__webpack_require__(95);
__webpack_require__(96);
__webpack_require__(98);
__webpack_require__(100);
__webpack_require__(102);
__webpack_require__(103);
__webpack_require__(104);
__webpack_require__(105);
up.framework.onEvaled();

})();

/******/ })()
;