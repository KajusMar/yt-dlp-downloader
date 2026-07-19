/**
 * yt-dlp Video Downloader - Popup Script
 */

const TAB_DETECT = 'detect';
const TAB_MANUAL = 'manual';
const TAB_DOWNLOADS = 'downloads';

let currentTab = TAB_DETECT;
let detectedVideos = [];
let activeDownloads = new Map();
let ytDlpAvailable = false;
let currentTabId = null;

/**
 * Initialize popup
 */
document.addEventListener('DOMContentLoaded', init);

async function init() {
  setupTabs();
  setupEventListeners();
  await checkHealth();
  await getCurrentTab();
  await scanPage();
  setupMessageListener();
}

/**
 * Setup tab navigation
 */
function setupTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });
}

function switchTab(tabName) {
  currentTab = tabName;
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabName);
  });
  document.querySelectorAll('.tab-panel').forEach(panel => {
    panel.classList.toggle('active', panel.id === 'tab-' + tabName);
  });
  
  if (tabName === TAB_DETECT) {
    scanPage();
  }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  // Manual URL input
  const manualUrl = document.getElementById('manualUrl');
  manualUrl.addEventListener('input', (e) => {
    document.getElementById('manualDownloadBtn').disabled = !e.target.value.trim();
  });
  
  document.getElementById('fetchInfoBtn').addEventListener('click', fetchManualVideoInfo);
  document.getElementById('manualDownloadBtn').addEventListener('click', downloadManualVideo);
  document.getElementById('scanBtn').addEventListener('click', scanPage);
  
  // Footer buttons
  document.getElementById('openFolderBtn').addEventListener('click', openDownloadFolder);
  document.getElementById('optionsBtn').addEventListener('click', openOptions);
}

/**
 * Listen for messages from background (progress updates)
 */
function setupMessageListener() {
  browser.runtime.onMessage.addListener((message) => {
    if (message.type === 'DOWNLOAD_PROGRESS') {
      updateDownloadProgress(message.requestId, message.progress);
    }
  });
}

/**
 * Get current active tab
 */
async function getCurrentTab() {
  const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
  currentTabId = tab?.id;
  return tab;
}

/**
 * Check yt-dlp health via native host
 */
async function checkHealth() {
  try {
    const response = await browser.runtime.sendMessage({ type: 'CHECK_HEALTH' });
    if (response.success) {
      ytDlpAvailable = true;
      const data = response.data;
      setStatus('ok', `yt-dlp ${data.yt_dlp_version || 'ready'} ${data.ffmpeg_available ? '• ffmpeg' : '• no ffmpeg'}`);
    } else {
      throw new Error(response.error || 'Health check failed');
    }
  } catch (e) {
    ytDlpAvailable = false;
    setStatus('error', `Not connected: ${e.message}`);
  }
}

function setStatus(type, text) {
  const statusEl = document.getElementById('status');
  const textEl = document.getElementById('statusText');
  statusEl.className = 'status ' + type;
  textEl.textContent = text;
}

/**
 * Scan current page for videos
 * Reads directly from the content script on the page.
 */
async function scanPage() {
  if (!ytDlpAvailable || !currentTabId) {
    renderDetectedVideos([]);
    return;
  }

  try {
    // Ask content script to scan, then return the detected list directly
    const response = await browser.tabs.sendMessage(currentTabId, { type: 'SCAN_AND_GET' });
    detectedVideos = (response && response.videos) || [];
    renderDetectedVideos(detectedVideos);
  } catch (e) {
    console.warn('[yt-dlp] scanPage failed:', e);
    detectedVideos = [];
    renderDetectedVideos([]);
  }
}

/**
 * Render detected videos list
 */
