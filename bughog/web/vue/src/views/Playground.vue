<script>
import '@vueform/slider/themes/default.css';
import { useDebounceFn } from '@vueuse/core';
import axios from 'axios';
import { toast } from 'vue3-toastify';
import { useDarkMode } from '../composables/useDarkMode';
import { useServerInfo } from '../composables/useServerInfo';
import { useSubjectAvailability } from '../composables/useSubjectAvailability';
import { useWebSocket } from '../composables/useWebSocket';

import ExperimentControls from '../components/experiment-controls.vue';
import JsonTree from '../components/json-tree.vue';
import PocEditor from "../components/poc-editor.vue";
import SectionHeader from "../components/section-header.vue";
import SubjectStateSelector from "../components/subject-state-selector.vue";
import Tooltip from "../components/tooltip.vue";

export default {
  components: {
    ExperimentControls,
    JsonTree,
    PocEditor,
    SectionHeader,
    SubjectStateSelector,
    Tooltip,
  },
  props: {
    subject_type: { type: String, required: true },
    subject_name: { type: String, required: true },
    project_name: { type: String, required: true },
    poc_name: { type: String, required: true },
  },
  setup() {
    const { darkMode } = useDarkMode()
    const { serverInfo, updateServerInfo, bannerMessage } = useServerInfo();
    const { subject_availability } = useSubjectAvailability();
    const socketHandlers = {
      onOpen: () => {},
      onMessage: () => {}
    };
    const { send: sendWithSocket, isConnected } = useWebSocket({
      autoConnect: true,
      onOpen: (ws) => {
        socketHandlers.onOpen(ws);
      },
      onMessage: (data) => {
        socketHandlers.onMessage(data);
      }
    });
    return {
      darkMode,
      subject_availability,

      server_info: serverInfo,
      updateServerInfo,

      sendWithSocket,
      isConnected,

      registerSocketHandlers: (handlers) => {
        socketHandlers.onOpen = handlers.onOpen;
        socketHandlers.onMessage = handlers.onMessage;
      }
    }
  },
  data() {
    return {
      commit_nb: null,
      experiment_result: null,
    }
  },
  computed: {
    experiment_parameters() {
      return {
        subject_type: this.subject_type,
        subject_name: this.subject_name,
        project_name: this.project_name,
        poc_name: this.poc_name,
        commit_nb: this.commit_nb,
      };
    },
    valid_subject_names() {
      return this.subject_availability.get_available_subject_names_for_type(this.subject_type) || [];
    },
    min_commit_nb() {
      const subject = this.subject_availability.get_subject_by_name(this.subject_type, this.subject_name);
      return subject["min_commit"];
    },
    max_commit_nb() {
      const subject = this.subject_availability.get_subject_by_name(this.subject_type, this.subject_name);
      return subject["max_commit"];
    },
  },
  watch: {
    // Watch for URL changes (e.g. when switching Subject Name).
    '$route.params': {
      handler: 'load_page_data',
      immediate: true
    },
    'commit_nb': function() {
      this.request_experiment_result();
    },
    'subject_name': function() {
      this.request_experiment_result();
    }
  },
  created() {
    this.registerSocketHandlers({
      onOpen: () => {
      },
      onMessage: (data) => {
        this.onSocketMessage(data);
      }
    });
    this.request_experiment_result = useDebounceFn(() => {
      console.log('<- Propagating parameter change ->');
      const experiment_params = JSON.parse(JSON.stringify(this.experiment_parameters));
      this.sendWithSocket({'request_experiment_result': experiment_params});
    }, 50);
  },
  methods: {
    onSocketMessage(data) {
      if (data.hasOwnProperty("update")) {
        if (data.update.hasOwnProperty("experiment_result")) {
          this.experiment_result = data.update.experiment_result;
        } else {
          this.updateServerInfo(data.update);
        }
      }
    },
    switch_subject(new_subject_name) {
      this.$router.push({
        name: 'playground',
        params: {
          subject_type: this.subject_type,
          subject_name: new_subject_name,
          project_name: this.project_name,
          poc_name: this.poc_name
        }
      });
    },
    load_page_data() {
      console.log(`Loading playground for ${this.subject_name} / ${this.poc_name}`);
    },

    // Experiment execution
    start_experiment() {
      const path = `/api/experiment/start/`;
      axios.post(path, this.experiment_parameters)
        .then((res) => {
          if (res.data.status === "NOK") {
            toast.error(res.data.msg, {
              position: toast.POSITION.TOP_RIGHT
            });
          }
        })
        .catch((error) => {
          console.error(error);
        });
    },
    stop(forcefully) {
      const path = `/api/experiment/stop/`;
      const data = {};
      if (forcefully) {
        data["forcefully"] = true;
      }
      axios.post(path, data)
        .then((res) => {

        })
        .catch((error) => {
          console.error(error);
        });
    },
    get_result_class(outcome) {
      const map = {
        'pass': 'bg-green-100 text-green-800 border-green-300',
        'fail': 'bg-red-100 text-red-800 border-red-300',
        'timeout': 'bg-orange-100 text-orange-800 border-orange-300'
      };
      return map[outcome] || 'bg-gray-100';
    }
  }
}
</script>

