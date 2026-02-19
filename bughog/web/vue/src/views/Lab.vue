<script setup>
import '@vueform/slider/themes/default.css';
import { useDebounceFn } from '@vueuse/core';
import axios from 'axios';
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { toast } from 'vue3-toastify';

import ExperimentControls from '../components/experiment-controls.vue';
import JsonTree from '../components/json-tree.vue';
import PocEditor from "../components/poc-editor.vue";
import SectionHeader from "../components/section-header.vue";
import SubjectStateSelector from "../components/subject-state-selector.vue";

import { useDarkMode } from '../composables/useDarkMode';
import { useServerInfo } from '../composables/useServerInfo';
import { useSubjectAvailability } from '../composables/useSubjectAvailability';
import { useWebSocket } from '../composables/useWebSocket';

const props = defineProps({
  subject_type: { type: String, required: true },
  subject_name: { type: String, required: true },
  project_name: { type: String, required: true },
  poc_name: { type: String, required: true },
});

const route = useRoute();
const router = useRouter();

const { darkMode } = useDarkMode();
const { serverInfo, updateServerInfo } = useServerInfo();
const { subject_availability } = useSubjectAvailability();

const commit_nb = ref(null);
const experiment_result = ref(null);

// Computed
const experiment_parameters = computed(() => ({
  subject_type: props.subject_type,
  subject_name: props.subject_name,
  project_name: props.project_name,
  poc_name: props.poc_name,
  commit_nb: commit_nb.value,
}));

const valid_subject_names = computed(() => {
  return subject_availability.get_available_subject_names_for_type(props.subject_type) || [];
});

const min_commit_nb = computed(() => {
  const subject = subject_availability.get_subject_by_name(props.subject_type, props.subject_name);
  return subject?.min_commit;
});

const max_commit_nb = computed(() => {
  const subject = subject_availability.get_subject_by_name(props.subject_type, props.subject_name);
  return subject?.max_commit;
});

// Socket logic
const onSocketMessage = (data) => {
  if (data.hasOwnProperty("update")) {
    if (data.update.hasOwnProperty("experiment_result")) {
      experiment_result.value = data.update.experiment_result;
    } else {
      updateServerInfo(data.update);
    }
  }
};

const { send: sendWithSocket } = useWebSocket({
  autoConnect: true,
  onMessage: onSocketMessage
});

const request_experiment_result = useDebounceFn(() => {
  console.log('<- Propagating parameter change ->');
  sendWithSocket({ request_experiment_result: JSON.parse(JSON.stringify(experiment_parameters.value)) });
}, 50);

// Watchers
watch(() => route.params, () => {
  console.log(`Loading lab for ${props.subject_name} / ${props.poc_name}`);
}, { immediate: true });

watch([commit_nb, () => props.subject_name], () => {
  request_experiment_result();
});

// Methods
const switch_subject = (new_subject_name) => {
  router.push({
    name: 'lab',
    params: {
      ...props,
      subject_name: new_subject_name,
    }
  });
};

const start_experiment = () => {
  const path = `/api/experiment/start/`;
  axios.post(path, experiment_parameters.value)
    .then((res) => {
      if (res.data.status === "NOK") {
        toast.error(res.data.msg, { position: toast.POSITION.TOP_RIGHT });
      }
    })
    .catch(console.error);
};

const stop = (forcefully) => {
  const path = `/api/experiment/stop/`;
  const data = forcefully ? { forcefully: true } : {};
  axios.post(path, data).catch(console.error);
};
</script>

