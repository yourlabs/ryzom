class Test extends HTMLElement {
    constructor() {
        this.something = 'test';
    }
    change(event) {
        console.log(event);
    }
}
