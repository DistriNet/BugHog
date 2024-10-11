<script>
  export default {
    data() {
      return {
        tooltips: {
          "bgb_sequence": {
            "tooltip": "Binaries are selected uniformly over the specified evaluation range. Experiment outcomes do not influence the next binary to be evaluated."
          },
          "bgb_search": {
            "tooltip": "Perform a search to identify either an introducing or fixing revision. This should only be performed within a range where one shift in reproducibility has been observed."
          },
          "comp_search": {
            "tooltip": "Combines the two strategies above. First, binaries are selected uniformly over the evaluation range, until the sequence limit is reached. Then, for each shift in reproducibility that can be observed, a search is conducted to identify the introducing or fixing binary."
          },
          "deep_search": {
            "tooltip": "Opt to evaluate at the revision level to pinpoint code changes that introduced or fixed a bug. If unchecked, only browser releases (or base positions of releases in the case of Chromium) will be analyzed."
          },
          "mech_id": {
            "tooltip": "Experiments can have one or more boolean outcomes. Each outcome is identified by a reproduction ID, which is linked to a boolean value indicating reproducibility. In most cases, experiments have only one outcome, and the reproduction ID is set to be the same as the experiment ID by default."
          },
          "request_or_cookie": {
            "tooltip": "TBD"
          },
          "sequence_limit": {
            "tooltip": "Specify the maximum number of binaries to be evaluated during the binary sequence stage."
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
