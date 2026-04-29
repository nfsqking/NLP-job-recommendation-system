document.addEventListener('DOMContentLoaded', function() {
    initDeepAnalysis();
});

function initDeepAnalysis() {
    document.querySelectorAll('.deep-analysis-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const jobId = this.dataset.jobId;
            startDeepAnalysis(jobId, this);
        });
    });
}

function startDeepAnalysis(jobId, btn) {
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = '分析中...';
    
    showLoading('正在进行深度分析，请稍候...');
    
    fetch('/deep_analysis/api/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ job_id: parseInt(jobId) })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        btn.disabled = false;
        btn.textContent = originalText;
        
        if (data.success) {
            window.location.href = `/deep_analysis/result/${jobId}`;
        } else {
            alert('分析失败：' + (data.message || '未知错误'));
        }
    })
    .catch(error => {
        hideLoading();
        btn.disabled = false;
        btn.textContent = originalText;
        console.error('深度分析出错:', error);
        alert('分析出错，请重试');
    });
}

function showLoading(text) {
    const overlay = document.getElementById('loadingOverlay');
    const loadingText = overlay.querySelector('.loading-text');
    if (loadingText) {
        loadingText.textContent = text || '正在处理中，请稍候...';
    }
    overlay.style.display = 'flex';
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = 'none';
}