<template>
  <div class="pt-2 w-[85vw] mx-auto">
    <div id="option-board" class="grid grid-rows-[auto_auto] grid-cols-1 content-start gap-3">

      <!-- Subject selection, results panel and experiment control -->
      <div class="grid grid-rows-1 grid-cols-[320px_1fr] gap-2">

        <!-- Subject selection and experiment control -->
        <div class="grid grid-rows-[auto_auto_auto_1fr] gap-3">

          <div class="form-section">
            <h2 class="form-section-title pb-4">Experiment details</h2>
            <div class="text-sm">
              <p><strong>Project:</strong> {{ project_name }}</p>
              <p><strong>PoC:</strong> {{ poc_name }}</p>
            </div>
          </div>

          <div class="form-section">
            <h2 class="form-section-title pb-4">Subject selection</h2>

            <div v-if="valid_subject_names.length > 0" class="flex flex-col">
              <div v-for="name in valid_subject_names" :key="name" class="radio-item">
                <input
                  type="radio"
                  :id="name"
                  :value="name"
                  :checked="name === subject_name"
                  @change="switch_subject(name)"
                />
                <label :for="name">
                  {{ name }}
                </label>
              </div>
            </div>
            <div v-else class="text-sm italic text-gray-500">
              Loading subjects...
            </div>
            <subject-state-selector
              v-model="commit_nb"
              mode="commit"
              :min="min_commit_nb"
              :max="max_commit_nb"
              class="mt-4"
            ></subject-state-selector>
          </div>

          <!-- Experiment control -->
          <div class="form-section">
            <ExperimentControls
              :is-running="serverInfo.state.is_running === true"
              :hasResult="experiment_result !== null"
              :can-start="true"
              @start="start_experiment"
              @stop-gracefully="stop(false)"
              @stop-forcefully="stop(true)"
            />
          </div>

          <!-- Experiment meta-data -->
          <div class="form-section flex flex-col">
            <h2 class="form-section-title">Experiment meta-data</h2>
            <!-- Row 1: Executable Version -->
            <div class="flex justify-between py-2 border-b dark:border-gray-700">
              <span class="font-medium text-xs text-gray-700 dark:text-gray-300">Executable version</span>
              <span v-if="experiment_result?.executable_version" class="font-mono text-xs text-gray-600 dark:text-gray-400">
                {{ experiment_result.executable_version }}
              </span>
              <span v-else class="font-mono text-xs text-gray-600 dark:text-gray-400">-</span>
            </div>
            <!-- Row 2: Commit ID -->
            <div class="flex justify-between py-2 border-b dark:border-gray-700">
              <span class="font-medium text-xs text-gray-700 dark:text-gray-300">Commit id</span>
              <span v-if="experiment_result?.state.commit_id" class="font-mono text-xs text-gray-600 dark:text-gray-400 truncate max-w-[12rem]" :title="experiment_result.state.commit_id">
                {{ experiment_result.state.commit_id }}
              </span>
              <span v-else class="font-mono text-xs text-gray-600 dark:text-gray-400">-</span>
            </div>
            <!-- Row 3: Clean -->
            <div class="flex justify-between py-2 border-b dark:border-gray-700 last:border-0">
              <span class="font-medium text-xs text-gray-700 dark:text-gray-300">Clean</span>
              <span
                v-if="experiment_result?.is_dirty !== undefined"
                class="font-mono font-bold text-xs"
                :class="experiment_result.is_dirty ? 'text-red-600' : 'text-green-600'"
              >
                {{ experiment_result.is_dirty ? "no" : "yes" }}
              </span>
              <span v-else class="font-mono text-xs text-gray-600 dark:text-gray-400">-</span>
            </div>
          </div>
        </div>

        <!-- Results -->
        <div class="grid grid-cols-[auto_1fr] gap-2">

          <!-- BugHog variables -->
          <div class="results-section flex flex-col min-h-0 h-full overflow-y-auto min-w-64 max-w-96">
            <h2 class="form-section-title border-b pb-2 dark:border-gray-700">Variables</h2>

            <div v-if="experiment_result?.result_variables">
              <div
                v-for="([key, value], index) in experiment_result?.result_variables"
                :key="index"
                class="flex justify-between py-2 border-b last:border-0 px-2 dark:border-gray-700"
              >
                <span class="font-medium text-gray-700 dark:text-gray-300">{{ key }}</span>
                <span
                  class="font-mono"
                  :class="{
                    'text-green-600 font-bold': key === 'reproduced' && value === 'OK',
                    'text-red-600 font-bold': key === 'reproduced' && value !== 'OK',
                    'text-gray-600 dark:text-gray-400': key !== 'reproduced'
                  }"
                >
                  {{ value }}
                </span>
              </div>
            </div>
            <div v-else class="text-gray-500 italic">No variables</div>
          </div>

          <!-- BugHog raw data -->
          <div class="results-section flex-1 gap-4 min-h-0 overflow-auto h-[700px]" >
              <h2 class="form-section-title border-b pb-2 dark:border-gray-700">Raw data</h2>
              <json-tree v-if="experiment_result?.raw_results" :data="experiment_result.raw_results" :initial-expanded="true"></json-tree>
              <div v-else class="text-gray-500 italic">No raw data</div>
          </div>
        </div>
      </div>

      <!-- PoC Editor -->
      <div class="form-section flex-shrink-0 col-span-full">
          <div>
            <poc-editor
              :darkMode="darkMode"
              :project="project_name"
              :poc="poc_name"
              :subject_type="subject_type"
              :available_domains="['leak.test', 'b.test', 'a.test', 'sub.a.test']"
            ></poc-editor>
          </div>
        </div>
    </div>
  </div>
</template>
