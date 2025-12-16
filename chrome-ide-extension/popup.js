const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const playBtn = document.getElementById('playBtn');
const saveBtn = document.getElementById('saveBtn');
const refreshBtn = document.getElementById('refreshBtn');
const recordingsList = document.getElementById('recordings');
const statusMessage = document.getElementById('statusMessage');
const recordingNameInput = document.getElementById('recordingName');

async function sendMessage(message) {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return chrome.tabs.sendMessage(tab.id, message).catch(() => {
    // Content script may not be injected if the page is restricted
    setStatus('Unable to communicate with this page');
    return { ok: false };
  });
}

function setStatus(text) {
  statusMessage.textContent = text;
}

async function startRecording() {
  await chrome.runtime.sendMessage({ type: 'startRecording' });
  await sendMessage({ type: 'startRecording' });
  startBtn.disabled = true;
  stopBtn.disabled = false;
  playBtn.disabled = true;
  saveBtn.disabled = true;
  setStatus('Recording...');
}

async function stopRecording() {
  const response = await sendMessage({ type: 'stopRecording' });
  if (response?.steps) {
    await chrome.runtime.sendMessage({ type: 'stopRecording' });
    saveBtn.disabled = false;
    playBtn.disabled = false;
    setStatus(`Captured ${response.steps.length} steps`);
  }
  startBtn.disabled = false;
  stopBtn.disabled = true;
}

async function playRecording(steps) {
  await chrome.runtime.sendMessage({ type: 'playRecording', steps });
  await sendMessage({ type: 'playSteps', steps });
  setStatus('Playing recording');
}

async function saveRecording() {
  const name = recordingNameInput.value.trim();
  if (!name) {
    setStatus('Please enter a recording name');
    return;
  }
  const { steps } = await chrome.runtime.sendMessage({ type: 'getCurrentRecording' });
  await chrome.runtime.sendMessage({ type: 'saveRecording', name, steps });
  setStatus(`Saved recording: ${name}`);
  saveBtn.disabled = true;
  await loadRecordings();
}

async function loadRecordings() {
  recordingsList.innerHTML = '';
  const { recordings } = await chrome.runtime.sendMessage({ type: 'listRecordings' });
  const names = Object.keys(recordings);
  if (!names.length) {
    recordingsList.innerHTML = '<li>No saved recordings yet.</li>';
    return;
  }

  names.forEach((name) => {
    const li = document.createElement('li');
    li.className = 'recording-item';

    const label = document.createElement('span');
    label.className = 'name';
    label.textContent = name;

    const actions = document.createElement('div');
    actions.className = 'recording-actions';

    const loadBtn = document.createElement('button');
    loadBtn.textContent = 'Load';
    loadBtn.addEventListener('click', async () => {
      const { steps } = await chrome.runtime.sendMessage({ type: 'loadRecording', name });
      playBtn.disabled = !steps.length;
      saveBtn.disabled = false;
      setStatus(`Loaded recording: ${name}`);
    });

    const playSavedBtn = document.createElement('button');
    playSavedBtn.textContent = 'Play';
    playSavedBtn.addEventListener('click', async () => {
      const { steps } = await chrome.runtime.sendMessage({ type: 'loadRecording', name });
      await playRecording(steps);
    });

    actions.appendChild(loadBtn);
    actions.appendChild(playSavedBtn);
    li.appendChild(label);
    li.appendChild(actions);
    recordingsList.appendChild(li);
  });
}

startBtn.addEventListener('click', startRecording);
stopBtn.addEventListener('click', stopRecording);
playBtn.addEventListener('click', async () => {
  const { steps } = await chrome.runtime.sendMessage({ type: 'getCurrentRecording' });
  if (!steps.length) {
    setStatus('Nothing to play yet');
    return;
  }
  await playRecording(steps);
});
saveBtn.addEventListener('click', saveRecording);
refreshBtn.addEventListener('click', loadRecordings);

(async function init() {
  const { steps } = await chrome.runtime.sendMessage({ type: 'getCurrentRecording' });
  playBtn.disabled = !steps.length;
  saveBtn.disabled = !steps.length;
  await loadRecordings();
})();
