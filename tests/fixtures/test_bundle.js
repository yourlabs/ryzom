class MyComponent extends HTMLElement {
    connectedCallback() {
        this.connected = true;
    }
}

window.customElements.define("foo-bar", MyComponent);
function OtherComponent_on_form_submit() {
    OtherComponent_nested_injection();
}

function OtherComponent_nested_injection() {
    console.log('hi');
}

function OtherComponent_onclick(target) {
    something();
    OtherComponent_click_nested_injection();
}

function OtherComponent_click_nested_injection() {
    console.log('hi');
}

function OtherComponent_onmouseover(target) {
    OtherComponent_nested_injection();
}
