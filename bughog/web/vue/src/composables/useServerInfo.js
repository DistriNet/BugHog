import { reactive, computed } from 'vue';

export function useServerInfo() {
  const serverInfo = reactive({
    db_info: {
      host: null,
      connected: false
    },
    logs: [],
    state: {
      is_running: false
    },
  });

  const bannerMessage = computed(() => {
    if (serverInfo.db_info.connected) {
      return `Connected to MongoDB at ${serverInfo.db_info.host}`;
    } else {
      return `Connecting to database...`;
    }
  });

  const updateServerInfo = (data) => {
    if (data.logs) {
      serverInfo.logs = data.logs;
    }

    for (const key in data) {
      if (key === 'logs') continue;
      serverInfo[key] = data[key];
    }
  };

  const addLogEntry = (entry) => {
    serverInfo.logs.push(entry);
  };

  return {
    serverInfo,
    bannerMessage,
    updateServerInfo,
    addLogEntry
  };
}
