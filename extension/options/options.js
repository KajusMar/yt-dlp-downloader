/**
 * yt-dlp Video Downloader - Options Script
 */
const DEFAULTS = {
  downloadDir: '',
  defaultFormat: 'best'
};

document.addEventListener('DOMContentLoaded', async () => {
  const dirInput = document.getElementById('downloadDir');
  const fmtInput = document.getElementById('defaultFormat');
  const saveBtn = document.getElementById('saveBtn');
  const savedMsg = document.getElementById('savedMsg');

  // Load saved settings
  const stored = await browser.storage.local.get(DEFAULTS);
  dirInput.value = stored.downloadDir || '';
  fmtInput.value = stored.defaultFormat || 'best';

  saveBtn.addEventListener('click', async () => {
    await browser.storage.local.set({
      downloadDir: dirInput.value.trim(),
      defaultFormat: fmtInput.value
    });
    savedMsg.classList.add('show');
    setTimeout(() => savedMsg.classList.remove('show'), 1500);
  });
});
