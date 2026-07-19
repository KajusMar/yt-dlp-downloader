/**
 * yt-dlp Video Downloader - Content Script
 * Detects videos on pages and adds download buttons
 */

(function() {
  'use strict';
  
  // Supported video hosting domains
  const VIDEO_DOMAINS = [
    'youtube.com',
    'youtu.be',
    'vimeo.com',
    'twitch.tv',
    'dailymotion.com',
    'facebook.com',
    'instagram.com',
    'twitter.com',
    'x.com',
    'tiktok.com',
    'reddit.com',
    'soundcloud.com',
    'bandcamp.com',
    'bilibili.com',
    'nicovideo.jp',
    'rumble.com',
    'odysee.com',
    'lbry.tv',
    'streamable.com',
    'gfycat.com',
    'imgur.com',
    'vk.com',
    'ok.ru'
  ];
  
  // Video element selectors
  const VIDEO_SELECTORS = [
    'video',
    'iframe[src*="youtube"]',
    'iframe[src*="vimeo"]',
    'iframe[src*="dailymotion"]',
    'iframe[src*="twitch"]',
    'iframe[src*="facebook"]',
    'iframe[src*="instagram"]',
    'div[data-video-url]',
    '[data-video-id]',
    'video source'
  ];
  
  // State
  const detectedVideos = new Map();
  const downloadButtons = new WeakMap();
  let observer = null;
  let scanTimeout = null;
  
  /**
   * Check if URL is from a supported video site
   */
  function isVideoUrl(url) {
    try {
      const hostname = new URL(url).hostname.replace('www.', '');
      return VIDEO_DOMAINS.some(domain => hostname.includes(domain));
    } catch {
      return false;
    }
  }
  
  /**
   * Extract video URL from element
   */
  function getVideoUrl(element) {
    // Direct video element
    if (element.tagName === 'VIDEO') {
      return element.currentSrc || element.src;
    }
    
    // Iframe
    if (element.tagName === 'IFRAME') {
      return element.src;
    }
    
    // Data attributes
    return element.dataset.videoUrl || 
           element.dataset.videoId || 
           element.getAttribute('data-video-url') ||
           element.getAttribute('data-video-id');
  }
  
  /**
   * Check if element is a downloadable video
   */
  function isDownloadableVideo(element) {
    const url = getVideoUrl(element);
    return url && isVideoUrl(url);
  }
  
  /**
   * Create download button for a video element
   */
  function createDownloadButton(videoUrl, element) {
    if (downloadButtons.has(element)) return;
    
    const btn = document.createElement('button');
    btn.className = 'ytdlp-download-btn';
    btn.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="7 10 12 15 17 10"/>
        <line x1="12" y1="15" x2="12" y2="3"/>
      </svg>
      <span>Download</span>
    `;
    btn.title = 'Download with yt-dlp (right-click for options)';
    
    // Styles
    Object.assign(btn.style, {
      position: 'fixed',
      top: '0',
      left: '0',
      zIndex: '2147483647',
      background: '#ff0000',
      color: '#fff',
      border: 'none',
      borderRadius: '4px',
      padding: '6px 10px',
      fontSize: '12px',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      cursor: 'pointer',
      display: 'inline-flex',
      alignItems: 'center',
      gap: '4px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
      opacity: '0',
      transform: 'translateY(10px)',
      transition: 'opacity 0.2s, transform 0.2s',
      whiteSpace: 'nowrap'
    });
    
    // Position button near element
    function positionButton() {
      const rect = element.getBoundingClientRect();
      btn.style.top = `${rect.top + window.scrollY - 36}px`;
      btn.style.left = `${rect.left + window.scrollX}px`;
    }
    
    // Show/hide handlers
    let hideTimeout = null;
    const showBtn = () => {
      clearTimeout(hideTimeout);
      positionButton();
      btn.style.opacity = '1';
      btn.style.transform = 'translateY(0)';
    };
    const hideBtn = () => {
      hideTimeout = setTimeout(() => {
        btn.style.opacity = '0';
        btn.style.transform = 'translateY(10px)';
      }, 500);
    };
    
    // Events
    element.addEventListener('mouseenter', showBtn);
    element.addEventListener('mouseleave', hideBtn);
    btn.addEventListener('mouseenter', showBtn);
    btn.addEventListener('mouseleave', hideBtn);
    
    // Click handler
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      downloadVideo(videoUrl);
    });
    
    // Context menu for options
    btn.addEventListener('contextmenu', (e) => {
      e.preventDefault();
      showDownloadOptions(videoUrl, btn);
    });
    
    document.body.appendChild(btn);
    downloadButtons.set(element, { btn, showBtn, hideBtn, positionButton });
    
    // Initial position
    positionButton();
  }
  
  /**
   * Show download options menu
   */
  function showDownloadOptions(videoUrl, anchorElement) {
    // Remove existing menu
    const existing = document.querySelector('.ytdlp-options-menu');
    if (existing) existing.remove();
    
    const menu = document.createElement('div');
    menu.className = 'ytdlp-options-menu';
    menu.innerHTML = `
      <div class="ytdlp-option" data-format="best">Best quality (up to 1080p)</div>
      <div class="ytdlp-option" data-format="bestvideo+bestaudio/best">Best available (any quality)</div>
      <div class="ytdlp-option" data-format="720p">720p</div>
      <div class="ytdlp-option" data-format="480p">480p</div>
      <div class="ytdlp-option" data-format="audio">Audio only (MP3)</div>
      <div class="ytdlp-divider"></div>
      <div class="ytdlp-option" data-format="info">Get info only</div>
    `;
    
    Object.assign(menu.style, {
      position: 'fixed',
      top: `${anchorElement.getBoundingClientRect().bottom + 4}px`,
      left: `${anchorElement.getBoundingClientRect().left}px`,
      background: '#1a1a1a',
      border: '1px solid #333',
      borderRadius: '6px',
      boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
      zIndex: '2147483648',
      minWidth: '200px',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      fontSize: '12px',
      overflow: 'hidden'
    });
    
    // Add styles
    const style = document.createElement('style');
    style.textContent = `
      .ytdlp-option { padding: 8px 12px; cursor: pointer; color: #fff; transition: background 0.1s; }
      .ytdlp-option:hover { background: #ff0000; }
      .ytdlp-divider { height: 1px; background: #333; margin: 4px 0; }
    `;
    document.head.appendChild(style);
    
    // Click handlers
    menu.querySelectorAll('.ytdlp-option').forEach(opt => {
      opt.addEventListener('click', () => {
        const format = opt.dataset.format;
        downloadVideo(videoUrl, format);
        menu.remove();
        style.remove();
      });
    });
    
    // Close on outside click
    const closeMenu = (e) => {
      if (!menu.contains(e.target)) {
        menu.remove();
        style.remove();
        document.removeEventListener('click', closeMenu);
      }
    };
    setTimeout(() => document.addEventListener('click', closeMenu), 0);
    
    document.body.appendChild(menu);
  }
  
  /**
   * Send download request to background
   */
  function downloadVideo(videoUrl, format = 'best') {
    if (typeof browser !== 'undefined' && browser.runtime) {
      browser.runtime.sendMessage({
        type: 'DOWNLOAD_VIDEO',
        payload: { url: videoUrl, format }
      }).catch(err => {
        console.error('yt-dlp: Failed to send download request', err);
        showNotification('Download failed: Could not reach extension', 'error');
      });
    } else {
      showNotification('Download failed: Extension context not available', 'error');
    }
  }
  
  /**
   * Show notification
   */
  function showNotification(message, type = 'info') {
    const existing = document.querySelector('.ytdlp-notification');
    if (existing) existing.remove();
    
    const notif = document.createElement('div');
    notif.className = `ytdlp-notification ${type}`;
    notif.innerHTML = `
      <div class="ytdlp-notification-content">
        <div class="ytdlp-notification-title">yt-dlp Downloader</div>
        <div class="ytdlp-notification-message">${message}</div>
      </div>
      <button class="ytdlp-notification-close">&times;</button>
    `;
    
    // Add styles if not present
    if (!document.querySelector('#ytdlp-notification-styles')) {
      const style = document.createElement('style');
      style.id = 'ytdlp-notification-styles';
      style.textContent = `
        .ytdlp-notification {
          position: fixed;
          bottom: 20px;
          right: 20px;
          background: #1a1a1a;
          color: #fff;
          padding: 12px 16px;
          border-radius: 8px;
          box-shadow: 0 4px 20px rgba(0,0,0,0.4);
          z-index: 2147483647;
          display: flex;
          align-items: center;
          gap: 12px;
          min-width: 280px;
          max-width: 400px;
          animation: ytdlp-slide-in 0.3s ease;
          border-left: 4px solid #ff0000;
        }
        .ytdlp-notification.success { border-left-color: #00ff88; }
        .ytdlp-notification.error { border-left-color: #ff4444; }
        @keyframes ytdlp-slide-in {
          from { opacity: 0; transform: translateX(100px); }
          to { opacity: 1; transform: translateX(0); }
        }
        .ytdlp-notification-content { flex: 1; }
        .ytdlp-notification-title { font-weight: 600; font-size: 13px; margin-bottom: 2px; }
        .ytdlp-notification-message { font-size: 12px; opacity: 0.8; }
        .ytdlp-notification-close {
          background: none;
          border: none;
          color: #888;
          cursor: pointer;
          padding: 4px;
          font-size: 16px;
          line-height: 1;
        }
        .ytdlp-notification-close:hover { color: #fff; }
      `;
      document.head.appendChild(style);
    }
    
    document.body.appendChild(notif);
    
    // Animate in
    requestAnimationFrame(() => {
      notif.style.transform = 'translateX(0)';
      notif.style.opacity = '1';
    });
    
    // Close button
    notif.querySelector('.ytdlp-notification-close').addEventListener('click', () => {
      notif.style.transform = 'translateX(100px)';
      notif.style.opacity = '0';
      setTimeout(() => notif.remove(), 300);
    });
    
    // Auto-dismiss
    setTimeout(() => {
      if (notif.parentNode) {
        notif.style.transform = 'translateX(100px)';
        notif.style.opacity = '0';
        setTimeout(() => notif.remove(), 300);
      }
    }, 5000);
  }
  
  /**
   * Scan page for videos
   */
  function scanPage() {
    // Check current page URL
    if (isVideoUrl(window.location.href)) {
      const key = 'page:' + window.location.href;
      if (!detectedVideos.has(key)) {
        detectedVideos.set(key, { url: window.location.href, source: 'page_url' });
      }
    }
    
    // Find video elements
    for (const selector of VIDEO_SELECTORS) {
      const elements = document.querySelectorAll(selector);
      elements.forEach(el => {
        if (isDownloadableVideo(el)) {
          const url = getVideoUrl(el);
          const fullUrl = url.startsWith('//') ? 'https:' + url : url;
          const key = 'element:' + fullUrl;
          
          if (!detectedVideos.has(key)) {
            detectedVideos.set(key, { url: fullUrl, source: selector, element: el });
            createDownloadButton(fullUrl, el);
          }
        }
      });
    }
    
    // Find links to video pages
    document.querySelectorAll('a[href]').forEach(link => {
      const href = link.href;
      if (isVideoUrl(href) && !link.classList.contains('ytdlp-processed')) {
        link.classList.add('ytdlp-processed');
        const indicator = document.createElement('span');
        indicator.className = 'ytdlp-link-indicator';
        indicator.textContent = ' ⬇';
        indicator.title = 'Downloadable with yt-dlp (right-click for options)';
        indicator.style.cssText = 'font-size: 10px; color: #ff0000; margin-left: 2px; cursor: help;';
        link.appendChild(indicator);
      }
    });
  }
  
  /**
   * Cleanup on unload
   */
  function cleanup() {
    for (const [, { btn, showBtn, hideBtn }] of downloadButtons) {
      btn.remove();
    }
    downloadButtons = new WeakMap();
  }
  
  /**
   * Debounced scan
   */
  function scheduleScan() {
    clearTimeout(scanTimeout);
    scanTimeout = setTimeout(scanPage, 500);
  }
  
  /**
   * Initialize content script
   */
  function init() {
    // Initial scan
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        scheduleScan();
        observer = new MutationObserver(() => scheduleScan());
        observer.observe(document.body || document.documentElement, {
          childList: true,
          subtree: true,
          attributes: true,
          attributeFilter: ['src', 'data-src', 'data-video-url', 'data-video-id', 'href']
        });
      });
    } else {
      scheduleScan();
      observer = new MutationObserver(() => scheduleScan());
      observer.observe(document.body || document.documentElement, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['src', 'data-src', 'data-video-url', 'data-video-id', 'href']
      });
    }
    
    // Cleanup
    window.addEventListener('beforeunload', cleanup);
    
    // Listen for messages from popup/background
    if (typeof browser !== 'undefined' && browser.runtime) {
      browser.runtime.onMessage.addListener((message) => {
        if (message.type === 'SCAN_VIDEOS') {
          scanPage();
        }
      });
    }
    
    // Expose API for popup
    window.ytdlpDetector = {
      scan: scanPage,
      getDetected: () => Array.from(detectedVideos.values()),
      download: downloadVideo
    };
  }
  
  // Start
  init();
  
})();