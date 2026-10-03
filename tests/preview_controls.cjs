// Execute the actual generated handler with controlled clipboard/DOM responses.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const page = fs.readFileSync(process.argv[2], 'utf8');
const mode = process.argv[3];
const payload = page.match(/<script id="body-source" type="application\/json">([\s\S]*?)<\/script>/)[1];
const controls = page.match(/<script>([\s\S]*?)<\/script>/)[1];
const original = JSON.parse(payload);
const nodes = {};
for (const id of ['body-source', 'source-box', 'source-panel', 'copy-status', 'select-source', 'copy-source']) {
  nodes[id] = {
    value: '', open: false, handlers: {},
    addEventListener(event, handler) { this.handlers[event] = handler; },
    focus() { this.focused = true; }, select() { this.selected = true; },
    setSelectionRange(start, end) { this.selection = [start, end]; },
  };
}
nodes['body-source'].textContent = payload;
const writes = [];
const navigator = mode === 'unavailable' ? {} : { clipboard: {
  async writeText(value) { writes.push(value); if (mode === 'rejected') throw new Error('permission denied'); },
}};
vm.runInNewContext(controls, { document: { getElementById: id => nodes[id] }, navigator });
(async () => {
  assert.equal(nodes['source-box'].value, original);
  await nodes['copy-source'].handlers.click();
  if (mode === 'success') {
    assert.deepEqual(writes, [original]);
    assert.match(nodes['copy-status'].textContent, /복사했습니다/);
    assert.equal(nodes['source-panel'].open, false);
  } else {
    assert.equal(nodes['source-panel'].open, true);
    assert.equal(nodes['source-box'].selected, true);
    assert.deepEqual(Array.from(nodes['source-box'].selection), [0, original.length]);
    assert.match(nodes['copy-status'].textContent, /Ctrl\+C/);
  }
  nodes['select-source'].handlers.click();
  assert.equal(nodes['source-box'].selected, true);
})().catch(error => { console.error(error); process.exitCode = 1; });
