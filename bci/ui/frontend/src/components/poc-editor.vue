<script>
  import ace from "ace-builds";
  import 'ace-builds/src-min-noconflict/ext-modelist';
  import axios from 'axios';
  export default {
    props: {
      available_domains: Array,
      darkmode: Boolean,
      experiment: String,
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
            name: null,
            active_domain: null,
            active_path: null,
            tree: {},
            // Example tree:
            // {
            //   'test.com': {
            //     "path1": ["file1", "file2"],
            //     "path2": ["file1"],
            //   },
            //   'not.test': {
            //     "path1": ["file1", "file2"],
            //     "path2": ["file1"],
            //   },
            // },
        },
        available_file_types: [
          'html',
          'js',
        ],
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
        editor: null,
        timeout: null,
      }
    },
    methods: {
      set_active_file(domain, file_path, file_name) {
        this.active_poc.active_domain = domain;
        this.active_poc.active_path = file_path;
        this.active_file.name = file_name;
        const project = this.project;
        const poc = this.active_poc.name;
        const path = `http://${location.hostname}:5000/api/poc/${project}/${poc}/${domain}/${file_path}/${file_name}/`;
        axios.get(path)
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
          const path = `http://${location.hostname}:5000/api/poc/${project}/${poc}/${domain}/${file_path}/${file_name}/`;
          axios.post(path, {"content": this.editor.session.getValue()})
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
      update_editor_mode(file_name) {
        file_ext = file_name.split('.').pop();
        switch (file_ext) {
          case "html":
            this.editor.session.setMode("ace/mode/html");
            break;
          case "js":
            this.editor.session.setMode("ace/mode/js");
            break;
        }
      },
      add_page() {
        const url = `http://${location.hostname}:5000/api/poc/${this.project}/${this.experiment}/`;
        axios.post(url, {
          "domain": this.dialog.domain.name,
          "page": this.dialog.page.name,
          "file_type": this.dialog.file.type,
        })
        .then(() => {
          
        })
        .catch(() => {

        });
        this.dialog.domain.name = null;
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
      "experiment": function(val) {
        this.active_poc.name = val;
        this.editor.setValue();
        this.editor.clearSelection();
        const path = `http://${location.hostname}:5000/api/poc/${this.project}/${val}/`;
        axios.get(path)
        .then((res) => {
          if (res.data.status === "OK") {
            this.active_poc.tree = res.data.tree;
          }
        })
        .catch((error) => {
          console.error(error);
        });
      },
    },
  };
</script>
<style>
  #editor {
      position: relative;
      height: 400px;
  }
</style>
<template>
  <div class="flex flex-row">
    <div v-if="this.active_poc.name == null" class="basis-4/12 w-1/12 h-full pr-6">
      Select an experiment in the Experiments pane to edit it here.
    </div>
    <div v-else class="basis-4/12 w-1/12 h-full">
      <ul class="relative flex flex-col text-gray-700 bg-white shadow-md w-96 rounded-md bg-clip-border">
        <nav class="flex min-w-[240px] h-full flex-col gap-1 p-2 font-sans text-base font-normal text-blue-gray-700">
          <li v-for="([domain, pages, index]) in Object.entries(active_poc.tree)">
            <ul>
              <li v-for="([path, files, index]) in Object.entries(pages)">
                <div class="flex border-b-2 p-2 font-bold">
                  <div class="w-full">
                    {{ domain }}/{{ path }}
                  </div>
                  <div role="button" onclick="create_file_dialog.showModal()">+</div>
                </div>
                <ul>
                  <li v-for="file in files">
                    <div
                      role="button"
                      class="flex items-center indent-4 w-full p-2 hover:bg-gray-100 hover:bg-opacity-80 hover:text-blue-gray-900 hover:cursor-pointer focus:bg-blue-gray-50 focus:bg-opacity-80 focus:text-blue-gray-900"
                      @click="set_active_file(domain, path, file)"
                    >
                      {{ file }}
                    </div>
                  </li>
                </ul>
              </li>
            </ul>
          </li>
          <li role="button" class="text-center p-1 bg-blue-200" onclick="create_domain_dialog.showModal()">
            Add domain
          </li>
        </nav>
      </ul>
    </div>
    <div id="editor" class="basis-8/12"></div>
  </div>

  <!-- Create domain dialog -->
  <dialog id="create_domain_dialog" class="p-2">
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
          <input type="text" id="page" v-model="dialog.page.name" required />

          <div class="py-2">Choose file type:</div>
          <select name="file" id="file" v-model="dialog.file.type" required>
            <option v-for="file_type in available_file_types" :value="file_type">
              {{ file_type }}
            </option>
          </select>
        </label>
      </p>
      <div class="flex pt-3">
        <input class="button m-2" type="submit" value="Add domain">
        <input class="button m-2" type="button" value="Cancel" onclick="create_domain_dialog.close()">
      </div>
    </form>
  </dialog>
</template>
