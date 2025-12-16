let isRecording = false;
let recordedSteps = [];
let stopPlayback = false;

const playbackDelayMs = 600;

const listeners = {
  click: (event) => recordStep(event, 'click'),
  change: (event) => recordInput(event, 'change'),
  input: (event) => recordInput(event, 'input'),
  submit: (event) => recordStep(event, 'submit'),
};

function getUniqueSelector(element) {
  if (!element) return null;
  if (element.id) return `#${CSS.escape(element.id)}`;

  const parts = [];
  let node = element;
  while (node && node.nodeType === Node.ELEMENT_NODE && node.tagName.toLowerCase() !== 'html') {
    let selector = node.tagName.toLowerCase();
    if (node.className) {
      const classes = Array.from(node.classList).map((c) => `.${CSS.escape(c)}`);
      if (classes.length) selector += classes.join('');
    }

    const siblings = Array.from(node.parentNode?.children || []).filter((n) => n.tagName === node.tagName);
    if (siblings.length > 1) {
      const index = siblings.indexOf(node) + 1;
      selector += `:nth-of-type(${index})`;
    }

    parts.unshift(selector);
    node = node.parentElement;
  }

  return parts.join(' > ');
}

function recordStep(event, type) {
  if (!isRecording) return;
  const selector = getUniqueSelector(event.target);
  if (!selector) return;

  const step = { type, selector, timestamp: Date.now() };
  recordedSteps.push(step);
  chrome.runtime.sendMessage({ type: 'recordedStep', step });
}

function recordInput(event, type) {
  if (!isRecording) return;
  const selector = getUniqueSelector(event.target);
  if (!selector) return;

  const value = event.target.value;
  const step = { type, selector, value, timestamp: Date.now() };
  recordedSteps.push(step);
  chrome.runtime.sendMessage({ type: 'recordedStep', step });
}

function addListeners() {
  Object.entries(listeners).forEach(([event, handler]) => {
    window.addEventListener(event, handler, true);
  });
}

function removeListeners() {
  Object.entries(listeners).forEach(([event, handler]) => {
    window.removeEventListener(event, handler, true);
  });
}

async function playSteps(steps = []) {
  stopPlayback = false;
  for (const step of steps) {
    if (stopPlayback) return;
    const element = document.querySelector(step.selector);
    if (!element) continue;

    if (step.type === 'click') {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      await wait(playbackDelayMs / 2);
      element.click();
    } else if (step.type === 'input' || step.type === 'change') {
      element.focus();
      element.value = step.value ?? '';
      element.dispatchEvent(new Event('input', { bubbles: true }));
      element.dispatchEvent(new Event('change', { bubbles: true }));
    } else if (step.type === 'submit') {
      element.dispatchEvent(new Event('submit', { bubbles: true }));
    }

    await wait(playbackDelayMs);
  }
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  switch (message.type) {
    case 'startRecording':
      recordedSteps = [];
      isRecording = true;
      addListeners();
      sendResponse?.({ ok: true });
      break;
    case 'stopRecording':
      isRecording = false;
      removeListeners();
      sendResponse?.({ ok: true, steps: recordedSteps });
      break;
    case 'playSteps':
      playSteps(message.steps);
      sendResponse?.({ ok: true });
      break;
    case 'cancelPlayback':
      stopPlayback = true;
      sendResponse?.({ ok: true });
      break;
    default:
      break;
  }
});
