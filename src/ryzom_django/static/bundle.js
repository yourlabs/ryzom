function MDCFileField_set_update_name(input_id, label_id, empty_value) {
    function update_name(event) {
        var file_name = event.target.value;
        var label = getElementByUuid(label_id);
        label.innerHTML = (file_name || empty_value);
    }
    document.querySelector(('#' + input_id)).addEventListener('change',update_name);
}

class MDCSnackBar extends HTMLElement {
    connectedCallback() {
        [new mdc.snackbar.MDCSnackbar(this).open()];
    }
}

window.customElements.define("mdc-snack-bar", MDCSnackBar);
function MDCCheckboxListItem_click_input(event) {
    event.stopPropagation();
    var elem = event.target.querySelector('input');
    if (elem) {
        elem.click();
    }
}

function MDCMultipleChoicesCheckbox_update_inputs(event) {
    var input_list = event.currentTarget;
    var checked = input_list.querySelectorAll('input:checked');
    var unchecked = input_list.querySelectorAll('input:not(:checked)');
    function disable(elem, pos, arr) {
        elem.disabled = true;
        var list_item = document.querySelector((('[data-list-item-of="' + elem.id) + '"]')).classList.add('mdc-deprecated-list-item--disabled');
    }
    function enable(elem, pas, arr) {
        elem.disabled = undefined;
        var list_item = document.querySelector((('[data-list-item-of="' + elem.id) + '"]')).classList.remove('mdc-deprecated-list-item--disabled');
    }
    if (checked.length  >=  this.max) {
        unchecked.forEach(disable);
    } else {
        unchecked.forEach(enable);
    }
}

class MDCSelectOutlined extends HTMLElement {
    connectedCallback() {
        this.addEventListener('MDCSelect:change',this.change.bind(this));
    }
    change(event) {
        var hidden = this.querySelector('input[type=hidden]');
        var option = this.querySelector('[aria-selected=true]');
        hidden.value = option.dataset.value;
        var input = event.target.querySelector('input');
        up.emit(input,'change');
    }
}

window.customElements.define("mdc-select-outlined", MDCSelectOutlined);
class MDCAccordionToggle extends HTMLElement {
    connectedCallback() {
        this.addEventListener('click',this.click.bind(this));
        this.addEventListener('keyup',this.click.bind(this));
        this.addEventListener('focusout',this.focusout.bind(this));
    }
    click(event) {
        if ((event.code && event.code  !=  'Enter')) {
            return;
        }
        var section = this.parentElement;
        if ((section.classList.contains('active') || section.classList.contains('opened'))) {
            section.toggle(this.dataset.arrowId);
        } else {
            section.parentElement.closeAll();
            section.open(this.dataset.arrowId);
        }
    }
    focusout(event) {
        setTimeout(
            () => {return this.setAttribute('tabindex',0)}
        ,10);
    }
    open() {
        this.classList.add('mdc-deprecated-list-item--selected');
        var arrow = this.querySelector('.arrow');
        arrow.classList.remove('right');
        arrow.classList.add('down');
    }
    close() {
        this.classList.remove('mdc-deprecated-list-item--selected');
        var arrow = this.querySelector('.arrow');
        arrow.classList.remove('down');
        arrow.classList.add('right');
    }
}

window.customElements.define("mdc-accordion-toggle", MDCAccordionToggle);
class MDCAccordionMenu extends HTMLElement {
    connectedCallback() {
        window.addEventListener('load',this.ready.bind(this));
    }
    ready() {
        var max_height = this.style.maxHeight;
        this.style.transition = '';
        this.close();
        this.from_px = '0px';
        if ((max_height && max_height  !=  '0px')) {
            this.from_px = max_height;
            this.open();
        }
    }
    start_layout() {
        this.style.transition = '';
        this.from_px = this.style.maxHeight;
        this.style.maxHeight = 'initial';
        this.rect = this.getBoundingClientRect();
        var closest = this.parentElement.closest('mdc-accordion-menu');
        if (closest) {
            closest.start_layout();
        }
    }
    end_layout() {
        this.style.maxHeight = this.from_px;
        this.getBoundingClientRect();
        this.style.transition = 'max-height 0.4s ease-out';
        this.style.maxHeight = (this.rect.height + 'px');
        var closest = this.parentElement.closest('mdc-accordion-menu');
        if (closest) {
            closest.end_layout();
        }
    }
    open() {
        this.ariaHidden = 'false';
        this.start_layout();
        this.end_layout();
        var i = 0;
        for (const elem of this.querySelectorAll('[tabindex]')) {
            elem.setAttribute('tabindex',i);
            i += 1;
        }
    }
    close() {
        this.ariaHidden = 'true';
        this.querySelectorAll('[tabindex]').forEach(
            (elem) => {return elem.setAttribute('tabindex',-(1))}
        );
        this.style.maxHeight = 0;
    }
}

