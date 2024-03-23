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
            "tooltip": "Specify a browser range based on revision numebers. The browser version range will be ignored if this is set."
          },
          "db_collection": {
            "title": "Database collection",
            "tooltip": "The evaluation results will be stored in the specified MongoDB database collection. The prefix for the collection name is fixed and is determined based on the selected project and browser. Additionally, you can choose a custom suffix for the collection name. The prefix and suffix will be appended with an underscore to form the final collection name."
          },
          "eval_range": {
            "title": "Browser version range",
            "tooltip":
              "Specify the scope of revisions to be evaluated by setting the boundaries using either browser release version numbers or revision numbers."
          },
          "eval_settings": {
            "title": "Evaluation settings",
            "tooltip": "Customize the evaluation process by selecting the automation mode, search strategy, and the number of parallel containers."
          },
          "experiments": {
            "title": "Experiments",
            "tooltip": "Choose the experiments to be conducted. All available experiments within the selected project are shown here. Note that if multiple experiments are chosen, binary search and composite search will only target the experiment of which the reproduction id is provided."
          },
          "parallel_containers": {
            "title": "Number of parallel containers",
            "tooltip": "Specify the number of concurrent containers allowed to run for evaluating each revision binary. To disable concurrency and conduct all experiments in the main container, enter '1'. This will prevent new containers from being spawned during the evaluation process."
          },
          "reproduction_id": {
            "title": "Reproduction id",
            "tooltip": "Experiments can have one or more boolean outcomes. Each outcome is identified by a reproduction ID, which is linked to a boolean value indicating reproducibility. In most cases, experiments have only one outcome, and the reproduction ID is set to be the same as the experiment ID by default."
          },
          "results": {
            "title": "Results",
            "tooltip": "The evaluation results can be visualized in a Gantt chart. This chart is generated based on the selected fields. Use the dropdown menu to choose the experiment for which you want to display the data. Be sure to input the reproduction ID as well, as this is used to infer the boolean outcome for each revision. Note that the zoom level within the Gantt chart widget will reset each time the chart is refreshed."
          },
          "search_strategy": {
            "title": "Search strategy",
            "tooltip": "Configure the evaluation to perform either a general sweep on revision binaries, a targeted search for introductions and fixes, or a combination of the two."
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
