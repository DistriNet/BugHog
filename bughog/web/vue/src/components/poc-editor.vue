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
      darkMode: Boolean,
      poc: String,
      project: String,
      subject_type: String,
    },
    data() {
      return {
        active_file: {
            name: null,
            content: null,
            should_update_server: true,
        },
        active_folder: null,
        active_poc: {
            name: null,
            tree: null,
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
          new_folder: null,
          new_file: null,
          selected_folder: null,
          selected_file: null,
        },
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
      },
      poc_api_path() {
        const poc_name = this.active_poc.name;
        return `/api/poc/${this.subject_type}/${this.project}/${poc_name}/`;
      },
      file_api_path() {
        const poc_name = this.active_poc.name;
        const file_name = this.active_file.name;
        const folder_name = this.active_folder;
        if (folder_name === null) {
          return `/api/poc/${this.subject_type}/${this.project}/${poc_name}/${file_name}/`;
        } else {
          return `/api/poc/${this.subject_type}/${this.project}/${poc_name}/${file_name}/${folder_name}/`;
        }
      }
    },
    methods: {
      set_active_file(folder_name, file_name) {
        this.active_file.name = file_name;
        this.active_folder = folder_name;
        axios.get(this.file_api_path)
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
          const data = {
            "content": this.editor.session.getValue()
          };
          axios.post(this.file_api_path, data)
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
      update_poc_tree() {
        axios.get(this.poc_api_path)
        .then((res) => {
          if (res.data.status === "OK") {
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
      add_folder() {
        const folder_name = this.dialog.new_folder;
        axios.post(this.poc_api_path, {
          "folder_name": folder_name,
          "file_name": null,
        })
        .then((res) => {
          if (res.data.status === "OK") {
            this.update_poc_tree();
            this.dialog.folder_name = null;
          } else {
            alert(res.data.msg);
          }
        })
        .catch(() => {

        });
      },
      add_file() {
        const folder_name = this.dialog.selected_folder;
        const file_name = this.dialog.new_file;
        axios.post(this.poc_api_path, {
          "folder_name": folder_name,
          "file_name": file_name,
        })
        .then((res) => {
          if (res.data.status === "OK") {
            this.update_poc_tree();
            this.dialog.selected_folder = null;
            this.dialog.new_file = null;
          } else {
            alert(res.data.msg);
          }
        })
        .catch(() => {

        });
      },
      add_script() {
        const url = `${this.poc_api_path}script.cmd/`;
        axios.post(url)
        .then(() => {
          this.update_poc_tree();
        })
        .catch(() => {

        });
      },
      remove_file_or_folder() {
        const folder_name = this.dialog.selected_folder;
        const file_name = this.dialog.selected_file;
        axios.delete(this.poc_api_path, {
          data: {
            "folder_name": folder_name,
            "file_name": file_name,
          }
        })
        .then((res) => {
          if (res.data.status === "OK") {
            this.update_poc_tree();
            this.dialog.selected_folder = null;
            this.dialog.selected_file = null;
          } else {
            alert(res.data.msg);
          }
        })
        .catch(() => {

        });
      },
    },
    mounted() {
      ace.config.set('basePath', '/node_modules/ace-builds/src-min-noconflict');
      this.editor = ace.edit("editor");
      this.editor.session.addEventListener("change", this.update_file_content);
    },
    watch: {
      "darkMode": function(val) {
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
        this.active_poc.name = val;
        this.update_poc_tree();
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
    <div v-if="this.active_poc.tree === null" class="basis-4/12 w-1/12 h-full pr-6">
      Select an experiment in the Experiments pane to edit it here.
    </div>
    <div v-else class="basis-4/12 w-1/12 h-full grow overflow-y-auto">
      <ul class="relative flex flex-col text-gray-700 bg-white shadow-md w-96 rounded-md bg-clip-border dark:bg-dark-3 dark:text-white">
        <nav class="flex min-w-[240px] h-full flex-col gap-1 p-2 font-sans text-base font-normal text-blue-gray-700">
        <!-- Root files -->
        <li v-for="file in active_poc.tree.files.sort((a, b) => a.name.localeCompare(b.name))" :key="file.name">
          <div
            class="group flex p-2 mb-2 hover:bg-gray-100 hover:bg-opacity-80 hover:text-blue-gray-900 hover:cursor-pointer focus:bg-blue-gray-50 focus:bg-opacity-80 focus:text-blue-gray-900"
            role="button"
            @click="set_active_file(null, file.name)">
            <span class="truncate">{{ file.name }}</span>
            <!-- Remove button -->
            <div
              class="ml-auto button shrink-0 rounded text-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
              @click="this.dialog.selected_file = file.name"
              onclick="remove_file_or_folder_dialog.showModal()">
              ✕
            </div>
          </div>
        </li>
        <!-- Folders -->
        <div v-for="subfolder in active_poc.tree.subfolders.sort((a, b) => a.name.localeCompare(b.name))" :key="subfolder.name">
          <li class="flex group border-b-2 mb-2">
            <div class="font-bold m-2 focus:bg-blue-gray-50 focus:bg-opacity-80 focus:text-blue-gray-900">
            {{ subfolder.name }}
            </div>
            <div class="ml-auto button m-1 opacity-0 group-hover:opacity-100 transition-opacity"
            @click="dialog.selected_folder = subfolder.name"
            onclick="add_file_dialog.showModal()">
              +
            </div>
            <!-- Remove button -->
            <div
              class="button m-1 opacity-0 group-hover:opacity-100 transition-opacity"
              @click="this.dialog.selected_folder = subfolder.name"
              onclick="remove_file_or_folder_dialog.showModal()">
              ✕
            </div>
          </li>
          <div>
            <!-- Files in subfolder -->
            <li v-for="file in subfolder.files.sort((a, b) => a.name.localeCompare(b.name))" :key="file.name">
              <div class="group relative flex items-center p-2 mb-2
                          hover:bg-gray-100 hover:bg-opacity-80 hover:text-blue-gray-900">
                <div
                  class="flex-grow hover:cursor-pointer focus:bg-blue-gray-50 focus:bg-opacity-80 focus:text-blue-gray-900"
                  role="button"
                  @click="set_active_file(subfolder.name, file.name)">
                  {{ file.name }}
                </div>
                <!-- Remove button -->
                <div
                  class="ml-auto button shrink-0 rounded text-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
                  @click="this.dialog.selected_file = file.name, this.dialog.selected_folder = subfolder.name"
                  onclick="remove_file_or_folder_dialog.showModal()">
                  ✕
                </div>
              </div>
            </li>
          </div>
        </div>
          <div class="flex flex-row justify-between">
            <li role="button" class="button text-center w-full mr-1" onclick="add_folder_dialog.showModal()">
              Add folder
            </li>
            <li role="button" class="button text-center w-full mr-1" onclick="add_file_dialog.showModal()">
              Add root file
            </li>
          </div>
        </nav>
      </ul>
    </div>
    <div id="editor" class="basis-8/12"></div>
  </div>

  <!-- Add folder dialog -->
  <dialog id="add_folder_dialog" class="dialog">
    <form method="dialog" @submit="add_folder">
      <p>
        <label>
          <div class="py-2">Folder name:</div>
          <input type="text" id="new_folder" class="input-box" v-model="dialog.new_folder" required />
        </label>
      </p>
      <div class="flex pt-3">
        <input class="button m-2 w-full" type="submit" value="Add folder">
        <input class="button m-2" type="button" value="Cancel" onclick="add_folder_dialog.close()">
      </div>
    </form>
  </dialog>

  <!-- Add file dialog -->
  <dialog id="add_file_dialog" class="dialog">
    <form method="dialog" @submit="add_file">
      <p>
        <div class="py-2">File name:</div>
        <input type="text" id="page" class="input-box" v-model="dialog.new_file" required />
      </p>
      <div class="flex pt-3">
        <input class="button m-2 w-full" type="submit" value="Add file">
        <input class="button m-2" type="button" value="Cancel" onclick="add_file_dialog.close()">
      </div>
    </form>
  </dialog>

  <!-- Add file dialog -->
  <dialog id="remove_file_or_folder_dialog" class="dialog">
    <form method="dialog" @submit.prevent="remove_file_or_folder">
      <p
        v-if="this.dialog.selected_folder !== null && this.dialog.selected_file !== null"
        class="py-2">
        Remove <b>{{ this.dialog.selected_folder }}/{{ this.dialog.selected_file }}</b>?
      </p>
      <p
        v-else-if="this.dialog.selected_folder !== null"
        class="py-2">
        Remove folder <b>{{ this.dialog.selected_folder }}</b> and all its contents?
      </p>
      <p
        v-else
        class="py-2">
        Remove file <b>{{ this.dialog.selected_file }}</b>?
      </p>

      <div class="flex pt-3 gap-2">
        <button type="submit"
          class="button m-2 w-full bg-red-600 text-white"
          onclick="remove_file_or_folder_dialog.close()">
          Confirm
        </button>
        <button type="button" class="button m-2"
          onclick="remove_file_or_folder_dialog.close()"
          @click="this.dialog.selected_folder = null, this.dialog.selected_file = null">
          Cancel
        </button>
      </div>
    </form>
  </dialog>

</template>