function renderDetectedVideos(videos) {
  const container = document.getElementById('detectedVideos');
  const emptyEl = document.getElementById('emptyDetected');
  
  if (videos.length === 0) {
    container.innerHTML = '';
    emptyEl.style.display = 'block';
    return;
  }
  
  emptyEl.style.display = 'none';
  
  container.innerHTML = videos.map((video, index) => `
    <div class="video-item" data-index="${index}">
      <div class="video-thumb">
        ${video.thumbnail ? `<img src="${escapeHtml(video.thumbnail)}" alt="">` : '<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:#555;font-size:10px;">No thumb</div>'}
      </div>
      <div class="video-info">
        <div class="video-title">${escapeHtml(video.title || video.url)}</div>
        <div class="video-meta">
          ${video.duration ? formatDuration(video.duration) : ''}
          ${video.uploader ? '• ' + escapeHtml(video.uploader) : ''}
        </div>
      </div>
      <div class="video-actions">
        <button class="btn btn-primary btn-small download-btn" data-index="${index}">Download</button>
        <button class="btn btn-secondary btn-small info-btn" data-index="${index}">Info</button>
      </div>
    </div>
  `).join('');
  
  // Add click handlers
  container.querySelectorAll('.download-btn').forEach(btn => {
    btn.addEventListener('click', (e) => downloadDetectedVideo(parseInt(e.currentTarget.dataset.index)));
  });
  container.querySelectorAll('.info-btn').forEach(btn => {
    btn.addEventListener('click', (e) => showVideoInfo(parseInt(e.currentTarget.dataset.index)));
  });
}

/**
 * Fetch info for manual URL
 */
async function fetchManualVideoInfo() {
  const url = document.getElementById('manualUrl').value.trim();
  if (!url || !ytDlpAvailable) return;
  
  const infoDiv = document.getElementById('manualVideoInfo');
  const formatGroup = document.getElementById('formatGroup');
  infoDiv.classList.remove('hidden');
  infoDiv.innerHTML = '<div style="color:#66aaff;padding:10px;">Fetching video info...</div>';
  formatGroup.style.display = 'none';
  
  try {
    const response = await browser.runtime.sendMessage({ 
      type: 'GET_VIDEO_INFO', 
      payload: { url } 
    });
    
    if (response.success) {
      const info = response.data;
      infoDiv.innerHTML = `
        <div class="video-info-header">
          <div class="video-info-thumb">
            ${info.thumbnail ? `<img src="${escapeHtml(info.thumbnail)}" alt="">` : '<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:#555;">No thumb</div>'}
          </div>
          <div class="video-info-details">
            <div class="video-info-title">${escapeHtml(info.title || 'Unknown')}</div>
            <div class="video-info-meta">
              ${info.duration ? `<span>⏱ ${formatDuration(info.duration)}</span>` : ''}
              ${info.uploader ? `<span>👤 ${escapeHtml(info.uploader)}</span>` : ''}
              ${info.view_count ? `<span>👁 ${formatNumber(info.view_count)}</span>` : ''}
              ${info.available_qualities && info.available_qualities.length ? `<span>📺 ${info.available_qualities.join(', ')}p</span>` : ''}
            </div>
          </div>
        </div>
      `;
      formatGroup.style.display = 'block';
      document.getElementById('manualDownloadBtn').disabled = false;
    } else {
      throw new Error(response.error);
    }
  } catch (e) {
    infoDiv.innerHTML = `<div style="color:#ff6666;padding:10px;">Error: ${escapeHtml(e.message)}</div>`;
    formatGroup.style.display = 'none';
    document.getElementById('manualDownloadBtn').disabled = true;
  }
}

/**
 * Download detected video
 */
async function downloadDetectedVideo(index) {
  const video = detectedVideos[index];
  if (!video || !ytDlpAvailable) return;
  
  const btn = document.querySelector(`.download-btn[data-index="${index}"]`);
  if (!btn) return;
  
  btn.disabled = true;
  btn.textContent = 'Starting...';
  
  try {
    const response = await browser.runtime.sendMessage({
      type: 'DOWNLOAD_VIDEO',
      payload: { 
        url: video.url, 
        options: { format: 'bestvideo[height<=1080]+bestaudio/best[height<=1080]' } 
      }
    });
    
    if (response.success) {
      btn.textContent = 'Started ✓';
      btn.classList.remove('btn-primary');
      btn.classList.add('btn-secondary');
      addDownloadToList(video.url, video.title || 'Video', response.data?.requestId);
    } else {
      throw new Error(response.error);
    }
  } catch (e) {
    btn.disabled = false;
    btn.textContent = 'Download';
    alert('Download failed: ' + e.message);
  }
}

