<script>
  export default {
    data() {
      return {
        sections: {
          "automation": {
            "title": "Browser automation",
            "tooltip": "Choose the method for instructing browser binaries. Currently, only command line instructions are supported."
          },
          "browser_config": {
            "title": "Browser configuration",
            "tooltip": "Specify custom browser settings, installed extensions and CLI flags that will be applied to all evaluated binaries. Please note that these settings depend on the selected browser."
          },
          "browser_rev_range": {
            "title": "Browser revision range",
            "tooltip": "Define a binary range based on revision numbers. The browser version range defined above will be disregarded if this option is used."
          },
          "db_collection": {
            "title": "Database collection",
            "tooltip": "The evaluation results will be stored in the specified MongoDB database collection. The prefix for the collection name is fixed and is determined based on the selected project and browser. Additionally, you can choose a custom suffix for the collection name. The prefix and suffix will be appended with an underscore to form the final collection name."
          },
          "eval_range": {
            "title": "Browser version range",
            "tooltip":
              "Specify which binaries you want to evaluate by selecting the browser and its version range. Enabling deep search extends the evaluation to include all available revision binaries, offering a more comprehensive analysis."
          },
          "eval_settings": {
            "title": "Evaluation settings",
            "tooltip": "Customize the evaluation process by selecting the search strategy, sequence limit and the number of parallel containers."
          },
          "experiments": {
            "title": "Experiments",
            "tooltip": "Pick a project from the dropdown menu to access all available experiments. Then, mark the experiments you wish to conduct. Keep in mind that if multiple experiments are chosen, only a binary sequence will be performed. For a binary search or composite search, select only one experiment."
          },
          "parallel_containers": {
            "title": "Number of parallel containers",
            "tooltip": "Specify the maximum number of concurrent containers allowed to run. To disable concurrency, simply input '1'."
          },
          "reproduction_id": {
            "title": "Reproduction id",
            "tooltip": "This option will be deprecated. Experiments can have one or more boolean outcomes. Each outcome is identified by a reproduction ID, which is linked to a boolean value indicating reproducibility. In most cases, experiments have only one outcome, and the reproduction ID is set to be the same as the experiment ID by default."
          },
          "results": {
            "title": "Results",
            "tooltip": "Choose an experiment from the dropdown menu to visualize its results in the Gantt chart below. Squares represent (approximate) release binaries, while dots represent revision binaries. Clicking on a dot will open the web page for the associated revision in the public browser repository."
          },
          "search_strategy": {
            "title": "Search strategy",
            "tooltip": "Select a search strategy. Additional information on each specific search strategy is available with each option."
          }
        }
      }
    }
  };
</script>

<template>
<div class="flex flex-wrap w-full justify-between">
  <h2 class="form-section-title">{{ this.sections[$attrs.section].title }}</h2>
  <!-- Tooltip -->
  <div v-if="this.sections[$attrs.section].tooltip !== undefined" class="tooltip text-right pl-3">
    <v-icon name="md-infooutline" class=""/>
    <span v-if="$attrs.left !== undefined" class="tooltiptext-left"> {{ this.sections[$attrs.section].tooltip }}</span>
    <span v-else class="tooltiptext"> {{ this.sections[$attrs.section].tooltip }}</span>
  </div>
</div>
</template>
