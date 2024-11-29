<script>
  import ace from "ace-builds";
  import { Mode as HtmlMode } from 'ace-builds/src-noconflict/mode-html';
  import { Mode as JsMode } from 'ace-builds/src-noconflict/mode-javascript';
  import { Mode as JsonMode } from 'ace-builds/src-noconflict/mode-json';
  import { Mode as PyMode } from 'ace-builds/src-noconflict/mode-python';
  import { getMode as getInteractionScriptMode } from '../interaction_script_mode';
  import 'ace-builds/src-min-noconflict/ext-modelist';
  import 'ace-builds/src-min-noconflict/theme-twilight';
  import 'ace-builds/src-min-noconflict/theme-xcode';
  import axios from 'axios';
  export default {
    props: {
      available_domains: Array,
      darkmode: Boolean,
      poc: String,
      project: String,
    },
    data() {
      return {
        active_file: {
            name: null,
            content: null,
            should_update_server: true,
        },
        active_poc: {
            name: this.poc,
            active_domain: null,
            active_path: null,
            tree: {},
            // Example tree:
            // {
            //   'test.com': {
            //     "path1": {
            //        "file1": null,
            //        "file2": null
            //     },
            //     "path2": {
            //        "file1": null
            //     },
            //   },
            //   'not.test': {
            //     "path1": {
            //        "file1": null,
            //        "file2": null
            //     },
            //     "path2": {
            //        "file1": null
            //     },
            //   },
            //  'script.cmd': null,
            // },
        },
        available_file_types: [
          'html',
          'js',
          'py',
        ],
        available_config_types: {
          'script.cmd': 'Interaction script',
          'url_queue.txt': 'URL queue'
        },
        poc_tree_config: {
          domain: 'Config',
          page: '_',
        },
        dialog: {
          domain: {
            name: null,
          },
          page: {
            name: "main",
          },
          file: {
            type: null,
          }
        },
        config_type: null,
        editor: null,
        timeout: null,
      }
    },
    computed: {
      active_poc_tree() {
        const configDomain = this.poc_tree_config.domain;
        const configPage = this.poc_tree_config.page;

        return Object.entries(this.active_poc.tree).reduce((acc, [domain, pages]) => {
          if (domain !== pages) {
            return [
              ...acc,
              [domain, pages]
            ]
          }

          // A single top-level file -> create a virtual config folder
          const config_folder = acc.find(([domain]) => domain === configDomain);
          return [
            ...acc.filter(([domain]) => domain !== configDomain),
            [configDomain, {
              [configPage]: {
                ...config_folder[1].subfolder,
                [domain]: pages,
              }
            }],
          ]
        }, [[configDomain, {[configPage]: {}}]]);
      }
    },
    methods: {
      set_active_file(domain, file_path, file_name) {
        this.active_poc.active_domain = domain;
        this.active_poc.active_path = file_path;
        this.active_file.name = file_name;
        const project = this.project;
        const poc = this.active_poc.name;
        const params = {};
        if (domain !== null) {
          params["domain"] = domain;
        }
        if (file_path !== null) {
          params["path"] = file_path;
        }
        const path = `/api/poc/${project}/${poc}/${file_name}/`;
        axios.get(path, {params: params})
        .then((res) => {
          if (res.data.status === "OK") {
            this.active_file.should_update_server = false;
            this.active_file.content = res.data.content;
            const modelist = ace.require("ace/ext/modelist");
            const mode = modelist.getModeForPath(file_name).mode
            this.editor.session.setMode(mode);
            this.editor.setValue(res.data.content);
            this.editor.clearSelection();
            this.active_file.should_update_server = true;
            this.update_editor_mode(file_name);
          }
        })
        .catch((error) => {
          console.error(error);
        });
      },
      update_file_content() {
        if (this.timeout) {
          clearTimeout(this.timeout);
        }
        if (this.active_file.should_update_server == false) {
          return;
        }
        if (this.active_file.name === null) {
          return;
        }
        this.timeout = setTimeout(() => {
          const project = this.project;
          const poc = this.active_poc.name;
          const domain = this.active_poc.active_domain;
          const file_path = this.active_poc.active_path;
          const file_name = this.active_file.name;
          const params = {
            "content": this.editor.session.getValue()
          };
          if (domain !== null) {
            params["domain"] = domain;
          }
          if (file_path !== null) {
            params["path"] = file_path;
          }
          const path = `/api/poc/${project}/${poc}/${file_name}/`;
          axios.post(path, {"content": this.editor.session.getValue()}, {params: params})
          .then((res) => {
            if (res.data.status == "NOK") {
              console.error("Could not update file on server");
            }
          })
          .catch((error) => {
            console.error(error);
          });
        }, 500);
      },
      update_poc_tree(poc_name) {
        const active_poc_name = poc_name === undefined ? this.active_poc.name : poc_name;
        const path = `/api/poc/${this.project}/${active_poc_name}/`;
        axios.get(path)
        .then((res) => {
          if (res.data.status === "OK") {
            this.active_poc.name = active_poc_name;
            this.active_poc.tree = res.data.tree;
          }
        })
        .catch((error) => {
          console.error(error);
        });
      },
      update_editor_mode(file_name) {
        const file_ext = file_name.split('.').pop();
        switch (file_ext) {
          case "html":
            this.editor.session.setMode(new HtmlMode());
            break;
          case "js":
            this.editor.session.setMode(new JsMode());
            break;
          case "json":
            this.editor.session.setMode(new JsonMode());
            break;
          case "py":
            this.editor.session.setMode(new PyMode());
            break;
          case "cmd":
            getInteractionScriptMode().then(({ Mode }) => { this.editor.session.setMode(new Mode()) })
            break;
        }
      },
      add_page() {
        const url = `/api/poc/${this.project}/${this.poc}/`;
        const domain = this.dialog.domain.name;
        const page = this.dialog.page.name;
        const file_type = this.dialog.file.type;
        axios.post(url, {
          "domain": domain,
          "page": page,
          "file_type": file_type,
        })
        .then((res) => {
          if (res.data.status === "OK") {
            this.update_poc_tree();
            this.dialog.domain.name = null;
            this.dialog.file.type = null;
          } else {
            alert(res.data.msg);
          }
        })
        .catch(() => {

        });
      },
      add_config() {
        const url = `/api/poc/${this.project}/${this.poc}/config`;
        axios.post(url, {
          "type": this.config_type,
        })
        .then(() => {
          this.update_poc_tree();
          this.config_type = null;
        })
        .catch(() => {

        });
      },
      has_config() {
        if (this.active_poc.tree === undefined) {
          console.error("Could not check config in undefined poc tree");
          return false;
        }
        const arr = Object.keys(this.active_poc.tree).filter((domain) => ['url_queue.txt', 'script.cmd'].includes(domain));
        return arr.length > 0;
      }
    },
    mounted() {
      ace.config.set('basePath', '/node_modules/ace-builds/src-min-noconflict');
      this.editor = ace.edit("editor");
      this.editor.session.addEventListener("change", this.update_file_content);
    },
    watch: {
      "darkmode": function(val) {
        if (val) {
          this.editor.setTheme("ace/theme/twilight");
        } else {
          this.editor.setTheme("ace/theme/xcode");
        }
      },
      "active_file.name": function (val) {
        // Make editor readOnly when no file is selected
        this.editor.setOptions({
          "readOnly": val === null
        });
      },
      "poc": function(val) {
        this.editor.setValue();
        this.editor.clearSelection();
        this.active_file.name = null;
        this.active_file.content = null;
        this.update_poc_tree(val);
      },
      "project": function(val) {
        this.editor.setValue();
        this.editor.clearSelection();
        this.active_file.name = null;
        this.active_file.content = null;
        this.active_poc.name = null;
        this.active_poc.active_domain = null;
        this.active_poc.active_path = null;
      },
    },
  };