/**
 * Download manual video
 */
async function downloadManualVideo() {
  const url = document.getElementById('manualUrl').value.trim();
  const format = document.getElementById('manualFormat').value;
  
  if (!url || !ytDlpAvailable) return;
  
  const btn = document.getElementById('manualDownloadBtn');
  btn.disabled = true;
  btn.textContent = 'Starting...';
  
  const formatMap = {
    'best': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
    'bestvideo+bestaudio/best': 'bestvideo+bestaudio/best',
    '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
    '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
    'audio': 'bestaudio'
  };
  
  const options = { format: formatMap[format] };
  if (format === 'audio') {
    options.extractAudio = true;
    options.audioFormat = 'mp3';
  }
  
  try {
    const response = await browser.runtime.sendMessage({
      type: 'DOWNLOAD_VIDEO',
      payload: { url, options }
    });
    
    if (response.success) {
      btn.textContent = 'Started ✓';
      btn.classList.remove('btn-primary');
      btn.classList.add('btn-secondary');
      addDownloadToList(url, 'Manual download', response.data?.requestId);
    } else {
      throw new Error(response.error);
    }
  } catch (e) {
    btn.disabled = false;
    btn.textContent = 'Download';
    alert('Download failed: ' + e.message);
  }
}

/**
 * Add to downloads list
 */
function addDownloadToList(url, title, requestId) {
  const id = 'dl_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8);
  activeDownloads.set(id, { url, title, progress: 0, status: 'starting', requestId });
  
  document.getElementById('emptyDownloads').style.display = 'none';
  renderDownloadsList();
  
  // Switch to downloads tab
  switchTab(TAB_DOWNLOADS);
}

/**
 * Update download progress
 */
function updateDownloadProgress(requestId, progress) {
  for (const [id, dl] of activeDownloads) {
    if (dl.requestId === requestId || (progress.url && dl.url === progress.url)) {
      dl.progress = progress.percent || 0;
      dl.status = progress.status || 'downloading';
      dl.requestId = requestId;
      if (progress.status === 'completed' || progress.percent >= 100) {
        dl.status = 'completed';
      }
      renderDownloadsList();
      break;
    }
  }
}

/**
 * Render downloads list
 */
function renderDownloadsList() {
  const list = document.getElementById('downloadsList');
  
  if (activeDownloads.size === 0) {
    list.innerHTML = '';
    document.getElementById('emptyDownloads').style.display = 'block';
    return;
  }
  
  document.getElementById('emptyDownloads').style.display = 'none';
  
  list.innerHTML = Array.from(activeDownloads.entries()).map(([id, dl]) => `
    <div class="download-item" data-id="${id}">
      <div class="download-info">
        <div class="download-title">${escapeHtml(dl.title)}</div>
        <div class="download-progress">
          <div class="download-progress-fill" style="width:${dl.progress}%"></div>
        </div>
      </div>
      <div class="download-status">
        ${dl.status === 'completed' ? '✓ Done' : dl.progress + '%'}
      </div>
    </div>
  `).join('');
}

/**
 * Show video info (simple alert for now)
 */
function showVideoInfo(index) {
  const video = detectedVideos[index];
  if (!video) return;
  
  let msg = `Title: ${video.title || 'Unknown'}\nURL: ${video.url}`;
  if (video.duration) msg += `\nDuration: ${formatDuration(video.duration)}`;
  if (video.uploader) msg += `\nUploader: ${video.uploader}`;
  alert(msg);
}

/**
 * Open download folder
 */
async function openDownloadFolder() {
  try {
    await browser.runtime.sendMessage({ type: 'OPEN_DOWNLOAD_FOLDER' });
  } catch (e) {
    browser.tabs.create({ url: 'about:downloads' });
  }
}

/**
 * Open options page
 */
function openOptions() {
  if (browser.runtime.openOptionsPage) {
    browser.runtime.openOptionsPage();
  }
}

/**
 * Utility functions
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function formatDuration(seconds) {
  if (!seconds) return '';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return h > 0 ? `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}` : `${m}:${s.toString().padStart(2, '0')}`;
}

function formatNumber(num) {
  if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
  if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
  if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
  return num.toString();
}