class MyComponent extends HTMLElement {
    connectedCallback() {
        this.connected = true;
    }
}

window.customElements.define("foo-bar", MyComponent);
function OtherComponent_on_form_submit() {
    console.log('hi!');
}
