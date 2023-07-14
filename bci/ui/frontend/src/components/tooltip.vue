<script>
  export default {
    data() {
      return {
        tooltips: {
          "bin_seq": {
            "tooltip": "Perform a general sweep over the evaluation range. Experiment outcomes will not influence the selection of the next revision to evaluate."
          },
          "bin_search": {
            "tooltip": "Perform a focused search to identify either an introducing or fixing revision. Should only be performed within a range where a shift in reproducibility has been observed."
          },
          "comp_search": {
            "tooltip": "Combines the two strategies above. First, a general sweep is performed until the sequence limit is reached. Then, for each shift in reproducibility that can be observed, a targeted search is conducted to identify an introducing or fixing revision."
          },
          "mech_id": {
            "tooltip": "Experiments can have one or more boolean outcomes. Each outcome is identified by a reproduction ID, which is linked to a boolean value indicating reproducibility. In most cases, experiments have only one outcome, and the reproduction ID is set to be the same as the experiment ID by default."
          },
          "request_or_cookie": {
            "tooltip": "TBD"
          },
          "sequence_limit": {
            "tooltip": "Specify the maximum number of revisions to be evaluated in the general sweep."
          },
        }
      }
    }
  };
</script>

<template>
  <div class="tooltip pl-1">
    <v-icon name="md-infooutline" scale=".8"/>
    <span class="tooltiptext"> {{ this.tooltips[$attrs.tooltip].tooltip }}</span>
  </div>
</template>
