<script setup>
import { computed } from 'vue';

const props = defineProps({
  isRunning: {
    type: Boolean,
    required: true
  },
  hasResult: {
    type: Boolean,
    default: false
  },
  canStart: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(['start', 'clear']);

const buttonText = computed(() => {
  if (props.isRunning) {
    return 'Running experiment...';
  }
  return props.hasResult ? 'Rerun experiment' : 'Run experiment';
});

const buttonClass = computed(() => {
  if (props.isRunning) {
    return 'bg-blue-300 dark:bg-blue-800 cursor-not-allowed text-gray-700 dark:text-gray-300';
  }
  if (!props.canStart) {
    return 'bg-gray-300 dark:bg-gray-700 cursor-not-allowed text-gray-500';
  }
  return 'bg-green-300 hover:bg-green-400 dark:bg-green-700 dark:hover:bg-green-600';
});
</script>

<template>
  <div class="w-full flex gap-2">
    <button
      @click="!isRunning && $emit('start')"
      :disabled="isRunning || !canStart"
      :class="buttonClass"
      class="flex-1 text-black dark:text-white font-bold py-2 px-4 rounded transition-colors"
    >
      {{ buttonText }}
    </button>
    <button
      v-if="hasResult && !isRunning"
      @click="$emit('clear')"
      title="Clear result"
      class="py-2 px-3 rounded bg-red-100 hover:bg-red-200 dark:bg-red-900 dark:hover:bg-red-800 text-red-600 dark:text-red-400 transition-colors"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="3 6 5 6 21 6"/>
        <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
        <path d="M10 11v6M14 11v6"/>
        <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
      </svg>
    </button>
  </div>
</template>
