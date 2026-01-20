import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import 'flowbite'
import 'axios'
import Vue3Toastify from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import { OhVueIcon, addIcons } from "oh-vue-icons";
import { MdInfooutline, FaRegularEdit, FaLink, FaPlus } from "oh-vue-icons/icons";

addIcons(MdInfooutline, FaRegularEdit, FaLink, FaPlus);
const app = createApp(App);
app.use(Vue3Toastify, {autoclose: 5000, position: 'top-right'});
app.component("v-icon", OhVueIcon).mount('#app')
