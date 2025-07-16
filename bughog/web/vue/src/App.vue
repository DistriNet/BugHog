<script>
import { useDarkMode } from './composables/useDarkMode'
import { useEvalParams } from './composables/useEvalParams'
import 'vue-multiselect/dist/vue-multiselect.min.css'
import '@vueform/slider/themes/default.css'
import axios from 'axios'

import Gantt from "./components/gantt.vue"
import PocEditor from "./components/poc-editor.vue"
import SectionHeader from "./components/section-header.vue";
import Slider from '@vueform/slider'
import Tooltip from "./components/tooltip.vue";
import EvaluationStatus from './components/evaluation_status.vue';
export default {
  components: {
    Gantt,
    PocEditor,
    SectionHeader,
    Slider,
    Tooltip,
    EvaluationStatus,
  },
  setup() {
    const { darkMode } = useDarkMode()
    const { evalParams, resetEvalParams } = useEvalParams()
    return {
      darkMode,
      evalParams,
      resetEvalParams,
    }
  },
  data() {
    return {
      timer: null,
      projects: [],
      subject_availability: [],
      subject_settings: [],
      cli_options_str: "",
      previous_cli_options_list: [],
      experiments: [],
      select_all_experiments: false,
      slider: {
        state: [0, 100],
        state_range: [0, 100],
        disabled: true
      },
      server_info: {
        db_info: {
          "host": null,
          "connected": false
        },
        logs: [],
        state: {},
      },
      results: {
        nb_of_evaluations: 0,
      },
      selected: {
        experiment: null,
        subject: null,
      },
      dialog: {
        new_experiment_name: null,
        new_project_name: null
      },
      target_mech_id_input: null,
      target_mech_id: null,
      fatal_error: null,
      hide_advanced_evaluation_options: true,
      hide_advanced_subject_options: true,
      hide_logs: true,
      hide_poc_editor: true,
      system: null,
      available_domains: null,
      websocket: null,
    }
  },
  computed: {
    "missing_plot_params": function () {
      const required_params_for_plotting = ["subject_type", "subject_name", "project", "experiment_to_plot"];
      return required_params_for_plotting.filter(param => this.evalParams[param] === null);

    },
    "banner_message": function () {
      if (this.fatal_error) {
        return `A fatal error has occurred! Please, check the logs below...`
      }
      else if (this.server_info.db_info.connected) {
        return `Connected to MongoDB at ${this.server_info.db_info.host}`;
      } else {
        return `Connecting to database...`;
      }
    },
    "available_subjects": function () {
      const subject_type = this.evalParams.subject_type;
      if (this.subject_availability.length == 0) {
        return [];
      }
      if (this.evalParams.subject_type !== null) {
        const result = this.subject_availability.find(type_entry => type_entry.subject_type === subject_type);
        return result['subjects'];
      } else {
        return [];
      }
    },
  },
  watch: {
    "selected.experiment": function (val) {
      if (val !== null) {
        this.hide_poc_editor = false;
      }
    },
    "slider.state": function () {
      this.evalParams.lower_version = this.slider.state[0];
      this.evalParams.upper_version = this.slider.state[1];
      this.propagate_new_params();
    },
    "info.log": {
      function(val) {
        if (log_section.scrollHeight - log_section.scrollTop - log_section.clientHeight < 1) {
          log_section.scrollTo({ "top": log_section.scrollHeight, "behavior": "auto" });
        }
      },
      "flush": "post",
    },
    "target_mech_id_input": function (val) {
      if (val === null || val === "") {
        this.evalParams.target_mech_id = this.evalParams.experiment_to_plot;
      } else {
        this.evalParams.target_mech_id = val;
      }
      this.propagate_new_params();
    },
    "evalParams.experiment_to_plot": function (val) {
      if (this.target_mech_id_input === null || this.target_mech_id_input === "") {
        this.evalParams.target_mech_id = val;
      }
      this.propagate_new_params();
    },
    "evalParams.subject_type": {
      handler(val) {
        this.set_curr_subject_type(val)
      },
      immediate: true
    },
    "selected.subject": function (subject) {
      if (subject === null) {
        console.log("Unset subject")
        return
      }
      console.log("Set subject: " + subject["name"])
      this.evalParams.subject_name = subject["name"];
      this.slider.state_range[0] = subject["min_version"];
      this.slider.state_range[1] = subject["max_version"];
      this.slider.state = [subject["min_version"], subject["max_version"]];
      this.slider.disabled = false;
      this.propagate_new_params();
    },
    "cli_options_str": function (val) {
      if (val !== "") {
        this.evalParams.cli_options = val.trim().split(" ");
      } else {
        this.evalParams.cli_options = [];
      }
      this.propagate_new_params()
    },
    "select_all_experiments": function (val) {
      console.log("hi")
      if (this.select_all_experiments === true) {
        this.evalParams.experiments = this.experiments
          .filter(tuple => tuple[1]) // Only select enabled checkboxes
          .map(tuple => tuple[0]);;
      } else {
        this.evalParams.experiments = [];
      }
    },
  },
  created: function () {
    this.websocket = this.create_socket();
    this.get_subject_support();
    this.get_projects();
    const path = `/api/poc/domain/`;
    axios.get(path)
    .then((res) => {
      if (res.data.status === "OK") {
        this.available_domains = res.data.domains;
      }
    })
    this.timer = setInterval(() => {
      if (this.subject_availability.length == 0) {
        this.get_subject_support();
      }
      if (this.projects.length == 0 && this.evalParams.subject_type !== null) {
        this.get_projects();
      }
      if (this.system == null) {
        this.get_system_info();
      }
      this.fetch_server_info(["logs"]);
    }, 2000);
  },
  mounted: function () {
    setTimeout(function () {
      log_section.scrollTo({ "top": log_section.scrollHeight, "behavior": "auto" });
    },
      500
    );
  },
  methods: {
    create_socket() {
      const url = `/api/socket/`;
      const websocket = new WebSocket(url);
      websocket.addEventListener("open", () => {
        console.log("WebSocket opened!");
        // Get all info upon open
        this.send_with_socket({
          "get": ["all"],
        });
        // This might be a re-open after connection loss, which means we might have to propagate our params again
        if (this.evalParams.project_name !== null) {
          this.set_curr_project(this.evalParams.project_name);
        }
        this.propagate_new_params();
      });
      websocket.addEventListener("message", (e) => {
        const data = JSON.parse(e.data);
        if (data.hasOwnProperty("update")) {
          if (data.update.hasOwnProperty("plot_data")) {
            const revision_data = data.update.plot_data.revision_data;
            const version_data = data.update.plot_data.version_data;
            this.$refs.gantt.update_plot(this.evalParams.subject_name, revision_data, version_data);
            this.results.nb_of_evaluations = revision_data.outcome.length + version_data.outcome.length;
          }
          if (data.update.hasOwnProperty("experiments")) {
            this.experiments = data.update.experiments;
          }
          if (data.update.hasOwnProperty("previous_cli_options")) {
            this.previous_cli_options_list = data.update.previous_cli_options;
            console.log(this.previous_cli_options_list);
          }
          else {
            for (const variable in data.update) {
              this.server_info[variable] = data.update[variable];
            }
          }
        }
      });
      websocket.addEventListener("error", () => {
        console.log("Could not connect to backend socket.");
      });
      websocket.addEventListener("close",  () => {
        console.log("Connection to backend socket was unexpectedly closed.");
      });
      return websocket;
    },
    send_with_socket(data_in_dict) {
      if (this.websocket === null || this.websocket === undefined || this.websocket.readyState > 1) {
        console.log(`Websocket connection died, reviving...`);
        this.websocket = this.create_socket();
      } else if (this.websocket.readyState === 0) {
        console.log(`Websocket is still trying to connect... (readyState: ${this.websocket.readyState})`);
      } else {
        this.websocket.send(JSON.stringify(data_in_dict));
      }
    },
    fetch_server_info(info_types) {
      this.send_with_socket({
        "get": info_types
      });
    },
    get_projects(cb) {
      if (this.evalParams.subject_type === null) {
        console.warn('Could not get projects because the subject type is not defined.');
        return;
      }
      const path = `/api/poc/${this.evalParams.subject_type}/`;
      axios.get(path)
        .then((res) => {
          if (res.data.status == "OK") {
            this.projects = res.data.projects;
            if (cb !== undefined) {
              cb();
            }
          }
        })
        .catch((error) => {
          console.error(error);
        });
    },
    get_subject_support() {
      const path = `/api/subject/`;
      axios.get(path)
        .then((res) => {
          if (res.data.status == "OK") {
            this.subject_availability = res.data.subject_availability;
          }
        })
        .catch((error) => {
          console.error(error);
        });
    },
    get_system_info() {
      const path = `/api/system/`;
      axios.get(path)
        .then((res) => {
          if (res.data.status == "OK") {
            this.system = res.data;
            if ("cpu_count" in res.data) {
              console.log("CPU: " + Math.max(res.data["cpu_count"] - 1, 1));
              this.evalParams.nb_of_containers = Math.max(res.data["cpu_count"] - 1, 1);
            }
          }
        })
        .catch((error) => {
          console.error(error);
        });
    },
    propagate_new_params() {
      debugger;
      if (this.missing_plot_params.length === 0) {
        console.log('Propagating parameter change');
        this.send_with_socket(
          {
            "new_params": this.evalParams
          }
        );
      } else if (this.evalParams.subject_name !== null) {
        console.log('Propagating subject change');
        this.send_with_socket(
          {
            "new_subject": this.evalParams
          }
        );
      } else {
        console.log("Missing plot parameters: ", this.missing_plot_params);
      }
    },
    reset_slider() {
      this.slider.state = [0, 100];
      this.slider.state_range = [0, 100];
      this.slider.disabled = true;
    },
    project_dropdown_change(event) {
      const option = event.target.value;
      if (option == "Create new project...") {
        create_project_dialog.showModal();
      } else {
        this.set_curr_project(option)
      }
    },
    set_curr_subject_type(subject_type) {
      this.set_curr_project(null);
      this.reset_slider();
      this.selected.experiment == null;
      this.send_with_socket({
        "select_subject_type": subject_type
      })
      this.evalParams.subject_name = null;
      this.get_projects();
    },
    set_curr_project(project) {
      if (project !== null) {
        this.experiments = [];
        this.send_with_socket({
          "select_project": project
        });
      }
      this.evalParams.project_name = project;
      this.evalParams.experiments = [];
      this.select_all_experiments = false;
    },
    submit_form() {
      const path = `/api/evaluation/start/`;
      const payload = {
        ...this.evalParams,
      };
      axios.post(path, payload)
        .then((res) => {
          if (res.data.status === "NOK") {
            alert(res.data.msg);
          }
        })
        .catch((error) => {
          console.error(error);
        });
    },
    stop(forcefully) {
      const path = `/api/evaluation/stop/`;
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
    fetch_results(url) {
      return axios.put(url, JSON.stringify(this.evalParams), {
        headers: {
          'Content-Type': 'application/json',
        }
      })
    },
    create_new_experiment() {
      const url = `/api/poc/${this.evalParams.subject_type}/${this.evalParams.project_name}/`;
      axios.post(url, {'poc_name': this.dialog.new_experiment_name})
      .then((res) => {
        if (res.data.status === "OK") {
          this.dialog.new_experiment_name = null;
        } else {
          alert(res.data.msg);
        }
      })
      .catch((error) => {
        console.error('Could not create new experiment');
      });
    },
    create_new_project() {
      const url = `/api/poc/${this.evalParams.subject_type}/`;
      const new_project_name = this.dialog.new_project_name;
      axios.post(url, {'project_name': new_project_name})
      .then((res) => {
        if (res.data.status === "OK") {
          this.dialog.new_project_name = null;
          this.get_projects(() => {
            this.set_curr_project(new_project_name);
          });
        } else {
          alert(res.data.msg);
        }
      })
      .catch((error) => {
        console.error('Could not create new project', error);
      });
    },
  },
  beforeDestroy() {
    clearInterval(this.timer);
  }
}
</script>

<template>
  <div id="option-board" class="grid grid-rows-[4rem,50rem,auto,auto] grid-cols-[18rem,58rem] content-start gap-3 justify-center h-screen">

    <!-- Banner -->
    <header class="banner-page row-start-1 col-span-2">

      <!-- <p>[FRAMEWORK NAME + LOGO]</p> -->
      <p :class="{ '!font-bold !text-red-600' : fatal_error }">{{ banner_message }}</p>

      <select id="subject-type-select" class="w-64 block p-2 border border-gray-300 rounded" v-model="this.evalParams.subject_type" :disabled="!subject_availability.length" >
        <option value="" disabled>Select subject type</option>
        <option v-for="subject in subject_availability" :key="subject.subject_type" :value="subject.subject_type" >
          {{ subject.subject_type }}
        </option>
      </select>

      <label class="inline-flex items-center cursor-pointer">
        <input id="darkmode_toggle" type="checkbox" class="sr-only peer" v-model="this.darkMode">
        <div
          class="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600">
        </div>
        <span class="ms-3 text-sm font-medium text-gray-900 dark:text-gray-300">Dark mode</span>
      </label>
    </header>

    <!-- Subject settings and experiments -->
    <div class="row-start-2 row-span-1 gap-3 flex flex-col">
      <!-- Subject settings -->
      <div class="form-section">
        <section-header section="eval_range"></section-header>

        <!-- Subject --><div class="form-subsection">
    <h2 class="form-subsection-title">Subject</h2>
    <div class="flex flex-row justify-center mx-5">
      <div v-for="subject in available_subjects" :key="subject.name" class="radio-item flex-auto">
        <input type="radio" :id="subject.name" name="subject" :value="subject" v-model="selected.subject" />
        <label :for="subject.name">{{ subject.name }}</label>
      </div>
    </div>
  </div>

        <div class="form-subsection">
          <h2 class="form-subsection-title">Subject version range</h2>
          <div class="flex flex-wrap">
            <div class="w-5/6 m-auto pt-12">
              <Slider
                v-model="this.slider.state"
                :min="this.slider.state_range[0]"
                :max="this.slider.state_range[1]"
                :disabled="this.slider.disabled"
                class="slider"
              />
            </div>
            <div class="pt-5 checkbox-item">
              <input
                v-model="this.evalParams.only_release_commits"
                :true-value="false"
                :false-value="true"
                type="checkbox">
              <label>Deep search
                <tooltip tooltip="deep_search"></tooltip>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Experiments -->
      <div class="form-section flex flex-col grow h-0">
        <section-header section="experiments" class="w-1/2"></section-header>

        <select id="project_dropdown" class="mb-2" @change="project_dropdown_change" v-model="this.evalParams.project_name">
          <option disabled value="">Select a project</option>
          <option v-for="project in projects">{{ project }}</option>
          <option>Create new project...</option>
        </select>

        <div class="h-0 grow overflow-y-auto overflow-x-hidden">
          <ul class="horizontal-select">
            <li>
              <div class="bg-gray-100 dark:bg-gray-800">
                <input id="select_all_experiments" type="checkbox" class="ml-1" v-model="this.select_all_experiments">
                <label for="vue-checkbox-list" class="flex group w-full">
                  <div class="pl-0 w-full">
                    <p class="truncate w-0 grow">
                      Select all
                    </p>
                  </div>
                </label>
              </div>
            </li>
            <li v-for="tuple in experiments">
              <div>
                <input v-model="this.evalParams.experiments" type="checkbox" class="ml-1" :value="tuple[0]" :disabled="!tuple[1]">
                <label for="vue-checkbox-list" class="flex group w-full">
                  <div class="pl-0 w-full">
                    <div v-if="!tuple[1]" class="text-red-500 font-bold">
                      !
                    </div>
                    <p class="truncate w-0 grow">
                      {{ tuple[0] }}
                    </p>
                  </div>
                  <div role="button" @click="this.selected.experiment=tuple[0]" class="invisible w-content collapse group-hover:visible">
                    <v-icon name="fa-regular-edit"/>
                  </div>
                </label>
              </div>
            </li>
          </ul>
        </div>
        <div v-if="this.evalParams.project_name" role="button" class="button mt-2" onclick="create_experiment_dialog.showModal()">
          Add new experiment
        </div>
      </div>
    </div>

    <!-- Start button and results section -->
    <div class="row-start-2 col-start-2 flex flex-col h-full">
      <div v-if="this.server_info.state.is_running == true">
        <button @click="stop(false)" class="w-1/2 bg-yellow-300 dark:bg-yellow-500">Stop gracefully</button>
        <button @click="stop(true)" class="w-1/2 bg-red-400 dark:bg-red-800">Stop forcefully</button>
      </div>
      <div v-else>
        <button @click="submit_form" class="w-full bg-green-300 dark:bg-green-900">Start evaluation</button>
      </div>
      <div class="results-section mt-2 h-full flex flex-col">
        <section-header section="results" left></section-header>
        <div class="flex flex-wrap justify-between h-fit">
          <select class="w-fit h-fit" v-model="this.evalParams.experiment_to_plot">
            <option disabled value="">Select an experiment</option>
            <option v-for="experiment in this.evalParams.experiments">{{ experiment }}</option>
          </select>
          <div class="flex flex-wrap">
            <evaluation-status :server_info="this.server_info">
            </evaluation-status>
          </div>
          <div class="flex flex-wrap">
            <ul class="my-3 w-64">
              <li><b>Number of experiments:</b> {{ results.nb_of_evaluations }}</li>
            </ul>
          </div>
        </div>
        <gantt ref="gantt" :eval_params="this.evalParams"></gantt>
      </div>
    </div>

    <!-- PoC editor -->
    <div class="form-section col-span-2 row-start-3">
      <div class="flex">
        <h2 class="flex flex-initial w-1/2 form-section-title pt-2">
          Experiment editor
          <div v-if="this.selected.experiment !== null && !this.hide_poc_editor" class="px-1 font-normal">
            ({{ this.selected.experiment }})
          </div>
        </h2>
        <div class="w-full text-right">
          <button class="collapse-button" @click="this.hide_poc_editor = !this.hide_poc_editor">
            <div class="flex items-center">
              <p class="text-xl pb-1 px-1">+</p>
            </div>
          </button>
        </div>
      </div>
      <div :class="this.hide_poc_editor ? 'hidden w-full' : 'w-full'">
        <poc-editor
        :darkmode="this.darkmode"
        :available_domains="this.available_domains"
        :project="this.evalParams.project_name"
        :poc="selected.experiment"
        :subject_type="this.evalParams.subject_type"></poc-editor>
      </div>
    </div>

    <!-- Advanced subject options -->
    <!-- <div class="form-section col-span-2 row-start-4">
      <div class="flex">
        <h2 class="flex flex-initial w-1/2 form-section-title pt-2">
          Advanced subject options
        </h2>
        <div class="w-full text-right">
          <button class="collapse-button" @click="this.hide_advanced_subject_options = !this.hide_advanced_subject_options">
            <div class="flex items-center">
              <p class="text-xl pb-1 px-1">+</p>
            </div>
          </button>
        </div>
      </div>
      <div :class="this.hide_advanced_subject_options ? 'hidden w-full' : 'w-full'">
        <div>
          <label for="cli_options" class="pb-2">CLI flags</label>
          <input class="w-full dark:!text-white dark:!bg-gray-800" type="text" name="cli_options" v-model="this.cli_options_str">
        </div>
        <div>
          <div>
            <label class="pt-4 pb-2">Previously used CLI flags</label>
          </div>
          <ul class="">
            <li v-for="cli_options_str in this.previous_cli_options_list">
              <div role="button" @click="this.cli_options_str=cli_options_str" class="button my-1 !text-black !text-left !bg-white hover:!bg-gray-100 dark:!text-white dark:!bg-gray-800 dark:hover:!bg-gray-600">
                {{ cli_options_str }}
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div> -->

    <!-- Advanced evaluation options -->
    <div class="form-section h-fit col-span-2 row-start-4">
      <div class="flex">
        <h2 class="flex-initial w-1/2 form-section-title pt-2">Advanced evaluation options</h2>
        <div class="w-full text-right">
          <button class="collapse-button" @click="this.hide_advanced_evaluation_options = !this.hide_advanced_evaluation_options">
            <div class="flex items-center">
              <p class="text-xl pb-1 px-1">+</p>
            </div>
          </button>
        </div>
      </div>
      <div :class="hide_advanced_evaluation_options ? 'hidden' : ''">
        <div class="grid grid-cols-[auto,auto,auto] justify-start">
          <div class="flex flex-col">
            <div class="form-subsection">
              <section-header section="subject_rev_range"></section-header>
              <div class="p-1 w-1/2">
                <label for="lower_commit_nb">Lower commit nb</label>
                <input v-model.lazy="this.evalParams.lower_commit_nb" class="number-input w-32" type="number">
              </div>

              <div class="p-1 w-1/2">
                <label for="upper_commit_nb">Upper rev nb</label>
                <input v-model.lazy="this.evalParams.upper_commit_nb" class="number-input w-32" type="number">
              </div>
            </div>
          </div>

          <!-- Evaluation settings -->
          <div class="form-subsection w-fit eval_opts col-start-3">
            <section-header section="eval_settings"></section-header>
            <div class="form-subsection">
              <section-header section="search_strategy"></section-header>

              <div class="radio-item">
                <input v-model="this.evalParams.search_strategy" type="radio" id="bin_seq" name="search_strategy_option"
                  value="bgb_sequence">
                <label for="bgb_sequence">BGB sequence</label>
                <tooltip tooltip="bgb_sequence"></tooltip>
              </div>

              <div class="radio-item">
                <input v-model="this.evalParams.search_strategy" type="radio" id="bgb_search" name="search_strategy_option"
                  value="bgb_search">
                <label for="bgb_search">BGB search</label>
                <tooltip tooltip="bgb_search"></tooltip>
              </div>

              <div class="radio-item">
                <input v-model="this.evalParams.search_strategy" type="radio" id="comp_search" name="search_strategy_option"
                  value="comp_search">
                <label for="comp_search">Composite search</label>
                <tooltip tooltip="comp_search"></tooltip>
              </div>
              <br>

              <div class="flex items-baseline mb-1">
                <label for="sequence_limit" class="mb-0 align-middle">Sequence limit</label>
                <tooltip tooltip="sequence_limit"></tooltip>
              </div>
              <input v-model.number="this.evalParams.sequence_limit" class="input-box" type="number" min="1" max="10000">
            </div>

            <div class="form-subsection">
              <section-header section="parallel_containers"></section-header>
              <input v-model.number="this.evalParams.nb_of_containers" class="input-box" type="number" id="nb_of_containers"
                name="nb_of_containers" min="1" max="16">
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Logs -->
    <div class="results-section h-fit col-span-2 row-start-5 flex-1">
      <div class="flex">
        <h2 class="flex-initial w-1/2 form-section-title">Log</h2>
        <div class="w-full text-right">
          <button class="collapse-button" @click="this.hide_logs = !this.hide_logs">
            <div class="flex items-center">
              <p class="text-xl pb-1 px-1">+</p>
            </div>
          </button>
        </div>
      </div>
      <div :class="hide_logs ? 'hidden' : ''">
        <div id="log_section" class="mt-3 h-96 bg-white overflow-y-scroll flex flex-col dark:bg-dark-3">
          <ul>
            <li v-for="entry in this.server_info.logs">
              <p>{{ entry }}</p>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>

  <!-- Create file dialog -->
  <dialog id="create_experiment_dialog" class="dialog">
    <form method="dialog" @submit="create_new_experiment">
      <p>
        <label>
          <div class="pb-5">
            Enter new experiment name:
          </div>
          <input type="text" v-model="dialog.new_experiment_name" class="input-box" required autocomplete="off" />
        </label>
      </p>
      <div class="flex pt-3">
        <input type="submit" value="Create file" class="button m-2 w-full">
        <input type="button" value="Cancel" class="button m-2" onclick="create_experiment_dialog.close()">
      </div>
    </form>
  </dialog>

  <!-- Create project dialog -->
  <dialog id="create_project_dialog" class="dialog">
    <form method="dialog" @submit="create_new_project">
      <p>
        <label>
          <div class="pb-5">
            Enter new project name:
          </div>
          <input type="text" v-model="dialog.new_project_name" class="input-box" required autocomplete="off" />
        </label>
      </p>
      <div class="flex pt-3">
        <input type="submit" value="Create project" class="button m-2 w-full">
        <input type="button" value="Cancel" class="button m-2" onclick="create_project_dialog.close()">
      </div>
    </form>
  </dialog>
</template>

