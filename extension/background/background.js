/**
 * yt-dlp Video Downloader - Background Script
 * Handles native messaging communication with the Python host
 */

// Native messaging host name (must match manifest file)
const NATIVE_HOST_NAME = 'com.kajusmar.ytdlp_downloader';

// Connection state
let nativePort = null;
let messageId = 0;
const pendingRequests = new Map();

// Detected videos per tab
const detectedVideos = new Map();

/**
 * Connect to native messaging host
 */
function connectNativeHost() {
  try {
    nativePort = browser.runtime.connectNative(NATIVE_HOST_NAME);

    nativePort.onMessage.addListener(handleNativeMessage);

    nativePort.onDisconnect.addListener(() => {
      const err = browser.runtime.lastError?.message || 'disconnected';
      console.log('[yt-dlp] Native host disconnected:', err);
      nativePort = null;

      // Reject pending requests
      for (const [, { reject }] of pendingRequests) {
        reject(new Error('Native host disconnected: ' + err));
      }
      pendingRequests.clear();

      // Try reconnecting after 3 seconds
      setTimeout(connectNativeHost, 3000);
    });
  } catch (e) {
    console.error('[yt-dlp] Failed to connect to native host:', e);
    nativePort = null;
    // Retry later
    setTimeout(connectNativeHost, 3000);
  }
}

/**
 * Send message to native host
 */
function sendToNative(message) {
  return new Promise((resolve, reject) => {
    if (!nativePort) {
      connectNativeHost();
      // Wait for connection to come up
      let waited = 0;
      const poll = setInterval(() => {
        waited += 100;
        if (nativePort) {
          clearInterval(poll);
          sendToNative(message).then(resolve).catch(reject);
        } else if (waited >= 8000) {
          clearInterval(poll);
          reject(new Error('Native host not available. Run install_windows.bat to register it.'));
        }
      }, 100);
      return;
    }

    const id = ++messageId;
    pendingRequests.set(id, { resolve, reject });

    nativePort.postMessage({ id, ...message });

    // Timeout after 5 minutes (large downloads)
    setTimeout(() => {
      if (pendingRequests.has(id)) {
        pendingRequests.delete(id);
        reject(new Error('Request timeout'));
      }
    }, 300000);
  });
}

/**
 * Handle messages from native host
 */
function handleNativeMessage(response) {
  const { id, result, error, progress } = response;

  // Handle progress updates
  if (progress !== undefined) {
    broadcastProgress(id, progress);
    return;
  }

  const pending = pendingRequests.get(id);
  if (!pending) return;

  pendingRequests.delete(id);

  if (error) {
    pending.reject(new Error(error));
  } else {
    pending.resolve(result);
  }
}

/**
 * Broadcast progress to popup
 */
function broadcastProgress(requestId, progress) {
  browser.runtime.sendMessage({
    type: 'DOWNLOAD_PROGRESS',
    requestId,
    progress
  }).catch(() => {}); // Ignore if no listeners
}

/**
 * Check if yt-dlp is available
 */
async function checkHealth() {
  return sendToNative({ command: 'health_check' });
}

/**
 * Get video info
 */
async function getVideoInfo(url) {
  return sendToNative({ command: 'get_info', url });
}

/**
 * Download video
 */
async function downloadVideo(url, options = {}) {
  return sendToNative({
    command: 'download',
    url,
    options: {
      format: options.format || 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
      extractAudio: options.extractAudio || false,
      audioFormat: options.audioFormat || 'mp3',
      outputDir: options.outputDir || ''
    }
  });
}

/**
 * Open download folder
 */
async function openDownloadFolder(dir = '') {
  return sendToNative({ command: 'open_folder', dir });
}

/**
 * Message handler (returns a value or Promise for async responses)
 */
