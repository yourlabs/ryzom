import './index.sass'

import {autoInit} from "material-components-web"
import {MDCTopAppBar} from "@material/top-app-bar"
import {MDCDrawer} from "@material/drawer"

const drawer = MDCDrawer.attachTo(document.querySelector('.mdc-drawer'))
const topAppBar = MDCTopAppBar.attachTo(document.getElementById('app-bar'))
const listEl = document.querySelector('.mdc-drawer .mdc-list');
const mainContentEl = document.querySelector('.main-content');

topAppBar.setScrollTarget(document.getElementById('main-content'))
topAppBar.listen('MDCTopAppBar:nav', () => {
  drawer.open = !drawer.open
})

function contentFocus() {
  let focusEl = mainContentEl.querySelector('input, button');
  if (focusEl) {
    focusEl.focus();
  }
}

listEl.addEventListener('click', (event) => {
  contentFocus();
});

document.body.addEventListener('MDCDrawer:closed', () => {
  contentFocus();
});

autoInit()
