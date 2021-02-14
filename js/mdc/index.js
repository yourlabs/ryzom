import './index.sass'

import {autoInit} from "material-components-web"
import {MDCTopAppBar} from "@material/top-app-bar"
import {MDCDrawer} from "@material/drawer"

const drawer = MDCDrawer.attachTo(document.querySelector('.mdc-drawer'))
const topAppBar = MDCTopAppBar.attachTo(document.getElementById('app-bar'))
topAppBar.setScrollTarget(document.getElementById('main-content'))
topAppBar.listen('MDCTopAppBar:nav', () => {
  drawer.open = !drawer.open
})

autoInit()