async function handleMessage(message, sender) {
  switch (message.type) {
    case 'CHECK_HEALTH':
      try {
        const data = await checkHealth();
        return { success: true, data };
      } catch (e) {
        return { success: false, error: e.message };
      }

    case 'GET_VIDEO_INFO':
      try {
        const data = await getVideoInfo(message.payload.url);
        return { success: true, data };
      } catch (e) {
        return { success: false, error: e.message };
      }

    case 'DOWNLOAD_VIDEO': {
      try {
        const data = await downloadVideo(message.payload.url, message.payload.options || {});
        return { success: true, data };
      } catch (e) {
        return { success: false, error: e.message };
      }
    }

    case 'OPEN_DOWNLOAD_FOLDER':
      try {
        await openDownloadFolder(message.payload?.dir);
        return { success: true };
      } catch (e) {
        return { success: false, error: e.message };
      }

    case 'REGISTER_VIDEO':
      if (sender.tab?.id) {
        if (!detectedVideos.has(sender.tab.id)) {
          detectedVideos.set(sender.tab.id, []);
        }
        detectedVideos.get(sender.tab.id).push(message.payload);
      }
      return { success: true };

    case 'GET_DETECTED_VIDEOS': {
      const videos = detectedVideos.get(sender.tab?.id) || [];
      return { videos };
    }

    case 'CLEAR_DETECTED_VIDEOS':
      if (sender.tab?.id) {
        detectedVideos.delete(sender.tab.id);
      }
      return { success: true };
  }

  return false;
}

/**
 * Handle messages from content scripts / popup
 */
browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const handled = handleMessage(message, sender);
  if (handled instanceof Promise) {
    handled.then(sendResponse).catch(e => sendResponse({ success: false, error: e.message }));
    return true;
  }
  return handled;
});

/**
 * Create context menus
 */
async function createContextMenus() {
  try {
    await browser.contextMenus.removeAll();

    browser.contextMenus.create({
      id: 'ytdlp-download-video',
      title: 'Download video with yt-dlp',
      contexts: ['link', 'video', 'audio', 'page'],
      documentUrlPatterns: ['<all_urls>']
    });

    browser.contextMenus.create({
      id: 'ytdlp-download-audio',
      title: 'Download audio only (MP3)',
      contexts: ['link', 'video', 'audio', 'page'],
      documentUrlPatterns: ['<all_urls>']
    });

    browser.contextMenus.create({
      id: 'ytdlp-download-best',
      title: 'Download best quality',
      contexts: ['link', 'video', 'audio', 'page'],
      documentUrlPatterns: ['<all_urls>']
    });
  } catch (e) {
    console.error('[yt-dlp] Failed to create context menus:', e);
  }
}

browser.contextMenus.onClicked.addListener(async (info, tab) => {
  const url = info.linkUrl || info.pageUrl || info.srcUrl;
  if (!url) return;

  let options = { format: 'bestvideo[height<=1080]+bestaudio/best[height<=1080]' };

  switch (info.menuItemId) {
    case 'ytdlp-download-audio':
      options = { format: 'bestaudio', extractAudio: true, audioFormat: 'mp3' };
      break;
    case 'ytdlp-download-best':
      options = { format: 'bestvideo+bestaudio/best' };
      break;
  }

  try {
    await downloadVideo(url, options);
    showNotification('Download started', 'Check your downloads folder');
  } catch (e) {
    showNotification('Download failed', e.message);
  }
});

/**
 * Show notification
 */
function showNotification(title, message) {
  browser.notifications.create({
    type: 'basic',
    iconUrl: browser.runtime.getURL('icons/icon48.png'),
    title,
    message
  });
}

/**
 * Handle keyboard shortcut
 */
browser.commands.onCommand.addListener(async (command) => {
  if (command === 'download-video') {
    const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
    if (tab?.url) {
      try {
        await downloadVideo(tab.url);
        showNotification('Download started', 'Check your downloads folder');
      } catch (e) {
        showNotification('Download failed', e.message);
      }
    }
  }
});

/**
 * Clean up on tab close
 */
browser.tabs.onRemoved.addListener((tabId) => {
  detectedVideos.delete(tabId);
});

// Initialize
browser.runtime.onStartup.addListener(() => {
  connectNativeHost();
  createContextMenus();
});

browser.runtime.onInstalled.addListener(() => {
  connectNativeHost();
  createContextMenus();
});

// Connect immediately
connectNativeHost();
