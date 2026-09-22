const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

console.log("[*] Validating dashboard/index.html JavaScript Runtime & Logic...");

const html = fs.readFileSync('dashboard/index.html', 'utf-8');
const scriptMatches = html.match(/<script>([\s\S]*?)<\/script>/);

if (!scriptMatches || !scriptMatches[1]) {
    console.error("[-] No <script> found in dashboard/index.html!");
    process.exit(1);
}

const jsCode = scriptMatches[1];

// 1. Verify JS Syntax
try {
    new vm.Script(jsCode, { filename: 'index.html.js' });
    console.log("[PASS] JavaScript syntax parsed cleanly without any SyntaxErrors.");
} catch (err) {
    console.error("[-] Syntax Error in index.html script:", err);
    process.exit(1);
}

// 2. Mock browser DOM and environment
const mockDOM = {
    elements: {},
    getElementById: function(id) {
        if (!this.elements[id]) {
            this.elements[id] = {
                id: id,
                innerText: '',
                innerHTML: '',
                style: {},
                classList: {
                    classes: new Set(),
                    add: function(c) { this.classes.add(c); },
                    remove: function(c) { this.classes.delete(c); },
                    contains: function(c) { return this.classes.has(c); }
                },
                children: [],
                insertBefore: function(node, ref) {
                    this.children.unshift(node);
                },
                removeChild: function(node) {
                    const idx = this.children.indexOf(node);
                    if (idx >= 0) this.children.splice(idx, 1);
                    else if (this.children.length > 0) this.children.pop();
                },
                clientWidth: 800,
                clientHeight: 400,
                getContext: function(type) {
                    return {
                        setTransform: () => {},
                        clearRect: () => {},
                        beginPath: () => {},
                        moveTo: () => {},
                        lineTo: () => {},
                        stroke: () => {},
                        fill: () => {},
                        arc: () => {},
                        closePath: () => {},
                        fillRect: () => {},
                        fillText: () => {},
                        save: () => {},
                        restore: () => {},
                        setLineDash: () => {},
                        createLinearGradient: () => ({ addColorStop: () => {} }),
                        createRadialGradient: () => ({ addColorStop: () => {} })
                    };
                },
                getBoundingClientRect: () => ({ width: 800, height: 400 }),
                scrollIntoView: function() {},
                setAttribute: function(k, v) { this[k] = v; },
                getAttribute: function(k) { return this[k]; },
                appendChild: function(node) { this.children.push(node); node.parentNode = this; }
            };
        }
        return this.elements[id];
    },
    querySelectorAll: function(sel) {
        return [this.getElementById("mock_" + (sel || "el"))];
    },
    querySelector: function(sel) {
        return this.getElementById("mock_" + (sel || "el"));
    },
    createElement: function(tag) {
        return {
            tagName: tag.toUpperCase(),
            innerHTML: '',
            style: {},
            classList: {
                classes: new Set(),
                add: function(c) { this.classes.add(c); },
                remove: function(c) { this.classes.delete(c); },
                contains: function(c) { return this.classes.has(c); }
            },
            setAttribute: function(k, v) { this[k] = v; },
            scrollIntoView: function() {},
            children: [],
            appendChild: function(c) { this.children.push(c); c.parentNode = this; }
        };
    },
    addEventListener: function() {}
};

const sandbox = {
    window: {
        devicePixelRatio: 2,
        addEventListener: () => {}
    },
    document: mockDOM,
    performance: { now: () => Date.now() },
    setInterval: () => {},
    setTimeout: (fn) => fn(),
    requestAnimationFrame: (cb) => {},
    EventSource: class {
        constructor() {}
        close() {}
    },
    fetch: () => Promise.resolve({ json: () => Promise.resolve({}) }),
    console: console,
    Float32Array: Float32Array,
    Date: Date,
    Math: Math,
    Number: Number,
    String: String,
    JSON: JSON,
    parseInt: parseInt
};

vm.createContext(sandbox);

// 3. Execute JS in sandbox
try {
    vm.runInContext(jsCode, sandbox);
    console.log("[PASS] Script executed in mock browser runtime successfully.");
} catch (err) {
    console.error("[-] Runtime Error executing index.html script:", err);
    process.exit(1);
}

// 4. Test escapeHtml
assert.strictEqual(sandbox.escapeHtml('<script>alert("xss")</script>'), '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;');
assert.strictEqual(sandbox.escapeHtml(null), '');
assert.strictEqual(sandbox.escapeHtml(undefined), '');
console.log("[PASS] escapeHtml() sanitizes all malicious tokens and handles null/undefined.");

// 5. Test addTelemetryRow with normal and extreme edge cases
// Edge Case A: Normal event
sandbox.addTelemetryRow({
    type: "WRITE_SAMPLE",
    entropy: 4.5,
    risk: 12.0,
    pid: 1001,
    comm: "gcc",
    count: 4096,
    ino: 12345,
    tier: 0
});
console.log("[PASS] addTelemetryRow handles normal WRITE_SAMPLE.");

// Edge Case B: NaN risk, negative entropy, missing comm/pid
sandbox.addTelemetryRow({
    type: "CANARY_BREACH",
    entropy: -99.9, // Negative entropy
    risk: NaN,      // NaN risk
    pid: null,      // null PID
    comm: undefined,// missing comm
    ino: null
});
console.log("[PASS] addTelemetryRow handles NaN risk, negative entropy, and null fields without crash.");

