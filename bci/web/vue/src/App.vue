<style src="vue-multiselect/dist/vue-multiselect.min.css"></style>
<style src="@vueform/slider/themes/default.css"></style>
<script>
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
  data() {
    return {
      timer: null,
      projects: [],
      browsers: [],
      browser_settings: [],
      db_collection_suffix: "",
      tests: [],
      curr_options: {
        min_browser_version: 0,
        max_browser_version: 100
      },
      slider: {
        state: [0, 100],
        disabled: true
      },
      eval_params: {
        check_for: "request",
        // Browser config
        browser_name: null,
        browser_setting: "default",
        cli_options: "",
        extensions: [],
        // Eval config
        project: null,
        automation: "terminal",
        seconds_per_visit: 5,
        // Eval range
        tests: [],
        lower_version: null,
        upper_version: null,
        lower_revision_nb: null,
        upper_revision_nb: null,
        only_release_revisions: true,
        // Sequence config
        nb_of_containers: 8,
        sequence_limit: 50,
        target_mech_id: null,
        target_cookie_name: "generic",
        search_strategy: "comp_search",
        // Database collection
        db_collection: null,
        // For plotting
        plot_mech_group: null,
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
        project: null,
      },
      dialog: {
        new_experiment_name: null,
        new_project_name: null
      },
      darkmode: null,
      darkmode_toggle: null,
      target_mech_id_input: null,
      target_mech_id: null,
      fatal_error: null,
      hide_advanced: true,
      hide_logs: true,
      hide_poc_editor: true,
      system: null,
      available_domains: null,
      websocket: null,
    }
  },
  computed: {
    "missing_plot_params": function () {
      const missing_params = [];
      const required_params_for_plotting = ["browser_name", "project", "plot_mech_group"];
      for (const index in required_params_for_plotting) {
        const param = required_params_for_plotting[index];
        if (this.eval_params[param] === null) {
          missing_params.push(param);
        }
      }
      return missing_params;

    },
    "db_collection_prefix": function () {
      if (this.eval_params.project === null || this.eval_params.browser_name === null) {
        return "";
      }
      return this.eval_params.project.toLowerCase() + "_" + this.eval_params.browser_name.toLowerCase();
    },
    "db_collection": function () {
      if (this.db_collection_suffix === "") {
        return this.db_collection_prefix;
      } else {
        return this.db_collection_prefix + "_" + this.db_collection_suffix;
      }
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
  },
  watch: {
    "selected.experiment": function (val) {
      if (val !== null) {
        this.hide_poc_editor = false;
      }
    },
    "slider.state": function (val) {
      this.eval_params.lower_version = val[0];
      this.eval_params.upper_version = val[1];
      this.propagate_new_params();
    },
    "db_collection": function (val) {
      this.eval_params.db_collection = val;
    },
    "info.log": {
      function(val) {
        if (log_section.scrollHeight - log_section.scrollTop - log_section.clientHeight < 1) {
          log_section.scrollTo({ "top": log_section.scrollHeight, "behavior": "auto" });
        }
      },
      "flush": "post",
    },
    "darkmode": function (val) {
      if (val) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    },
    "target_mech_id_input": function (val) {
      if (val === null || val === "") {
        this.eval_params.target_mech_id = this.eval_params.plot_mech_group;
      } else {
        this.eval_params.target_mech_id = val;
      }
      this.propagate_new_params();
    },
    "eval_params.plot_mech_group": function (val) {
      if (this.target_mech_id_input === null || this.target_mech_id_input === "") {
        this.eval_params.target_mech_id = val;
      }
      this.propagate_new_params();
    },
    "eval_params.browser_name": function (val) {
      // db_collection gets updated too late, so updating manually.
      this.eval_params.db_collection = this.db_collection;
      this.propagate_new_params();
    },
  },
  created: function () {
    this.websocket = this.create_socket();
    this.get_projects();
    this.get_browser_support();
    const path = `/api/poc/domain/`;
    axios.get(path)
    .then((res) => {
      if (res.data.status === "OK") {
        this.available_domains = res.data.domains;
      }
    })
    this.timer = setInterval(() => {
      if (this.projects.length == 0) {
        this.get_projects();
      }
      if (this.browsers.length == 0) {
        this.get_browser_support();
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
    // Darkmode functionality
    if ('theme' in localStorage) {
      this.darkmode = (localStorage.theme === 'dark');
      this.darkmode_toggle = (localStorage.theme === 'dark');
    }
    else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      this.darkmode = true;
      this.darkmode_toggle = true;
    } else {
      this.darkmode = false;
      this.darkmode_toggle = false;
    }
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
        if (this.selected.project !== null) {
          this.set_curr_project(this.selected.project);
        }
        this.propagate_new_params();
      });
      websocket.addEventListener("message", (e) => {
        const data = JSON.parse(e.data);
        if (data.hasOwnProperty("update")) {
          if (data.update.hasOwnProperty("plot_data")) {
            const revision_data = data.update.plot_data.revision_data;
            const version_data = data.update.plot_data.version_data;
            this.$refs.gantt.update_plot(this.eval_params.browser_name, revision_data, version_data);
            this.results.nb_of_evaluations = revision_data.outcome.length + version_data.outcome.length;
          }
          if (data.update.hasOwnProperty("experiments")) {
            this.tests = data.update.experiments;
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
      if (this.websocket === undefined || this.websocket.readyState > 1) {
        console.log(`Websocket connection died, reviving... (readyState: ${this.websocket.readyState})`);
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
    toggle_darkmode(event) {
      let darkmode_toggle_checked = event.srcElement.checked;
      this.darkmode = darkmode_toggle_checked;
      if (darkmode_toggle_checked) {
        localStorage.setItem('theme', 'dark');
      } else {
        localStorage.setItem('theme', 'light');
      }
    },
    get_projects(cb) {
      const path = `/api/projects/`;
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
    get_browser_support() {
      const path = `/api/browsers/`;
      axios.get(path)
        .then((res) => {
          if (res.data.status == "OK") {
            this.browsers = res.data.browsers;
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
          }
        })
        .catch((error) => {
          console.error(error);
        });
    },
    propagate_new_params() {
      if (this.missing_plot_params.length === 0) {
        console.log('Propagating parameter change');
        this.send_with_socket(
          {
            "new_params": this.eval_params
          }
        );
      } else {
        console.log("Missing plot parameters: ", this.missing_plot_params);
      }
    },
    project_dropdown_change(event) {
      const option = event.target.value;
      if (option == "Create new project...") {
        create_project_dialog.showModal();
      } else {
        this.set_curr_project(option)
      }
    },
    set_curr_project(project) {
      this.eval_params.project = project;
      this.send_with_socket({
        "select_project": project
      })
      this.selected.project = project;
      this.eval_params.tests = [];
    },
    set_curr_browser(browser) {
      this.eval_params.browser_name = browser["name"];
      this.curr_options.min_browser_version = browser["min_version"];
      this.curr_options.max_browser_version = browser["max_version"];
      this.slider.state = [browser["min_version"], browser["max_version"]];
      this.slider.disabled = false;
      this.browser_settings = browser['options'];
    },
    submit_form() {
      const path = `/api/evaluation/start/`;
      axios.post(path, this.eval_params)
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
      return axios.put(url, JSON.stringify(this.eval_params), {
        headers: {
          'Content-Type': 'application/json',
        }
      })
    },
    create_new_experiment() {
      const url = `/api/poc/${this.selected.project}/`;
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
      const url = `/api/projects/`;
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

      <label class="inline-flex items-center cursor-pointer">
        <input id="darkmode_toggle" type="checkbox" class="sr-only peer" @click="toggle_darkmode($event)"
          v-model="darkmode_toggle">
        <div
          class="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600">
        </div>
        <span class="ms-3 text-sm font-medium text-gray-900 dark:text-gray-300">Dark mode</span>
      </label>
    </header>

    <!-- Browser settings and experiments -->
    <div class="row-start-2 row-span-1 gap-3 flex flex-col">
      <!-- Browser settings -->
      <div class="form-section">
        <section-header section="eval_range"></section-header>

        <!-- Browser -->
        <div class="form-subsection">
          <h2 class="form-subsection-title">Browser</h2>
          <div class="flex flex-row justify-center mx-5">
            <div v-for="browser in browsers" class="radio-item flex-auto">
              <input type="radio" name="browser_name" @click="set_curr_browser(browser)">
              <label>{{ browser["name"] }}</label>
            </div>
          </div>
        </div>

        <div class="form-subsection">
          <h2 class="form-subsection-title">Browser version range</h2>
          <div class="flex flex-wrap">
            <div class="w-5/6 m-auto pt-12">
              <Slider
                v-model="this.slider.state"
                :min="this.curr_options.min_browser_version"
                :max="this.curr_options.max_browser_version"
                :disabled="this.slider.disabled"
                class="slider"
              />
            </div>
            <div class="pt-5 checkbox-item">
              <input
                v-model="eval_params.only_release_revisions"
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

        <select id="project_dropdown" class="mb-2" @change="project_dropdown_change" v-model="selected.project">
          <option disabled value="">Select a project</option>
          <option v-for="project in projects">{{ project }}</option>
          <option>Create new project...</option>
        </select>

        <div class="h-0 grow overflow-y-auto overflow-x-hidden">
          <ul class="horizontal-select">
            <li v-for="tuple in tests">
              <div>
                <input v-model="eval_params.tests" type="checkbox" class="ml-1" :value="tuple[0]" :disabled="!tuple[1]">
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
        <div v-if="this.selected.project" role="button" class="button mt-2" onclick="create_experiment_dialog.showModal()">
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
          <select class="w-fit h-fit" v-model="eval_params.plot_mech_group">
            <option disabled value="">Select an experiment</option>
            <option v-for="test in eval_params.tests">{{ test }}</option>
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
        <gantt ref="gantt" :eval_params="this.eval_params"></gantt>
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
        :project="this.selected.project"
        :poc="this.selected.experiment"></poc-editor>
      </div>
    </div>

    <!-- Advanced options -->
    <div class="form-section h-fit col-span-2 row-start-4">
      <div class="flex">
        <h2 class="flex-initial w-1/2 form-section-title pt-2">Advanced options</h2>
        <div class="w-full text-right">
          <button class="collapse-button" @click="this.hide_advanced = !this.hide_advanced">
            <div class="flex items-center">
              <p class="text-xl pb-1 px-1">+</p>
            </div>
          </button>
        </div>
      </div>
      <div :class="hide_advanced ? 'hidden' : ''">
        <div class="grid grid-cols-[auto,auto,auto] justify-start">
          <div class="flex flex-col">
            <div class="form-subsection">
              <section-header section="browser_rev_range"></section-header>
              <div class="p-1 w-1/2">
                <label for="lower_revision_nb">Lower rev nb</label>
                <input v-model.lazy="eval_params.lower_revision_nb" class="number-input w-32" type="number">
              </div>

              <div class="p-1 w-1/2">
                <label for="upper_revision_nb">Upper rev nb</label>
                <input v-model.lazy="eval_params.upper_revision_nb" class="number-input w-32" type="number">
              </div>
            </div>

            <div class="form-subsection row-start-2">
              <section-header section="reproduction_id"></section-header>
              <input v-model="target_mech_id_input" type="text" class="input-box" id="mech_id" name="mech_id"
                :placeholder="eval_params.plot_mech_group"><br>
              <br>
            </div>
          </div>

          <div class="form-subsection col-start-2 h-max">
              <section-header section="db_collection"></section-header>
              <label for="db_collection_name" hidden>Database collection:</label>
              <input v-bind:value="this.db_collection_prefix" type="text" class="input-box" disabled>
              <input v-model="db_collection_suffix" type="text" class="input-box mb-1"><br>
          </div>

          <!-- Evaluation settings -->
          <div class="form-subsection w-fit eval_opts col-start-3">
            <section-header section="eval_settings"></section-header>
            <div class="form-subsection">
              <section-header section="search_strategy"></section-header>

              <div class="radio-item">
                <input v-model="eval_params.search_strategy" type="radio" id="bin_seq" name="search_strategy_option"
                  value="bgb_sequence">
                <label for="bgb_sequence">BGB sequence</label>
                <tooltip tooltip="bgb_sequence"></tooltip>
              </div>

              <div class="radio-item">
                <input v-model="eval_params.search_strategy" type="radio" id="bgb_search" name="search_strategy_option"
                  value="bgb_search">
                <label for="bgb_search">BGB search</label>
                <tooltip tooltip="bgb_search"></tooltip>
              </div>

              <div class="radio-item">
                <input v-model="eval_params.search_strategy" type="radio" id="comp_search" name="search_strategy_option"
                  value="comp_search">
                <label for="comp_search">Composite search</label>
                <tooltip tooltip="comp_search"></tooltip>
              </div>
              <br>

              <div class="flex items-baseline mb-1">
                <label for="sequence_limit" class="mb-0 align-middle">Sequence limit</label>
                <tooltip tooltip="sequence_limit"></tooltip>
              </div>
              <input v-model.number="eval_params.sequence_limit" class="input-box" type="number" min="1" max="10000">
            </div>

            <div class="form-subsection">
              <section-header section="parallel_containers"></section-header>
              <input v-model.number="eval_params.nb_of_containers" class="input-box" type="number" id="nb_of_containers"
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

