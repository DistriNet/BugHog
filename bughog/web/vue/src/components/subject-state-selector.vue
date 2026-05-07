<script setup>
import { computed } from 'vue';
import Slider from '@vueform/slider';

const props = defineProps({
  modelValue: {
    type: [Number, Array],
    required: true
  },
  mode: {
    type: String,
    default: 'version',
    validator: (value) => ['version', 'commit'].includes(value)
  },
  min: {
    type: Number,
    default: 1
  },
  max: {
    type: Number,
    default: 100
  },
  disabled: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:modelValue']);

const internalValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
});

const isSliderMode = computed(() => {
  return props.mode === 'version' && (props.max - props.min) <= 200;
});
</script>

<template>
  <div class="w-full">
    <div class="flex justify-between items-center mb-2">
      <label class="block text-sm font-bold text-gray-700 dark:text-gray-200">
        {{ mode === 'version' ? 'Subject Version' : 'Commit Number' }}
      </label>
      <span class="text-xs text-gray-500 dark:text-gray-400">
        Range: {{ min }} - {{ max }}
      </span>
    </div>

    <div v-if="isSliderMode" class="px-2 py-4">
      <Slider
        v-model="internalValue"
        :min="min"
        :max="max"
        :disabled="disabled"
        :tooltips="true"
        class="slider-blue"
      />
    </div>

    <div v-else class="relative">
      <div class="flex items-center">
        <button
          @click="internalValue = internalValue != null ? Math.max(min, internalValue - 1) : min"
          class="px-3 py-2 bg-gray-200 hover:bg-gray-300 rounded-l border border-r-0 border-gray-300 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          :disabled="disabled || (internalValue != null && internalValue <= min)"
        >
          -
        </button>
        <input
          v-model.number="internalValue"
          type="number"
          :min="min"
          :max="max"
          :disabled="disabled"
          class="w-full text-center p-2 border-t border-b border-gray-300 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
        />
        <button
          @click="internalValue = internalValue != null ? Math.min(max, internalValue + 1) : max"
          class="px-3 py-2 bg-gray-200 hover:bg-gray-300 rounded-r border border-l-0 border-gray-300 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          :disabled="disabled || (internalValue != null && internalValue >= max)"
        >
          +
        </button>
      </div>

      <div v-if="mode === 'commit'" class="flex justify-between mt-1">
        <button @click="internalValue = min" class="no-style text-xs text-blue-500 hover:underline">Min</button>
        <button @click="internalValue = max" class="no-style text-xs text-blue-500 hover:underline">Max</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.slider-blue {
  --slider-connect-bg: #3b82f6;
  --slider-tooltip-bg: #3b82f6;
  --slider-handle-ring-color: #3b82f630;
}
</style>
