class MyComponent extends HTMLElement {
    connectedCallback() {
        this.connected = true;
    }
}

window.customElements.define("foo-bar", MyComponent);