window.customElements.define("mdc-accordion-menu", MDCAccordionMenu);
class MDCAccordionSection extends HTMLElement {
    open() {
        this.classList.add('active');
        var toggle = this.querySelector('mdc-accordion-toggle');
        toggle.open();
        var menu = this.querySelector('mdc-accordion-menu');
        menu.open();
    }
    close() {
        this.classList.remove('active');
        this.classList.remove('opened');
        var toggle = this.querySelector('mdc-accordion-toggle');
        toggle.close();
        var menu = this.querySelector('mdc-accordion-menu');
        menu.close();
    }
    toggle() {
        if ((this.classList.contains('active') || this.classList.contains('opened'))) {
            this.close();
        } else {
            this.open();
        }
    }
}

window.customElements.define("mdc-accordion-section", MDCAccordionSection);
class MDCAccordion extends HTMLElement {
    closeAll() {
        var sections = this.querySelectorAll('mdc-accordion-section');
        for (const section of sections) {
            section.close();
        }
    }
}

window.customElements.define("mdc-accordion", MDCAccordion);
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
        if ((document.up && document.up.visit)) {
            up.visit((url.pathname + search),{target: '.mdc-data-table'});
        } else {
            document.location.href = (url.pathname + search);
        }
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
class MDCDialog extends HTMLElement {
    connectedCallback() {
        this.addEventListener('MDCDialog:closing',this.handle_closing.bind(this));
        this.addEventListener('MDCDialog:closed',this.handle_closed.bind(this));
        this.addEventListener('MDCDialog:opening',this.handle_opening.bind(this));
        this.addEventListener('MDCDialog:opened',this.handle_opened.bind(this));
    }
    onclosing(event) {
        /* pass */
    }
    onclosed(event) {
        /* pass */
    }
    onopening(event) {
        /* pass */
    }
    onopened(event) {
        /* pass */
    }
    open() {
        this.MDCDialog.open();
    }
    close() {
        this.MDCDialog.close();
    }
    layout() {
        this.MDCDialog.layout();
    }
    handle_closing(event) {
        this.onclosing(event);
    }
    handle_closed(event) {
        this.onclosed(event);
    }
    handle_opening(event) {
        this.onopening(event);
    }
    handle_opened(event) {
        this.onopened(event);
    }
}

window.customElements.define("mdc-dialog", MDCDialog);
class MDCMenu extends HTMLElement {
    connectedCallback() {
        console.log('menu connected');
        this.menu = new mdc.menu.MDCMenu(this);
    }
    open() {
        this.menu.open = true;
    }
    close() {
        this.menu.open = false;
    }
    toggle() {
        console.log('toggle');
        if (this.menu.open) {
            console.log('close');
            this.close();
        } else {
            console.log('open');
            this.open();
        }
    }
}

window.customElements.define("mdc-menu", MDCMenu);
class PlaceholderRemover extends HTMLElement {
    connectedCallback() {
        this.setup();
    }
    setup() {
        if (!(this.input)) {
            this.input = this.querySelector('input');
            this.field = this.querySelector('label');
            if ((this.input && this.field)) {
                this.input.addEventListener('focus',this.focus.bind(this));
                this.input.addEventListener('blur',this.blur.bind(this));
            }
        }
    }
    focus(event) {
        this.setup();
        event.target.value = '';
    }
    blur(event) {
        this.setup();
        if ((event && event.target)) {
            event.target.value = '';
            this.field.MDCTextField.foundation.deactivateFocus();
        }
    }
}

window.customElements.define("placeholder-remover", PlaceholderRemover);
async function AjaxFormMixin_on_form_submit(event) {
    event.preventDefault();
    var form = event.target;
    await fetch(form.action,{
        'method': form.method,
        'body': new FormData(form)
    }).then(
        (response) => {return console.log(response)}
    );
    form.reset();
}

class DeleteButton extends HTMLElement {
    connectedCallback() {
        this.addEventListener('click',this.delete.bind(this));
    }
    async delete(event) {
        var csrf = document.querySelector('[name="csrfmiddlewaretoken"]');
        console.log('url',this.attributes['delete-url'].value);
        await fetch(this.attributes['delete-url'].value,{
            method: 'delete',
            headers: {'X-CSRFTOKEN': csrf.value},
            redirect: 'manual'
        }).then(
            (response) => {return console.log(response)}
        );
    }
}

window.customElements.define("delete-button", DeleteButton);