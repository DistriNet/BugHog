import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import 'flowbite'
import 'axios'

import { OhVueIcon, addIcons } from "oh-vue-icons";
import { MdInfooutline } from "oh-vue-icons/icons";

addIcons(MdInfooutline);
const app = createApp(App);
app.component("v-icon", OhVueIcon).mount('#app')
