import { ref, watchEffect } from 'vue'

const darkMode = ref(
  localStorage.theme === 'dark' ||
  (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)
)

watchEffect(() => {
  document.documentElement.classList.toggle('dark', darkMode.value)
  localStorage.theme = darkMode.value ? 'dark' : 'light'
})

export function useDarkMode() {
  return { darkMode }
}
