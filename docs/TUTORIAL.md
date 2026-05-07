# BugHog tutorial

Whether you're a seasoned bug hunter or just starting out, this tutorial will help you get a hold of the **BugHog basics**. By the end, you will have utilized BugHog to identify the lifecycle of a publicly disclosed bug, leveraging its *proof of concept* across more than 100 automated experiments.

**Estimated Time**: 30 minutes.

## Prerequisites

- Docker installed and running.
- Internet connection.
- A UNIX-based system (Linux, macOS, or WSL on Windows).

## 1. Obtaining BugHog 🐗

First, clone the repository and start BugHog:

```bash
git clone https://github.com/DistriNet/BugHog.git
cd BugHog

# Pull pre-built images and start BugHog
./scripts/deploy.sh
```

Access the BugHog Web UI at [http://localhost](http://localhost).

## 2. Preparing the adventure! 🚀

As you explore the world of web browsers, you stumble upon an intriguing artifact: a [dead bug](https://issues.chromium.org/issues/40095297) in Chromium. This bug acts as a bypass for the Content Security Policy (CSP) by allowing navigation to a `javascript:` URI that loads an external image, even when `img-src 'self'` is set.

BugHog will help us answer: *Where did the bug come from? How long has it been around? Is it truly deceased?*

## 3. Using BugHog for analysis 🔬

1. **Selecting the Experiment**:
   - In the Web UI, select `web_browser` as the **Subject type** in the dropdown menu in the top bar.
   - Select **Subject**: `chromium`.
   - Make sure the **Deep search** checkbox is unchecked.
   - Select the project `examples` in the **Experiments** dropdown menu.
   - Select experiment `csp-image-src` from the experiment list.

2. **Starting the Bisection**:
   - Press the green **Start evaluation** button.
   - BugHog will now start downloading and running various versions of Chromium to test the PoC.

3. **Analyzing Results**:
   As the experiments complete, you will see a timeline of results:
   - `v20 - v25`: CSP not supported.
   - `v26 - v39`: Bug not present.
   - `v40 - v62`: **Buggy!**
   - `v63 - v73`: Fixed.
   - `v74 - v91`: **Reintroduced!**
   - `v92 - ...`: Fixed again.

## 4. Targeted tracking 🎯

If you want to find the *exact* commit that introduced the bug, you can use **Deep Search**:

- Tick the **Deep search** box in the UI and start the evaluation again.
- This will evaluate revision binaries (individual commits) instead of just release versions.
- You can identify the exact revision (e.g., Revision 294410) that introduced the bug. In this case, it was a "Blink roll" intended to fix another vulnerability.

## Next steps

Now that you've completed the tutorial, you can try:
- Writing your own PoC.
- Exploring other [Configuration Options](/docs/CONFIGURATION.md).
- Learning more about [Experiment Parameters](/docs/experiments/README.md).