<template>
  <div class="pt-2 w-[70vw] mx-auto">
    <div id="option-board" class="grid grid-rows-[auto_auto] grid-cols-1 content-start gap-3">

      <!-- Subject selection, results panel and experiment control -->
      <div class="grid grid-rows-1 grid-cols-[320px_1fr] gap-2">

        <!-- Subject selection and experiment start control -->
        <div class="grid grid-rows-[1fr_auto_auto_auto] gap-2">

          <div class="bg-white dark:bg-gray-800 p-4 rounded shadow-sm">
            <section-header section="eval_range"></section-header>

            <div class="form-subsection mt-2">
              <div v-if="valid_subject_names.length > 0" class="flex flex-col space-y-2">
                <div v-for="name in valid_subject_names" :key="name" class="flex items-center">
                  <input
                    type="radio"
                    :id="name"
                    :value="name"
                    :checked="name === subject_name"
                    @change="switch_subject(name)"
                    class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 focus:ring-blue-500"
                  />
                  <label :for="name" class="ms-2 text-sm font-medium cursor-pointer">
                    {{ name }}
                  </label>
                </div>
              </div>
              <div v-else class="text-sm italic text-gray-500">
                Loading subjects...
              </div>
            </div>
          </div>

          <div class="bg-white dark:bg-gray-800 p-4 rounded shadow-sm flex-1 flex flex-col">
            <section-header section="eval_range"></section-header>

            <div class="mt-4 space-y-4">
              <div class="text-sm">
                <p><strong>Project:</strong> {{ project_name }}</p>
                <p><strong>PoC:</strong> {{ poc_name }}</p>
              </div>

              <subject-state-selector
                v-model="this.commit_nb"
                mode="commit"
                :min="this.min_commit_nb"
                :max="this.max_commit_nb"
                class="mt-4"
              ></subject-state-selector>
            </div>
          </div>

          <!-- Experiment control -->
          <ExperimentControls
            :is-running="server_info.state.is_running === true"
            :hasResult="experiment_result !== null"
            :can-start="true"
            @start="start_experiment"
            @stop-gracefully="stop(false)"
            @stop-forcefully="stop(true)"
          />

          <!-- Experiment meta-data -->
          <div class="flex flex-col border rounded-md p-4 bg-white dark:bg-gray-800">
            <h3 class="font-bold mb-4 text-lg border-b pb-2">Experiment meta-data</h3>
            <!-- Row 1: Executable Version -->
            <div class="flex justify-between py-2 border-b">
              <span class="font-medium text-xs text-gray-700 dark:text-gray-300">Executable version</span>
              <span v-if="experiment_result?.executable_version" class="font-mono text-xs text-gray-600 dark:text-gray-400">
                {{ experiment_result.executable_version }}
              </span>
              <span v-else class="font-mono text-xs text-gray-600 dark:text-gray-400">-</span>
            </div>
            <!-- Row 2: Commit ID -->
            <div class="flex justify-between py-2 border-b">
              <span class="font-medium text-xs text-gray-700 dark:text-gray-300">Commit id</span>
              <span v-if="experiment_result?.state.commit_id" class="font-mono text-xs text-gray-600 dark:text-gray-400 truncate max-w-[12rem]" :title="experiment_result.state.commit_id">
                {{ experiment_result.state.commit_id }}
              </span>
              <span v-else class="font-mono text-xs text-gray-600 dark:text-gray-400">-</span>
            </div>
            <!-- Row 3: Clean -->
            <div class="flex justify-between py-2 border-b last:border-0">
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
          <div class="flex flex-col min-h-0 h-full border rounded-md p-4 bg-white dark:bg-gray-800 overflow-y-auto min-w-64 max-w-96">
            <h3 class="font-bold mb-4 text-lg border-b pb-2">Variables</h3>

            <div v-if="experiment_result?.result_variables">
              <div
                v-for="([key, value], index) in experiment_result?.result_variables"
                :key="index"
                class="flex justify-between py-2 border-b last:border-0 px-2"
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
          <div class="flex-1 gap-4 min-h-0 overflow-auto border rounded-md p-4 bg-white dark:bg-gray-800 h-[700px]" >
              <h3 class="font-bold mb-4 text-lg border-b pb-2">Raw data</h3>
              <json-tree v-if="experiment_result?.raw_results" :data="experiment_result.raw_results" :initial-expanded="true"></json-tree>
              <div v-else class="text-gray-500 italic">No raw data</div>
          </div>
        </div>
      </div>

      <!-- PoC Editor -->
      <div class="bg-white dark:bg-gray-800 p-4 rounded shadow-sm flex-shrink-0 col-span-full">
          <div>
            <poc-editor
              :darkMode="this.darkMode"
              :project="this.project_name"
              :poc="this.poc_name"
              :subject_type="this.subject_type"
              :available_domains="['leak.test', 'b.test', 'a.test', 'sub.a.test']"
            ></poc-editor>
          </div>
        </div>
    </div>
  </div>
</template>
