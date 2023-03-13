function MDCFileField_set_update_name(input_id, label_id) {
    function update_name(event) {
        var file_name = event.target.value;
        var label = getElementByUuid(label_id);
        label.innerHTML = (file_name || 'No file selected');
    }
    document.querySelector(('#' + input_id)).addEventListener('change',update_name);
}

function MDCCheckboxListItem_click_input(event) {
    event.stopPropagation();
    var elem = event.target.querySelector('input');
    if (elem) {
        elem.click();
    }
}

function MDCMultipleChoicesCheckbox_update_inputs(event) {
    var input_list = event.target;
    var checked = input_list.querySelectorAll('input:checked');
    var unchecked = input_list.querySelectorAll('input:not(:checked)');
    function disable(elem, pos, arr) {
        elem.disabled = true;
        var list_item = document.querySelector((('[data-list-item-of="' + elem.id) + '"]')).classList.add('mdc-list-item--disabled');
    }
    function enable(elem, pas, arr) {
        elem.disabled = undefined;
        var list_item = document.querySelector((('[data-list-item-of="' + elem.id) + '"]')).classList.remove('mdc-list-item--disabled');
    }
    if (checked.length  >=  this.max) {
        unchecked.forEach(disable);
    } else {
        unchecked.forEach(enable);
    }
}

class MDCSelectOutlined extends HTMLElement {
    connectedCallback() {
        this.addEventListener('change',this.change.bind(this));
    }
    change(event) {
        var hidden = this.querySelector('input[type=hidden]');
        var option = this.querySelector('[aria-selected=true]');
        hidden.value = option.dataset.value;
    }
}

window.customElements.define("mdc-select-outlined", MDCSelectOutlined);
class MDCSelectPerPage extends HTMLElement {
    connectedCallback() {
        this.addEventListener('MDCSelect:change',this.change.bind(this));
    }
    async change(event) {
        var url = new URL(document.location);
        if (url.search.indexOf('per_page=')  >  0) {
            var search = url.search.replace(new RegExp('per_page=[^&]*'),('per_page=' + event.detail.value));
        } else {
            search = ('?per_page=' + event.detail.value);
        }
        up.visit((url.pathname + search),{target: '.mdc-data-table'});
    }
}

window.customElements.define("mdc-select-per-page", MDCSelectPerPage);
class MDCDrawerToggle extends HTMLElement {
    connectedCallback() {
        this.addEventListener('click',this.toggle.bind(this));
    }
    toggle() {
        var drawer = document.getElementById(this.attributes['data-drawer-id'].value);
        drawer = mdc.drawer.MDCDrawer.attachTo(drawer);
        drawer.open = !(drawer.open);
    }
}

window.customElements.define("mdc-drawer-toggle", MDCDrawerToggle);
class ToggleNextElement extends HTMLElement {
    connectedCallback() {
        this.addEventListener('click',this.click.bind(this));
    }
    click(event) {
        var element = this.nextElementSibling;
        if (element.style.display  ==  'none') {
            element.style.display = 'block';
            this.classList.add('open');
        } else {
            element.style.display = 'none';
            this.classList.remove('open');
        }
    }
}

window.customElements.define("toggle-element", ToggleNextElement);
function ListAction_onclick(element) {
    var link = (element.attributes.href.value + '?');
    for (const checkbox of document.querySelectorAll('[data-pk]:checked')) {
        link += ('&pk=' + checkbox.attributes['data-pk'].value);
    }
    up.modal.visit(link,{target: '.main-inner'});
}

class ListActions extends HTMLElement {
    connectedCallback() {
        this.previousElementSibling.addEventListener('change',this.change.bind(this));
    }
    change(event) {
        if (event.target.checked) {
            this.style.display = 'block';
        } else {
            if (!(this.previousElementSibling.querySelector(':checked'))) {
                this.style.display = 'none';
            }
        }
    }
}

window.customElements.define("list-actions", ListActions);
function mdcTopAppBar_setup() {
    window.drawer = mdc.drawer.MDCDrawer.attachTo(document.getElementById('drawer'));
    var topAppBar = mdc.topAppBar.MDCTopAppBar.attachTo(document.getElementById('app-bar'));
    topAppBar.setScrollTarget(document.getElementById('main'));
    topAppBar.listen('MDCTopAppBar:nav',mdcTopAppBar_nav);
}

function mdcTopAppBar_nav() {
    window.drawer.open = !(window.drawer.open);
}
