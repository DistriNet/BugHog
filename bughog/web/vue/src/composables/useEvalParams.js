import { reactive, watch } from 'vue'

const DEFAULT_EVAL_PARAMS = {
  subject_type: null,
  subject_name: null,
  project_name: null,
  subject_setting: 'default',
  cli_options: [],
  extensions: [],
  experiments: [],
  lower_version: null,
  upper_version: null,
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
  const persisted = localStorage.getItem('eval_params_persisted')
  return persisted ? { ...DEFAULT_EVAL_PARAMS, ...JSON.parse(persisted) } : { ...DEFAULT_EVAL_PARAMS }
}

export function useEvalParams() {
  const evalParams = reactive(loadPersistedParams())

  watch(evalParams, (val) => {
    const persist = {
      subject_type: val.subject_type,
      subject_name: val.subject_name,
      project_name: val.project_name,
      // Add more fields as needed
    }
    localStorage.setItem('eval_params_persisted', JSON.stringify(persist))
  }, { deep: true })

  // Helper: reset parameters to default (if needed)
  function resetEvalParams() {
    Object.assign(evalParams, { ...DEFAULT_EVAL_PARAMS })
    localStorage.removeItem('eval_params_persisted')
  }

  return {
    evalParams,
    resetEvalParams,
  }
}