</script>
<style>
  #editor {
      position: relative;
  }
</style>
<template>
  <div class="flex flex-row h-[32rem]">
    <div v-if="this.active_poc.name == null" class="basis-4/12 w-1/12 h-full pr-6">
      Select an experiment in the Experiments pane to edit it here.
    </div>
    <div v-else class="basis-4/12 w-1/12 h-full grow overflow-y-auto">
      <ul class="relative flex flex-col text-gray-700 bg-white shadow-md w-96 rounded-md bg-clip-border dark:bg-dark-3 dark:text-white">
        <nav class="flex min-w-[240px] h-full flex-col gap-1 p-2 font-sans text-base font-normal text-blue-gray-700">
          <li v-for="([domain, pages]) in Object.entries(active_poc.tree).sort()">
            <div v-if="domain === 'url_queue.txt' || domain === 'script.cmd'">
              <div
                class="flex border-b-2 p-2 font-bold mb-2 hover:bg-gray-100 hover:bg-opacity-80 hover:text-blue-gray-900 hover:cursor-pointer focus:bg-blue-gray-50 focus:bg-opacity-80 focus:text-blue-gray-900"
                role="button"
                @click="set_active_file(null, null, domain)" >
                {{ domain }}
              </div>
            </div>
            <ul v-else>
              <li v-for="([path, files]) in Object.entries(pages).sort()">
                <div v-if="files">
                  <div class="flex border-b-2 p-2 font-bold mb-2" >
                    <div class="w-full">
                      {{ domain }}/{{ path }}
                    </div>
                    <a :href="'https://'+domain+'/'+this.project+'/'+this.active_poc.name+'/'+path" target="_blank">
                      <v-icon name="fa-link" class=""/>
                    </a>
                  </div>
                  <ul>
                    <li v-for="([file, _]) in Object.entries(files)"
                    :class="(domain + '/' + path === this.active_poc.active_domain + '/' + this.active_poc.active_path) && (file === this.active_file.name) ? 'bg-blue-100 dark:bg-blue-900 rounded-lg' : 'rounded-lg'">
                      <div
                        role="button"
                        class="flex items-center indent-4 w-full p-2 hover:bg-gray-100 hover:bg-opacity-80 hover:text-blue-gray-900 hover:cursor-pointer focus:bg-blue-gray-50 focus:bg-opacity-80 focus:text-blue-gray-900 rounded-lg"
                        @click="set_active_file(domain, path, file)"
                      >
                        {{ file }}
                      </div>
                    </li>
                  </ul>
                </div>
                <div v-else class="flex justify-between border-b-2 p-2 font-bold mb-2 hover:bg-gray-100 hover:bg-opacity-80 hover:text-blue-gray-900 hover:cursor-pointer focus:bg-blue-gray-50 focus:bg-opacity-80 focus:text-blue-gray-900">
                  <div
                      role="button"
                      class="rounded-lg"
                      @click="set_active_file(domain, null, path)"
                    >
                    <div class="w-full">
                      {{ domain }}/{{ path }}
                    </div>
                  </div>
                  <div>
                    <a :href="'https://'+domain+'/'+this.project+'/'+this.active_poc.name+'/'+path" target="_blank">
                      <v-icon name="fa-link" class=""/>
                    </a>
                  </div>
                </div>
              </li>
            </ul>
          </li>
          <div class="flex flex-row justify-between">
            <li role="button" class="button text-center w-full mr-1" onclick="create_domain_dialog.showModal()">
              Add page
            </li>
            <li v-if="!this.has_config()" role="button" class="button text-center w-full mr-1" onclick="create_config_dialog.showModal()">
              Add script
            </li>
          </div>
        </nav>
      </ul>
    </div>
    <div id="editor" class="basis-8/12"></div>
  </div>

  <!-- Create domain dialog -->
  <dialog id="create_domain_dialog" class="dialog">
    <form method="dialog" @submit="add_page">
      <p>
        <label>
          <div class="py-2">Choose a domain:</div>
          <select name="domain" id="domain" v-model="dialog.domain.name" required>
            <option v-for="domain in available_domains" :value="domain">
              {{ domain }}
            </option>
          </select>

          <div class="py-2">Choose path:</div>
          <input type="text" id="page" class="input-box" v-model="dialog.page.name" required />

          <div class="py-2">Choose file type:</div>
          <select name="file" id="file" v-model="dialog.file.type" required>
            <option v-for="file_type in available_file_types" :value="file_type">
              {{ file_type }}
            </option>
          </select>
        </label>
      </p>
      <div class="flex pt-3">
        <input class="button m-2 w-full" type="submit" value="Add domain">
        <input class="button m-2" type="button" value="Cancel" onclick="create_domain_dialog.close()">
      </div>
    </form>
  </dialog>

  <!-- Create config dialog -->
  <dialog id="create_config_dialog" class="dialog">
    <form method="dialog" @submit="add_config">
      <p>
        <label>
          <div class="py-2">Choose config type:</div>
          <select name="config_type" id="config_type" v-model="config_type" required>
            <option v-for="(label, value) of available_config_types" :value="value">
              {{ label }}
            </option>
          </select>
        </label>
      </p>
      <div class="flex pt-3">
        <input class="button m-2 w-full" type="submit" value="Create config">
        <input class="button m-2" type="button" value="Cancel" onclick="create_config_dialog.close()">
      </div>
    </form>
  </dialog>
</template>
