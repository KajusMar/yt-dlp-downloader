/**
 * yt-dlp Video Downloader - Options Script
 */
const DEFAULTS = {
  downloadDir: '',  // empty => videos always save in ~/Videos/yt-dlp
  defaultFormat: 'best'
};

const YTDLP_FOLDER = (() => {
  // Resolve the canonical yt-dlp folder (~/Videos/yt-dlp) so the Options
  // field pre-fills with it; empty input still means "always the yt-dlp folder".
  const home = (process.env.HOME || process.env.USERPROFILE || '~').replace(/\\/g, '\\');
  return home + '\\Videos\\yt-dlp';
})();

document.addEventListener('DOMContentLoaded', async () => {
  const dirInput = document.getElementById('downloadDir');
  const fmtInput = document.getElementById('defaultFormat');
  const saveBtn = document.getElementById('saveBtn');
  const savedMsg = document.getElementById('savedMsg');

  // Load saved settings; default display to the yt-dlp folder.
  const stored = await browser.storage.local.get(DEFAULTS);
  dirInput.value = stored.downloadDir || YTDLP_FOLDER;
  fmtInput.value = stored.defaultFormat || 'best';

  saveBtn.addEventListener('click', async () => {
    // Empty field => reset to the yt-dlp folder (videos always save there).
    const dir = dirInput.value.trim() || YTDLP_FOLDER;
    await browser.storage.local.set({
      downloadDir: dir,
      defaultFormat: fmtInput.value
    });
    savedMsg.classList.add('show');
    setTimeout(() => savedMsg.classList.remove('show'), 1500);
  });
});
