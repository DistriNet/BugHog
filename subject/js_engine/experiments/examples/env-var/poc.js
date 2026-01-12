// bughog_env_vars: ASAN_OPTIONS=verbosity=1
// bughog_expected_output: exited
%DebugPrint("bughog_sanity_check=ok");
print('V8 version: ' + version());
