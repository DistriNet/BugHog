import { reactive, watch } from 'vue';

const persisted_general_params = [
  'nb_of_containers',
  'only_release_commits',
  'sequence_limit',
];

const persisted_subject_type_specific_params = [
  'project_name',
  'subject_name',
];

const DEFAULT_EVAL_PARAMS = {
  subject_type: null,
  subject_name: null,
  project_name: null,
  subject_setting: 'default',
  cli_options: [],
  extensions: [],
  experiments: [],
  version_range: [-1, -1],
  lower_commit_nb: null,
  upper_commit_nb: null,
  only_release_commits: true,
  nb_of_containers: null,
  sequence_limit: 50,
  target_mech_id: null,
  search_strategy: 'comp_search',
  experiment_to_plot: null,
};

function getFromLocalStorage(param_name) {
  var param_value = localStorage.getItem(param_name);
  // LocalStorage only stores strings, so we will convert stringified booleans to actual booleans.
  if (param_value === 'true') {
    return true;
  } else if (param_value === 'false') {
    return false;
  }
  return param_value;
}

function loadPersistedParams() {
  var loaded_eval_params = {};

  // Load general params.
  let param_value;
  for (const param_name of persisted_general_params) {
    if (process.env.NODE_ENV === "development") {
      param_value = getFromLocalStorage(`dev_${param_name}`);
    } else {
      param_value = getFromLocalStorage(param_name)
    }
    if (param_value !== null) {
      loaded_eval_params[param_name] = param_value;
    }
  }

  // Load subject type specific params.
  const selected_subject_type = localStorage.getItem('selected_subject_type');
  if (selected_subject_type === null) {
    console.debug(`No selected subject type.`);
    return { ...DEFAULT_EVAL_PARAMS, ...loaded_eval_params };
  }

  const stored_eval_params_raw = localStorage.getItem(`eval_params_${selected_subject_type}`);
  if (stored_eval_params_raw === null) {
    console.debug(`No eval params stored for ${selected_subject_type}.`)
    return { ...DEFAULT_EVAL_PARAMS, 'subject_type': selected_subject_type, ...loaded_eval_params };
  }

  const stored_eval_params = JSON.parse(stored_eval_params_raw);
  console.debug(`Loading eval params for ${selected_subject_type}.`)
  return { ...DEFAULT_EVAL_PARAMS, ...stored_eval_params, 'subject_type': selected_subject_type, ...loaded_eval_params };
}

export function useEvalParams() {
  var evalParams = reactive(loadPersistedParams());

  watch(evalParams, (new_params) => {
    // Store general params.
    for (const param_name of persisted_general_params) {
      if (localStorage.getItem(param_name) !== new_params[param_name]) {
        if (process.env.NODE_ENV === "development") {
          localStorage.setItem(`dev_${param_name}`, new_params[param_name]);
        } else {
          localStorage.setItem(param_name, new_params[param_name]);
        }
      }
    }

    // Store subject type specific params.
    const old_selected_subject_type = localStorage.getItem('selected_subject_type');
    var old_params = localStorage.getItem(`eval_params_${new_params.subject_type}`);

    if (new_params.subject_type === null) {
      return;
    } else if (old_params === null) {
      const default_params = Object.fromEntries(
        Object.entries(DEFAULT_EVAL_PARAMS).filter(([key]) => persisted_subject_type_specific_params.includes(key))
      );
      Object.assign(evalParams, default_params);
      localStorage.setItem(`eval_params_${new_params.subject_type}`, JSON.stringify(default_params))
    } else {
      old_params = JSON.parse(old_params);
    }

    if (new_params.subject_type !== old_selected_subject_type) {
      console.log(`Updating stored selected subject type from ${old_selected_subject_type} to ${new_params.subject_type}.`);
      localStorage.setItem('selected_subject_type', new_params.subject_type);
      if (old_params !== null) {
        persisted_subject_type_specific_params.forEach(key => {
          evalParams[key] = old_params[key];
        });
      }
    } else {
      var params_to_store = {}
      persisted_subject_type_specific_params.forEach(key => {
        if (new_params[key] !== old_params[key]) {
          console.log(`Updating stored ${key} from ${old_params[key]} to ${new_params[key]}`);
        }
        params_to_store[key] = new_params[key];
      });
      localStorage.setItem(`eval_params_${new_params.subject_type}`, JSON.stringify(params_to_store));
    }
  }, { deep: true });

  function resetEvalParams() {
    Object.assign(evalParams, { ...DEFAULT_EVAL_PARAMS })
    localStorage.removeItem('eval_params_persisted')
  }

  console.log("Eval params has been initialized.")

  return {
    evalParams,
    resetEvalParams,
  }
}
