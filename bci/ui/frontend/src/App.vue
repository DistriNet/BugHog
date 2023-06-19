<style src="vue-multiselect/dist/vue-multiselect.min.css"></style>
<script>
import axios from 'axios'
export default {
  data() {
    return {
      timer: null,
      projects: [],
      browsers: [],
      browser_settings: [],
      extensions: [],
      // db_collection_suffix: "",
      db_collection_suffix: "",
      tests: [],
      plot_mech_group: null,
      info: {
        log: [],
        database: {
          "host": "connecting...",
          "connected": false
        },
        running: false,
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
        only_release_revisions: false,
        // Sequence config
        nb_of_containers: 8,
        sequence_limit: 1000,
        target_mech_id: "",
        target_cookie_name: "generic",
        search_strategy: "bin_seq",
        // Database collection
        db_collection: "",
        // For plotting
        plot_mech_group: ""
      },
      results: {
        nb_of_evaluations: null,
        plot_html: null
      }
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
    }
  },
  watch: {
    "db_collection": function (val) {
      this.eval_params.db_collection = val;
    },
    "info.log": {
      function (val) {
        console.log("hi");
        if (log_section.scrollHeight - log_section.scrollTop - log_section.clientHeight < 1) {
          log_section.scrollTo({"top": log_section.scrollHeight, "behavior": "auto"});
        }
      },
      "flush": "post"
    }
  },
  mounted: function () {
    this.get_info();
    this.get_projects();
    this.get_browsers();
    setTimeout(function() {
        log_section.scrollTo({"top": log_section.scrollHeight, "behavior": "auto"});
      },
      500
    );
    this.timer = setInterval(() => {
      if (this.projects.length == 0 || this.browsers.length == 0) {
        this.get_projects();
        this.get_browsers();
      }
      this.get_info();
    }, 2000);
  },
  methods: {
    get_info() {
      const path = `http://${location.host}/api/info/`;
      axios.get(path)
        .then((res) => {
          if (res.data.status == "OK") {
            if (log_section.scrollHeight - log_section.scrollTop - log_section.clientHeight < 1) {
              this.info = res.data.info;
              log_section.scrollTo({"top": log_section.scrollHeight, "behavior": "auto"});
            } else {
              this.info = res.data.info;
            }
          }
        })
        .catch((error) => {
          console.error(error);
        });
    },
    get_projects() {
      const path = `http://${location.host}/api/projects/`;
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
    get_browsers() {
      const path = `http://${location.host}/api/browsers/`;
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
    get_options(browser) {
      const path = `http://${location.host}/api/options/${browser}/`;
      axios.get(path)
        .then((res) => {
          this.browser_settings = res.data.options;
        })
        .catch((error) => {
          console.error(error);
        });
    },
    get_extensions(browser) {
      const path = `http://${location.host}/api/extensions/${browser}/`;
      axios.get(path)
        .then((res) => {
          this.extensions = res.data.extensions;
        })
        .catch((error) => {
          console.error(error);
        });
    },
    get_tests(project) {
      const path = `http://${location.host}/api/tests/${project}/`;
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
      this.eval_params.browser_name = browser;
      this.get_options(browser);
      this.get_extensions(browser);
    },
    set_plot_mech_group(mech_group) {
      this.eval_params.plot_mech_group = mech_group;
      this.update_plot();
    },
    submit_form() {
      const path = `http://${location.host}/api/evaluation/start/`;
      axios.post(path, this.eval_params)
        .then((res) => {

        })
        .catch((error) => {
          console.error(error);
        });
    },
    stop(forcefully) {
      const path = `http://${location.host}/api/evaluation/stop/`;
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
    update_plot() {
      const path = `http://${location.host}/api/results/`;
      axios.put(path, this.eval_params)
        .then((res) => {
          if (res.data.status == "OK") {
            this.results.nb_of_evaluations = res.data.nb_of_evaluations;
            this.results.plot_html = res.data.plot_html;
          }
        })
        .catch((error) => {
          console.error(error);
        });
    },
  },
  beforeDestroy() {
    clearInterval(this.timer)
  }
}
</script>

<template>
  <div class="banner-page">
    <div>
      <button id="dropdown_project" data-dropdown-toggle="project_dropdown" class="dropdown mx-3" type="button">{{
        eval_params.project || "Project" }}<svg class="w-4 h-4 ml-2" aria-hidden="true" fill="none" stroke="currentColor"
          viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
        </svg></button>
      <!-- Dropdown menu -->
      <div id="project_dropdown"
        class="z-10 hidden bg-white divide-y divide-gray-100 rounded-lg shadow w-44 dark:bg-gray-700">
        <ul class="py-2 text-sm text-gray-700 dark:text-gray-200" aria-labelledby="dropdown_project">
          <li v-for="project in projects">
            <a href="#" class="dropdown-item" @click="set_curr_project(project)">{{ project }}</a>
          </li>
        </ul>
      </div>

      <button id="dropdown_browser" data-dropdown-toggle="browser_dropdown" class="dropdown" type="button">{{
        eval_params.browser_name || "Browser"
      }}<svg class="w-4 h-4 ml-2" aria-hidden="true" fill="none" stroke="currentColor" viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
        </svg></button>
      <!-- Dropdown menu -->
      <div id="browser_dropdown"
        class="z-10 hidden bg-white divide-y divide-gray-100 rounded-lg shadow w-44 dark:bg-gray-700">
        <ul class="py-2 text-sm text-gray-700 dark:text-gray-200" aria-labelledby="dropdown_browser">
          <li v-for="browser in browsers">
            <a href="#" class="dropdown-item" @click="set_curr_browser(browser)">{{ browser }}</a>
          </li>
        </ul>
      </div>
    </div>

    <!-- <p>[FRAMEWORK NAME + LOGO]</p> -->
    <p v-if="info.database.host !== null">Using MongoDB at {{ info.database.host }}</p>
    <p v-else>Could not connect to MongoDB. Click <a ref="db_retry" href="#" ping="/api/database/connect/">here</a> to retry connection.</p>
    <p class="pr-10"><a href="/log">Logs</a></p>
  </div>
  <div>
    <div class="column">
      <div class="w-screen form-section w-screen">
        <div class=" w-screen">
          <h2 class="form-section-title">Experiments</h2>
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
    <div class="flex flex-wrap w-screen">
      <div>


        <div class="flex flex-wrap">

          <div class="column">
            <div class="form-section">
              <h2 class="form-section-title">Evaluation range</h2>

              <div>
                <div class="form-subsection flex flex-wrap">
                  <div class="flex flex-wrap w-full">
                    <div class="p-1 w-1/2">
                      <label for="lower_version">Lower version</label>
                      <input v-model.number="eval_params.lower_version" class="number-input w-20" type="number">
                    </div>

                    <div class="p-1 w-1/2">
                      <label for="upper_version">Upper version</label>
                      <input v-model.number="eval_params.upper_version" class="number-input w-20" type="number">
                    </div>
                  </div>

                  <div class="checkbox-item">
                    <input v-model="eval_params.only_release_revisions" type="checkbox" disabled>
                    <label><i>Only release revisions (coming soon)</i></label>
                  </div>
                </div>

                <div class="text-center w-full">
                  <p> -- or -- </p>
                </div>

                <div class="form-subsection flex flex-wrap w-full">
                  <div class="p-1 w-1/2">
                    <label for="lower_revision_nb">Lower rev nb</label>
                    <input v-model.lazy="eval_params.lower_revision_nb" class="number-input w-32" type="number">
                  </div>

                  <div class="p-1 w-1/2">
                    <label for="upper_revision_nb">Upper rev nb</label>
                    <input v-model.lazy="eval_params.upper_revision_nb" class="number-input w-32" type="number">
                  </div>
                </div>
              </div>
            </div>

            <div class="form-section">
              <label for="db_collection_name">Database collection:</label>
              <input v-bind:value="this.db_collection_prefix" type="text" disabled>
              <input v-model="db_collection_suffix" type="text"><br>
            </div>

            <div class="form-section">
              <h2 class="form-section-title">Browser configuration</h2>

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
            </div>
          </div>

          <div class="column">
            <div class="form-section eval_opts">
              <h2 class="form-section-title">Evaluation settings</h2>

              <div class="form-subsection">
                <h2 class="form-section-title">Automation</h2>
                <div class="radio-item">
                  <input v-model="eval_params.automation" type="radio" id="automation" name="automation_option" value="terminal">
                  <label for="terminal_automation">CLI automation</label>
                </div>

                <!-- <div class="radio-item">
                  <input v-model="eval_params.automation" type="radio" id="automation" name="automation_option" value="selenium">
                  <label for="terminal_automation">Selenium automation</label><br>
                </div> -->
              </div>

              <div class="form-subsection">
                <h2 class="form-section-title">Search strategy</h2>

                <div class="radio-item">
                  <input v-model="eval_params.search_strategy" type="radio" id="bin_seq" name="search_strategy_option" value="bin_seq">
                  <label for="bin_seq">Binary sequence</label>
                </div>

                <div class="radio-item">
                  <input v-model="eval_params.search_strategy" type="radio" id="bin_search" name="search_strategy_option" value="bin_search">
                  <label for="bin_search">Binary search</label>
                </div>

                <div class="radio-item">
                  <input v-model="eval_params.search_strategy" type="radio" id="bin_search" name="search_strategy_option" value="comp_search">
                  <label for="comp_search">Composite search</label>
                </div>
                <br>

                <label for="sequence_limit">Sequence limit</label>
                <input v-model.number="eval_params.sequence_limit" type="number" min="1" max="10000">
                <div id="search_stategy_hidden_options" class="hidden_options">
                  <br>
                  <label for="mech_id">Reproduction id (this will only work for the experiment to which it is associated):</label>
                  <input v-model="eval_params.target_mech_id" type="text" id="mech_id" name="mech_id"><br>
                  <br>
                  <label for="leak">Request or cookie</label>
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
                </div>
              </div>

              <div class="form-subsection">
                <h2 class="form-section-title">Number of parallel containers</h2>

                <input v-model.number="eval_params.nb_of_containers" type="number" id="nb_of_containers" name="nb_of_containers" min="1" max="16">
              </div>

            </div>

          </div>
        </div>

      </div>
      <div class="column">
        <div v-if="this.info.running == false" class="m-2">
          <button @click="submit_form" class="w-full bg-green-300">Start evaluation</button>
        </div>
        <div v-else class="m-2">
          <button @click="stop(false)" class="w-1/2 bg-yellow-300">Stop gracefully</button>
          <button @click="stop(true)" class="w-1/2 bg-red-400">Stop forcefully</button>
        </div>
        <div class="results-section">
          <div class="banner-generic">
            <h2 class="form-section-title">Results</h2>
            <div>
              <button id="dropdown_test" data-dropdown-toggle="test_dropdown" class="dropdown mx-3" type="button">{{
                eval_params.plot_mech_group || "Select an experiment" }}<svg class="w-6 h-4 ml-2" aria-hidden="true" fill="none" stroke="currentColor"
                  viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg></button>
              <!-- Dropdown menu -->
              <div id="test_dropdown"
                class="z-10 hidden bg-white divide-y divide-gray-100 rounded-lg shadow w-44 dark:bg-gray-700">
                <ul class="py-2 text-sm text-gray-700 dark:text-gray-200" aria-labelledby="dropdown_project">
                  <li v-for="test in eval_params.tests">
                    <a href="#" class="dropdown-item" @click="set_plot_mech_group(test)">{{ test }}</a>
                  </li>
                </ul>
              </div>
            </div>
            <button @click="update_plot" class="bg-gray-300">Refresh</button>
          </div>
          <ul>
            <li>Number of experiments: {{ results.nb_of_evaluations }}</li>
          </ul>
          <iframe id="plot" width="700" height="350" scrolling="no" :srcdoc="results.plot_html">
          </iframe>
          <!-- <svg width="500" height="250">
            <rect width="500" height="250" style="fill:rgb(255,255,255);stroke-width:3;stroke:rgb(0,0,0)" />
          </svg> -->
        </div>
      </div>

      <div class="column">
        <div class="results-section w-screen">
          <h2 class="form-section-title">Log</h2>
          <div id="log_section" class="h-96 p-1 bg-white overflow-y-scroll flex flex-col">
            <ul>
              <li v-for="entry in this.info.log">
                <p>{{ entry }}</p>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div></template>

