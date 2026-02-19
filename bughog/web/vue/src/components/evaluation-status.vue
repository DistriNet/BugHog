<script>
  export default {
    props: {
      server_info: Object
    },
    methods: {
      get_emoji(evaluation_state) {
        if (evaluation_state === 'active') {
          return "🟢";
        } else if (evaluation_state === 'pending') {
          return "🕖";
        } else if (evaluation_state === 'done') {
          return "🏁";
        }
      },
    }
  };
</script>

<template>
  <div class="tooltip pl-1">
    <ul class="my-3">
      <li v-if="this.server_info.state.status === 'running'" class="flex">
        <b class="pr-1">Status:</b>
        <div class="pr-1">Running</div>
        <div v-if="this.server_info.state.nb_of_running_containers !== undefined" class="pr-1">({{ this.server_info.state.nb_of_running_containers }})</div>
        <div>&#x2705;</div>
      </li>
      <li v-else-if="this.server_info.state.status === 'waiting_to_stop'" class="flex">
        <b class="pr-1">Status:</b>
        <div class="pr-1">Stopping...</div>
        <div v-if="this.server_info.state.nb_of_running_containers !== undefined" class="pr-1">({{ this.server_info.state.nb_of_running_containers }})</div>
        <div>&#x231B;</div>
      </li>
      <li v-else class="flex">
        <b class="pr-1">Status:</b>
        <div class="pr-1">Idle</div>
        <div v-if="this.server_info.state.reason === 'finished'" class="pr-1">(all binaries evaluated)</div>
        <div v-if="this.server_info.state.reason === 'user'" class="pr-1">(stopped by user)</div>
        <div>&#x1F6D1;</div>
      </li>
    </ul>
    <span v-if="this.server_info.state.queue" class="tooltiptext">
      <ul v-for="evaluation in this.server_info.state.queue">
        <li>{{get_emoji(evaluation['state'])}} {{ evaluation['experiment'] }}</li>
      </ul>
    </span>
  </div>
</template>
