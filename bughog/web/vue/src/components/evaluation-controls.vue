<script setup>

const props = defineProps({
  isRunning: {
    type: Boolean,
    required: true
  },
  canStart: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(['start', 'stop-gracefully', 'stop-forcefully']);

</script>

<template>
  <div class="flex flex-col w-full">
    <div v-if="isRunning" class="flex gap-2 w-full">
      <button
        @click="$emit('stop-gracefully')"
        class="flex-1 bg-yellow-300 hover:bg-yellow-400 text-black font-bold py-2 px-4 rounded dark:bg-yellow-600 dark:text-white transition-colors"
      >
        Stop gracefully
      </button>
      <button
        @click="$emit('stop-forcefully')"
        class="flex-1 bg-red-400 hover:bg-red-500 text-white font-bold py-2 px-4 rounded dark:bg-red-800 transition-colors"
      >
        Stop forcefully
      </button>
    </div>

    <div v-else class="w-full">
      <button
        @click="$emit('start')"
        :disabled="!canStart"
        :class="canStart
          ? 'bg-green-300 hover:bg-green-400 dark:bg-green-700 dark:hover:bg-green-600 cursor-pointer'
          : 'bg-gray-300 dark:bg-gray-700 cursor-not-allowed text-gray-500'"
        class="w-full text-black dark:text-white font-bold py-2 px-4 rounded transition-colors"
      >
        Start evaluation
      </button>
    </div>
  </div>
</template>
