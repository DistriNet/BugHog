import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

import './style.css'
import 'flowbite'

import Vue3Toastify from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

import { OhVueIcon, addIcons } from "oh-vue-icons";
import { MdInfooutline, FaRegularEdit, FaLink, FaPlus } from "oh-vue-icons/icons";

addIcons(MdInfooutline, FaRegularEdit, FaLink, FaPlus);

const app = createApp(App);
app.use(router);
app.use(Vue3Toastify, {autoclose: 5000, position: 'top-right'});
app.component("v-icon", OhVueIcon);
app.mount('#app')
