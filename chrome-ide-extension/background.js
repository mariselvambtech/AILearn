const CURRENT_STEPS_KEY = 'currentSteps';
const SAVED_RECORDINGS_KEY = 'recordings';

async function setCurrentSteps(steps) {
  await chrome.storage.local.set({ [CURRENT_STEPS_KEY]: steps });
}

async function getCurrentSteps() {
  const data = await chrome.storage.local.get({ [CURRENT_STEPS_KEY]: [] });
  return data[CURRENT_STEPS_KEY];
}

async function getSavedRecordings() {
  const data = await chrome.storage.local.get({ [SAVED_RECORDINGS_KEY]: {} });
  return data[SAVED_RECORDINGS_KEY];
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    switch (message.type) {
      case 'startRecording': {
        await setCurrentSteps([]);
        if (sender.tab?.id !== undefined) {
          chrome.tabs.sendMessage(sender.tab.id, { type: 'startRecording' });
        }
        sendResponse({ ok: true });
        break;
      }
      case 'stopRecording': {
        if (sender.tab?.id !== undefined) {
          chrome.tabs.sendMessage(sender.tab.id, { type: 'stopRecording' }, async (response) => {
            if (response?.steps) {
              await setCurrentSteps(response.steps);
              sendResponse({ ok: true, steps: response.steps });
            }
          });
          return true;
        }
        sendResponse({ ok: false });
        break;
      }
      case 'recordedStep': {
        const current = await getCurrentSteps();
        current.push(message.step);
        await setCurrentSteps(current);
        sendResponse({ ok: true });
        break;
      }
      case 'getCurrentRecording': {
        const steps = await getCurrentSteps();
        sendResponse({ steps });
        break;
      }
      case 'playRecording': {
        const steps = message.steps ?? (await getCurrentSteps());
        if (sender.tab?.id !== undefined) {
          chrome.tabs.sendMessage(sender.tab.id, { type: 'playSteps', steps });
        }
        sendResponse({ ok: true });
        break;
      }
      case 'saveRecording': {
        const recordings = await getSavedRecordings();
        recordings[message.name] = message.steps ?? (await getCurrentSteps());
        await chrome.storage.local.set({ [SAVED_RECORDINGS_KEY]: recordings });
        sendResponse({ ok: true, recordings });
        break;
      }
      case 'listRecordings': {
        const recordings = await getSavedRecordings();
        sendResponse({ recordings });
        break;
      }
      case 'loadRecording': {
        const recordings = await getSavedRecordings();
        const steps = recordings[message.name] ?? [];
        await setCurrentSteps(steps);
        sendResponse({ ok: true, steps });
        break;
      }
      default:
        sendResponse({ ok: false, error: 'Unknown message type' });
    }
  })();
  return true;
});
