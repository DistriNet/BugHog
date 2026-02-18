<template>
  <div class="font-mono text-sm leading-6 min-w-max">
    <!-- Primitive Value -->
    <div v-if="!isObject && !isArray">
      <div class="flex items-start hover:bg-gray-50 dark:hover:bg-gray-800/50 rounded px-1">
        <span v-if="objectKey !== null" class="text-purple-600 dark:text-purple-400 mr-2">"{{ objectKey }}":</span>
        <span :class="valueClass">{{ formatValue(data) }}</span>
        <span v-if="!isLast" class="text-gray-400 ml-0.5">,</span>
      </div>
    </div>

    <!-- Object or Array -->
    <div v-else>
      <!-- Opening Line -->
      <div
        @click="toggle"
        class="flex items-center cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 rounded px-1 select-none group"
      >
        <!-- Toggler arrow -->
        <span
          class="text-gray-400 dark:text-gray-500 w-4 mr-1 transition-transform duration-200 inline-block text-center"
          :class="{ 'rotate-90': expanded }"
        >▶</span>

        <!-- Key (if exists) -->
        <span v-if="objectKey !== null" class="text-purple-600 dark:text-purple-400 mr-2">"{{ objectKey }}":</span>

        <!-- Open Bracket/Brace -->
        <span class="text-gray-600 dark:text-gray-300 font-bold">{{ isArray ? '[' : '{' }}</span>

        <!-- Collapsed state preview -->
        <span v-if="!expanded" class="flex items-center text-gray-400 ml-2">
          <span class="text-xs italic">{{ itemCount }} items</span>
          <span class="ml-2 text-gray-600 dark:text-gray-300 font-bold">{{ isArray ? ']' : '}' }}</span>
          <span v-if="!isLast" class="text-gray-400 ml-0.5">,</span>
        </span>
      </div>

      <!-- Expanded Content -->
      <div v-if="expanded" class="ml-2 pl-4 border-l border-gray-200 dark:border-gray-700">
        <template v-if="isArray">
          <json-tree
            v-for="(value, index) in data"
            :key="index"
            :data="value"
            :object-key="null"
            :depth="depth + 1"
            :is-last="index === data.length - 1"
            :initial-expanded="false"
          />
        </template>
        <template v-else>
          <json-tree
            v-for="(value, key, index) in data"
            :key="key"
            :data="value"
            :object-key="key"
            :depth="depth + 1"
            :is-last="index === Object.keys(data).length - 1"
            :initial-expanded="false"
          />
        </template>
      </div>

      <!-- Closing Bracket/Brace (only when expanded) -->
      <!-- Added padding-left to align with the start of the opening line (ignoring the arrow) -->
      <div v-if="expanded" class="hover:bg-gray-50 dark:hover:bg-gray-800/50 rounded px-1 flex items-center">
        <!-- Spacer to match arrow width (w-4) + margin (mr-1) -->
        <span class="w-4 mr-1 inline-block"></span>

        <span class="text-gray-600 dark:text-gray-300 font-bold">{{ isArray ? ']' : '}' }}</span>
        <span v-if="!isLast" class="text-gray-400 ml-0.5">,</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'JsonTree',
  props: {
    data: { required: true },
    objectKey: { type: [String, Number], default: null },
    depth: { type: Number, default: 0 },
    isLast: { type: Boolean, default: true },
    initialExpanded: { type: Boolean, default: false }
  },
  data() {
    return {
      expanded: this.initialExpanded || (this.depth < 1 && this.objectKey === null)
    }
  },
  computed: {
    isObject() {
      return this.data && typeof this.data === 'object' && !Array.isArray(this.data);
    },
    isArray() {
      return Array.isArray(this.data);
    },
    itemCount() {
      if (this.isArray) return this.data.length;
      if (this.isObject) return Object.keys(this.data).length;
      return 0;
    },
    valueClass() {
      if (typeof this.data === 'string') return 'text-green-600 dark:text-green-400 font-medium whitespace-nowrap';
      if (typeof this.data === 'number') return 'text-blue-600 dark:text-blue-400 font-medium';
      if (typeof this.data === 'boolean') return 'text-orange-600 dark:text-orange-400 font-bold';
      if (this.data === null) return 'text-red-500 dark:text-red-400 italic';
      return 'text-gray-500';
    }
  },
  methods: {
    toggle() {
      this.expanded = !this.expanded;
    },
    formatValue(val) {
      if (typeof val === 'string') return `"${val}"`;
      if (val === null) return 'null';
      return val;
    }
  }
}
</script>
