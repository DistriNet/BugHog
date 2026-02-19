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

const emit = defineEmits(['start']);

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
  <div class="w-full">
    <button
      @click="!isRunning && $emit('start')"
      :disabled="isRunning || !canStart"
      :class="buttonClass"
      class="w-full text-black dark:text-white font-bold py-2 px-4 rounded transition-colors"
    >
      {{ buttonText }}
    </button>
  </div>
</template>
