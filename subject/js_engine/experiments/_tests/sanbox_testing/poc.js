// bughog_runtime_flags: --allow-natives-syntax --sandbox-testing
// bughog_expected_output: AddressSanitizer

print('bughog_sanity_check=ok');

// Agnostic V8 Sandbox Escape Target Selection
let targetAddress;
if (typeof Sandbox === 'object' && 'targetPage' in Sandbox) {
    // OLD MODE: V8 requires writing to this specific page to prove escape
    targetAddress = Sandbox.targetPage;
    console.log("[+] Detected legacy Sandbox testing API. Target:", targetAddress);
} else {
    // NEW MODE: Any OOB write causes a crash caught by the sandbox filter
    // 0x41414141 is a safe bet for an unmapped address outside the 1TB sandbox
    targetAddress = 0x41414141n; 
    console.log("[+] Detected modern crash-based verification. Target:", targetAddress);
}