<script setup>
import { computed } from 'vue';
import { useDarkMode } from '../composables/useDarkMode';

const props = defineProps({
  fatal_error: {
    type: Boolean,
    default: false
  },
  banner_message: {
    type: String,
    default: 'Welcome'
  },
  subject_availability: {
    type: Object,
    required: true,
    default: () => ({
      is_empty: () => false,
      get_available_subject_types: () => []
    })
  },
  modelValue: {
    type: Object,
    default: () => ({ subject_type: '' })
  }
});

const emit = defineEmits(['update:modelValue', 'params-changed', 'toggle-dark-mode']);


const evalParams = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
});

const { darkMode } = useDarkMode();

const propagate_new_params = () => {
  emit('params-changed', evalParams.value);
};

const toggleDarkMode = () => {
  emit('toggle-dark-mode', darkMode.value);
};
</script>

<template>
  <header class="banner-page row-start-1 col-span-2">
    <!-- <p>[FRAMEWORK NAME + LOGO]</p> -->
    <p :class="{ '!font-bold !text-red-600': fatal_error }">
      {{ banner_message }}
    </p>

    <select
      id="subject-type-select"
      class="w-64"
      v-model="evalParams.subject_type"
      :disabled="subject_availability?.is_empty ? subject_availability.is_empty() : false"
      @change="propagate_new_params"
    >
      <option value="" disabled>Select subject type</option>
      <option
        v-for="subject_type in (subject_availability?.get_available_subject_types ? subject_availability.get_available_subject_types() : [])"
        :key="subject_type"
        :value="subject_type"
      >
        {{ subject_type }}
      </option>
    </select>

    <label class="inline-flex items-center cursor-pointer">
      <input
        id="darkmode_toggle"
        type="checkbox"
        class="sr-only peer"
        v-model="darkMode"
        @change="toggleDarkMode"
      >
      <div class="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600">
      </div>
      <span class="ms-3 text-sm font-medium text-gray-900 dark:text-gray-300">Dark mode</span>
    </label>
  </header>
</template>