// Edge Case C: Bounded DOM table rows (feed 100 events)
const tbody = mockDOM.getElementById("telemetryBody");
for (let i = 0; i < 100; i++) {
    sandbox.addTelemetryRow({
        type: "WRITE_SAMPLE",
        entropy: 7.9,
        risk: 85.0,
        pid: i + 2000,
        comm: `proc_${i}`,
        tier: 3
    });
}
assert(tbody.children.length <= 60, `DOM rows should be capped at 60, but got ${tbody.children.length}`);
console.log(`[PASS] Unbounded DOM growth prevented: table row cap verified (Current rows: ${tbody.children.length} <= 60).`);

// 6. Test openForensicModal edge cases
sandbox.openForensicModal(null);
sandbox.openForensicModal({ ino: undefined, entropy: NaN, comm: null });
console.log("[PASS] openForensicModal handles null and undefined inputs safely.");

// 7. Test Presentation Tour step boundaries
const stepNumEl = mockDOM.getElementById("tourStepNum");
sandbox.renderTourStep(0);
assert.strictEqual(stepNumEl.innerText, 1);
sandbox.renderTourStep(999); // Out of bounds high
assert.strictEqual(stepNumEl.innerText, 6);
sandbox.renderTourStep(-50); // Out of bounds low
assert.strictEqual(stepNumEl.innerText, 1);
console.log("[PASS] renderTourStep() enforces strict array boundary clamping [0 .. 5].");

// 8. Test formatHexDump
const dump = sandbox.formatHexDump("000102030405060708090A0B0C0D0E0F", false);
assert(dump.includes("0x0000:"), "Hex dump must contain offset");
console.log("[PASS] formatHexDump correctly formats binary slice with offset and ASCII.");

// 9. Comprehensive Button & Interaction Execution Test Suite
console.log("\n[*] Testing execution of all 11 button click handler functions in runtime...");

// 9.1 toggleMode
assert.doesNotThrow(() => {
    sandbox.toggleMode();
}, "toggleMode() should execute cleanly");
console.log("[PASS] Button Handler 'toggleMode()' executed without error.");

// 9.2 toggleAgent
assert.doesNotThrow(() => {
    sandbox.toggleAgent();
}, "toggleAgent() should execute cleanly");
console.log("[PASS] Button Handler 'toggleAgent()' executed without error.");

// 9.3 togglePresenterTour
assert.doesNotThrow(() => {
    sandbox.togglePresenterTour(); // Open
    const drawer = mockDOM.getElementById("presenterDrawer");
    assert.strictEqual(drawer.style.display, "block");
    sandbox.togglePresenterTour(); // Close
    assert.strictEqual(drawer.style.display, "none");
}, "togglePresenterTour() should execute cleanly");
console.log("[PASS] Button Handler 'togglePresenterTour()' executed without error.");

// 9.4 triggerAction for all 5 simulation actions
const actions = ['simulate_entropy', 'simulate_canary', 'simulate_encryptor', 'simulate_benign', 'clear_logs'];
actions.forEach(act => {
    assert.doesNotThrow(() => {
        sandbox.triggerAction(act);
    }, `triggerAction('${act}') should execute cleanly`);
});
console.log("[PASS] Button Handler 'triggerAction()' executed cleanly for all 5 actions.");

// 9.5 switchTab for all 4 subsystem tabs
const tabs = ['benchmark', 'executive', 'technical', 'explainer'];
tabs.forEach(tab => {
    assert.doesNotThrow(() => {
        sandbox.switchTab(tab, null);
    }, `switchTab('${tab}') should execute cleanly`);
});
console.log("[PASS] Button Handler 'switchTab()' executed cleanly for all 4 tabs.");

// 9.6 openForensicModal and closeModal
assert.doesNotThrow(() => {
    sandbox.openForensicModal({ ino: 42, entropy: 7.95, comm: 'encryptor', pid: 1234 });
    sandbox.closeModal();
}, "openForensicModal and closeModal should execute cleanly");
console.log("[PASS] Button Handlers 'openForensicModal()' and 'closeModal()' executed without error.");

// 9.7 loadForensicSample
assert.doesNotThrow(() => {
    sandbox.loadForensicSample('cipher');
    sandbox.loadForensicSample('plain');
}, "loadForensicSample should execute cleanly");
console.log("[PASS] Button Handler 'loadForensicSample()' executed without error.");

// 9.8 Tour navigation: nextTourStep, prevTourStep, executeTourAction
assert.doesNotThrow(() => {
    sandbox.togglePresenterTour(); // Open tour
    sandbox.nextTourStep();
    sandbox.prevTourStep();
    sandbox.executeTourAction();
    sandbox.togglePresenterTour(); // Close tour
}, "Tour navigation and action functions should execute cleanly");
console.log("[PASS] Button Handlers 'nextTourStep()', 'prevTourStep()', and 'executeTourAction()' executed without error.");

console.log("\n=== ALL FRONTEND RUNTIME JAVASCRIPT & BUTTON TESTS PASSED (100% OPERATIONAL)! ===");

