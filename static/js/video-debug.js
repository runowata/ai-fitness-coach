/**
 * Video Debug Script - Add to daily_workout.html to debug video issues
 * Logs detailed information about video loading and playback
 */

(function() {
    'use strict';
    
    console.log('=== VIDEO DEBUG SCRIPT LOADED ===');
    
    // Check if video element exists
    const video = document.getElementById('mainVideo');
    if (!video) {
        console.error('ERROR: Video element #mainVideo not found!');
        return;
    }
    
    console.log('Video element found:', video);
    console.log('Current source:', video.src);
    console.log('Video ready state:', video.readyState);
    console.log('Video network state:', video.networkState);
    
    // Log all video events
    const videoEvents = [
        'loadstart', 'progress', 'suspend', 'abort', 'error', 'emptied',
        'stalled', 'loadedmetadata', 'loadeddata', 'canplay', 'canplaythrough',
        'playing', 'waiting', 'seeking', 'seeked', 'ended', 'durationchange',
        'timeupdate', 'play', 'pause', 'ratechange', 'resize', 'volumechange'
    ];
    
    videoEvents.forEach(eventName => {
        video.addEventListener(eventName, function(e) {
            console.log(`VIDEO EVENT: ${eventName}`, {
                currentTime: video.currentTime,
                duration: video.duration,
                readyState: video.readyState,
                networkState: video.networkState,
                error: video.error
            });
        });
    });
    
    // Check video error in detail
    video.addEventListener('error', function(e) {
        console.error('VIDEO ERROR DETAILS:', {
            error: video.error,
            errorCode: video.error ? video.error.code : 'N/A',
            errorMessage: video.error ? video.error.message : 'N/A',
            src: video.src,
            currentSrc: video.currentSrc
        });
        
        // Check if URL is accessible
        if (video.src) {
            fetch(video.src, { method: 'HEAD' })
                .then(response => {
                    console.log('Video URL check:', {
                        url: video.src,
                        status: response.status,
                        statusText: response.statusText,
                        contentType: response.headers.get('content-type'),
                        contentLength: response.headers.get('content-length')
                    });
                })
                .catch(err => {
                    console.error('Failed to fetch video URL:', err);
                });
        }
    });
    
    // Check playlist items
    const playlistItems = document.querySelectorAll('.playlist-item');
    console.log(`Found ${playlistItems.length} playlist items`);
    
    playlistItems.forEach((item, index) => {
        const videoUrl = item.getAttribute('data-video-url');
        const videoTitle = item.getAttribute('data-video-title');
        console.log(`Playlist item ${index + 1}:`, {
            title: videoTitle,
            url: videoUrl,
            isActive: item.classList.contains('active')
        });
        
        // Add error handling to playlist clicks
        const originalClickHandler = item.onclick;
        item.onclick = function(e) {
            console.log(`Playlist item clicked: ${videoTitle}`);
            console.log(`Switching to URL: ${videoUrl}`);
            
            // Call original handler if exists
            if (originalClickHandler) {
                originalClickHandler.call(this, e);
            }
            
            // Monitor the video change
            setTimeout(() => {
                console.log('After playlist click:', {
                    newSrc: video.src,
                    readyState: video.readyState,
                    error: video.error
                });
            }, 100);
        };
    });
    
    // Test video playback capability
    console.log('Video codec support:', {
        mp4: video.canPlayType('video/mp4'),
        webm: video.canPlayType('video/webm'),
        ogg: video.canPlayType('video/ogg')
    });
    
    // Check if videos are being blocked by browser
    if (video.autoplay && !video.paused && video.readyState >= 3) {
        console.log('Video autoplay is working');
    } else if (video.autoplay) {
        console.warn('Video autoplay might be blocked by browser');
    }
    
    // Add manual play button for testing
    const debugPanel = document.createElement('div');
    debugPanel.style.cssText = 'position: fixed; bottom: 10px; right: 10px; background: rgba(0,0,0,0.8); color: white; padding: 10px; border-radius: 5px; z-index: 9999;';
    debugPanel.innerHTML = `
        <h5>Video Debug Panel</h5>
        <button id="debugPlay" class="btn btn-sm btn-primary">Force Play</button>
        <button id="debugReload" class="btn btn-sm btn-warning">Reload Video</button>
        <button id="debugInfo" class="btn btn-sm btn-info">Log Info</button>
        <div id="debugStatus" style="margin-top: 10px; font-size: 12px;"></div>
    `;
    document.body.appendChild(debugPanel);
    
    const debugStatus = document.getElementById('debugStatus');
    
    document.getElementById('debugPlay').onclick = function() {
        video.play().then(() => {
            console.log('Video play() succeeded');
            debugStatus.textContent = 'Play succeeded';
        }).catch(err => {
            console.error('Video play() failed:', err);
            debugStatus.textContent = 'Play failed: ' + err.message;
        });
    };
    
    document.getElementById('debugReload').onclick = function() {
        console.log('Reloading video...');
        video.load();
        debugStatus.textContent = 'Video reloaded';
    };
    
    document.getElementById('debugInfo').onclick = function() {
        const info = {
            src: video.src,
            duration: video.duration,
            currentTime: video.currentTime,
            paused: video.paused,
            ended: video.ended,
            readyState: video.readyState,
            networkState: video.networkState,
            videoWidth: video.videoWidth,
            videoHeight: video.videoHeight,
            error: video.error
        };
        console.table(info);
        debugStatus.innerHTML = '<pre style="font-size: 10px;">' + JSON.stringify(info, null, 2) + '</pre>';
    };
    
    // Update status periodically
    setInterval(() => {
        if (!debugStatus.textContent.includes('Play failed')) {
            debugStatus.textContent = `State: ${video.paused ? 'Paused' : 'Playing'} | Ready: ${video.readyState} | Network: ${video.networkState}`;
        }
    }, 1000);
    
})();