import { reactive, watch } from 'vue';

const DEFAULT_EVAL_PARAMS = {
  subject_type: null,
  subject_name: null,
  project_name: null,
  subject_setting: 'default',
  cli_options: [],
  extensions: [],
  experiments: [],
  version_range: [1, 100],
  lower_commit_nb: null,
  upper_commit_nb: null,
  only_release_commits: true,
  nb_of_containers: 8,
  sequence_limit: 50,
  target_mech_id: null,
  search_strategy: 'comp_search',
  experiment_to_plot: null,
}

function loadPersistedParams() {
  const selected_subject_type = localStorage.getItem('selected_subject_type');
  var eval_params = localStorage.getItem(`eval_params_${selected_subject_type}`);
  if (selected_subject_type === null || eval_params === null) {
    console.log(`No selected subject type.`)
    return { ...DEFAULT_EVAL_PARAMS };
  } else if (eval_params === null) {
    console.log(`Loaded stored selected subject type ${selected_subject_type}.`);
    return { ...DEFAULT_EVAL_PARAMS, ...{ 'subject_type': selected_subject_type } }
  } else {
    eval_params = JSON.parse(eval_params);
    return { ...DEFAULT_EVAL_PARAMS, ...eval_params, ...{ 'subject_type': selected_subject_type } };
  }
}

export function useEvalParams() {
  var evalParams = reactive(loadPersistedParams());

  watch(evalParams, (new_params) => {
    const to_persist = [
      'subject_name',
      'project_name',
    ]
    const old_selected_subject_type = localStorage.getItem('selected_subject_type');
    var old_params = localStorage.getItem(`eval_params_${new_params.subject_type}`);

    if (new_params.subject_type === null) {
      return;
    } else if (old_params === null) {
      const default_params = Object.fromEntries(
        Object.entries(DEFAULT_EVAL_PARAMS).filter(([key]) => to_persist.includes(key))
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
        to_persist.forEach(key => {
          evalParams[key] = old_params[key];
        });
      }
    } else {
      var params_to_store = {}
      to_persist.forEach(key => {
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

  return {
    evalParams,
    resetEvalParams,
  }
}
