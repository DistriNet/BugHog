<style src="vue-multiselect/dist/vue-multiselect.min.css"></style>
<style src="@vueform/slider/themes/default.css"></style>
<script>
import axios from 'axios'
import Gantt from "./components/gantt.vue"
import SectionHeader from "./components/section-header.vue";
import Slider from '@vueform/slider'
import Tooltip from "./components/tooltip.vue";
export default {
  components: {
    Gantt,
    SectionHeader,
    Slider,
    Tooltip,
  },
  data() {
    return {
      timer: null,
      projects: [],
      browsers: [],
      browser_settings: [],
      db_collection_suffix: "",
      tests: [],
      info: {
        log: [],
        database: {
          "host": null,
          "connected": false
        },
        running: false,
      },
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
        sequence_limit: 100,
        target_mech_id: null,
        target_cookie_name: "generic",
        search_strategy: "comp_search",
        // Database collection
        db_collection: null,
        // For plotting
        plot_mech_group: null,
      },
      results: {
        nb_of_evaluations: 0,
      },
      selected: {
        experiment: null,
        project: null,
      },
      darkmode: null,
      darkmode_toggle: null,
      target_mech_id_input: null,
      target_mech_id: null,
      fatal_error: null,
      hide_advanced: true,
      hide_logs: true,
      system: null,
    }
  },
  computed: {
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
      else if (this.info.database.connected) {
        return `Connected to MongoDB at ${this.info.database.host}`;
      } else {
        return `Connecting to database...`;
      }
    },
  },
  watch: {
    "selected.project": function (val) {
      this.set_curr_project(val);
    },
    "slider.state": function (val) {
      this.eval_params.lower_version = val[0];
      this.eval_params.upper_version = val[1];
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
      this.update_results();
    },
    "eval_params.plot_mech_group": function (val) {
      if (this.target_mech_id_input === null || this.target_mech_id_input === "") {
        this.eval_params.target_mech_id = val;
      }
      this.update_results();
    },
  },
  mounted: function () {
    this.get_info();
    this.update_results();
    this.get_projects();
    this.get_browser_support();
    setTimeout(function () {
      log_section.scrollTo({ "top": log_section.scrollHeight, "behavior": "auto" });
    },
      500
    );
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
      this.get_info();
      this.update_results();
    }, 2000);
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
    toggle_darkmode(event) {
      let darkmode_toggle_checked = event.srcElement.checked;
      this.darkmode = darkmode_toggle_checked;
      if (darkmode_toggle_checked) {
        localStorage.setItem('theme', 'dark');
      } else {
        localStorage.setItem('theme', 'light');
      }
    },
    get_info() {
      const path = `/api/info/`;
      axios.get(path)
        .then((res) => {
          if (res.data.status === "OK") {
            if (log_section.scrollHeight - log_section.scrollTop - log_section.clientHeight < 1) {
              this.info = res.data.info;
              log_section.scrollTo({ "top": log_section.scrollHeight, "behavior": "auto" });
            }
            this.fatal_error = false;
          } else {
            this.info.log = res.data.info.log;
            this.fatal_error = true;
          }
        })
        .catch((error) => {
          console.error(error);
        });
    },
    get_projects() {
      const path = `/api/projects/`;
      axios.get(path)
        .then((res) => {
          if (res.data.status == "OK") {
            this.projects = res.data.projects;
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
    get_tests(project) {
      const path = `/api/tests/${project}/`;
      axios.get(path)
        .then((res) => {
          this.tests = res.data.tests;
        })
        .catch((error) => {
          console.error(error);
        });
    },
    set_curr_project(project) {
      this.eval_params.project = project;
      this.get_tests(project);
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
    update_results() {
      this.fetch_results('/api/data/').then((res) => {
        if (res.data.status === "NOK") {
          this.results.nb_of_evaluations = 0;
          return;
        }
        let revision_data = res.data.revision;
        let version_data = res.data.version;
        this.$refs.gantt.update_plot(this.eval_params.browser_name, revision_data, version_data);
        this.results.nb_of_evaluations = revision_data.outcome.length + version_data.outcome.length;
      })
      .catch((error) => {
        console.error(error);
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

        <!-- <div v-for="option in browser_settings" class="radio-item w-full">
          <input v-model="eval_params.browser_setting" type="radio" :value="option.short">
          <label :for="option.short">{{ option.pretty }}</label>
        </div> -->

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

        <select class="mb-2" v-model="selected.project">
          <option disabled value="">Select a project</option>
          <option v-for="project in projects">{{ project }}</option>
        </select>

        <div class="h-0 grow overflow-y-auto">
          <ul class="horizontal-select">
            <li v-for="test in tests">
              <div>
                <input v-model="eval_params.tests" type="checkbox" :value="test">
                <label for="vue-checkbox-list">{{ test }}</label>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Start button and results section -->
    <div class="row-start-2 col-start-2 flex flex-col h-full">
      <div v-if="this.info.running == false">
        <button @click="submit_form" class="w-full bg-green-300 dark:bg-green-900">Start evaluation</button>
      </div>
      <div v-else>
        <button @click="stop(false)" class="w-1/2 bg-yellow-300 dark:bg-yellow-500">Stop gracefully</button>
        <button @click="stop(true)" class="w-1/2 bg-red-400 dark:bg-red-800">Stop forcefully</button>
      </div>
      <div class="results-section mt-2 h-full flex flex-col">
        <section-header section="results" left></section-header>
        <div class="flex flex-wrap justify-between h-fit">
          <select class="w-fit h-fit" v-model="eval_params.plot_mech_group">
            <option disabled value="">Select an experiment</option>
            <option v-for="test in eval_params.tests">{{ test }}</option>
          </select>
          <div class="flex flex-wrap">
            <ul class="my-3">
              <li v-if="this.info.running"> <b>Status:</b> Running &#x2705;</li>
              <li v-else> <b>Status:</b> Stopped &#x1F6D1;</li>
            </ul>
          </div>
          <div class="flex flex-wrap">
            <ul class="my-3 w-64">
              <li><b>Number of experiments:</b> {{ results.nb_of_evaluations }}</li>
            </ul>
          </div>
        </div>
        <gantt ref="gantt"></gantt>
      </div>
    </div>

    <!-- Advanced options -->
    <div class="form-section h-fit col-span-2 row-start-3">
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

            <!-- <div class="form-subsection">
              <section-header section="automation"></section-header>
              <div class="radio-item">
                <input v-model="eval_params.automation" type="radio" id="automation" name="automation_option"
                  value="terminal">
                <label for="terminal_automation">CLI automation</label>
              </div>

              <div class="radio-item">
                <input v-model="eval_params.automation" type="radio" id="automation" name="automation_option" value="selenium">
                <label for="terminal_automation">Selenium automation</label><br>
              </div>
            </div> -->

            <div class="form-subsection">
              <section-header section="search_strategy"></section-header>

              <div class="radio-item">
                <input v-model="eval_params.search_strategy" type="radio" id="bin_seq" name="search_strategy_option"
                  value="bin_seq">
                <label for="bin_seq">Binary sequence</label>
                <tooltip tooltip="bin_seq"></tooltip>
              </div>

              <div class="radio-item">
                <input v-model="eval_params.search_strategy" type="radio" id="bin_search" name="search_strategy_option"
                  value="bin_search">
                <label for="bin_search">Binary search</label>
                <tooltip tooltip="bin_search"></tooltip>
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
              <!-- <div id="search_stategy_hidden_options" class="hidden_options">
                <br>

                <div class="flex items-baseline">
                  <label for="leak">Request or cookie</label>
                  <tooltip tooltip="request_or_cookie"></tooltip>
                </div>
                <div class="radio-item">
                  <input v-model="eval_params.check_for" type="radio" id="request" name="leak" value="request">
                  <label for="request">Request</label>
                </div>
                <div class="radio-item">
                  <input v-model="eval_params.check_for" type="radio" id="cookie" name="leak" value="cookie">
                  <label for="cookie">Cookie</label>
                </div>
                <div v-if="eval_params.check_for == 'cookie'">
                  <label for="cookie_name">Cookie name</label>
                  <input v-model="eval_params.target_cookie_name"  type="text" id="cookie_name" name="cookie_name">
                </div>
              </div> -->
            </div>

            <div class="form-subsection">
              <section-header section="parallel_containers"></section-header>
              <input v-model.number="eval_params.nb_of_containers" class="input-box" type="number" id="nb_of_containers"
                name="nb_of_containers" min="1" max="16">
            </div>

            <!-- <div class="form-section">
            <section-header section="browser_config"></section-header>

            <div class="form-subsection flex flex-wrap">
              <h2 class="form-subsection-title">Settings</h2>

              <div v-for="option in browser_settings" class="radio-item w-full">
                <input v-model="eval_params.browser_setting" type="radio" :value="option.short">
                <label :for="option.short">{{ option.pretty }}</label>
              </div>
            </div>

            <div class="form-subsection flex flex-wrap">
              <h2 class="form-subsection-title">Extensions</h2>

              <div v-for="extension in extensions" class="checkbox-item">
                <input v-model="eval_params.extensions" type="checkbox" :value="extension">
                <label :for="extension">{{ extension }}</label>
              </div>
            </div>

            <div class="form-subsection flex flex-wrap">
              <h2 class="form-subsection-title">CLI options <i>(beta)</i></h2>

              <textarea v-model="eval_params.cli_options" id="message" rows="4" class="large-text-input"
                placeholder="--sandbox"></textarea>

            </div>
          </div> -->
          </div>
        </div>
      </div>
    </div>

    <!-- Logs -->
    <div class="results-section h-fit col-span-2 row-start-4 flex-1">
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
            <li v-for="entry in this.info.log">
              <p>{{ entry }}</p>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

