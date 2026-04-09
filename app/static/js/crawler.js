/* 岗位爬虫与查询 JavaScript */

let currentPage = 1;
let totalPages = 1;
let statusCheckInterval = null;

document.addEventListener('DOMContentLoaded', function() {
    loadJobs(1);
    
    document.getElementById('searchBtn').addEventListener('click', function() {
        currentPage = 1;
        loadJobs(1);
    });
    
    document.getElementById('resetBtn').addEventListener('click', function() {
        document.getElementById('keyword').value = '';
        document.getElementById('location').value = '';
        document.getElementById('experience').value = '';
        document.getElementById('education').value = '';
        currentPage = 1;
        loadJobs(1);
    });
    
    document.getElementById('startCrawlerBtn').addEventListener('click', startCrawler);
    document.getElementById('stopCrawlerBtn').addEventListener('click', stopCrawler);
    
    document.querySelectorAll('#keyword, #location, #experience, #education').forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                currentPage = 1;
                loadJobs(1);
            }
        });
    });
});

function loadJobs(page) {
    const keyword = document.getElementById('keyword').value.trim();
    const location = document.getElementById('location').value.trim();
    const experience = document.getElementById('experience').value.trim();
    const education = document.getElementById('education').value.trim();
    
    const params = new URLSearchParams({
        page: page,
        per_page: 10
    });
    
    if (keyword) params.append('keyword', keyword);
    if (location) params.append('location', location);
    if (experience) params.append('experience', experience);
    if (education) params.append('education', education);
    
    fetch(`/api/jobs/search?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderJobList(data.data.jobs);
                document.getElementById('jobCount').textContent = `共 ${data.data.total} 条记录`;
                currentPage = data.data.current_page;
                totalPages = data.data.pages;
                renderPagination(data.data);
            } else {
                showFlashMessage('加载岗位列表失败', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showFlashMessage('网络错误，请稍后重试', 'danger');
        });
}

function renderJobList(jobs) {
    const jobList = document.getElementById('jobList');
    
    if (jobs.length === 0) {
        jobList.innerHTML = `
            <div class="empty-state">
                <p>暂无岗位数据，请先启动爬虫获取数据</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    jobs.forEach(job => {
        html += `
            <div class="job-item" onclick="showJobDetail(${job.id})">
                <div class="job-info">
                    <h4 class="job-title">${escapeHtml(job.job_name)}</h4>
                    <div class="job-meta">
                        <span>${escapeHtml(job.location || '未知')}</span>
                        <span>${escapeHtml(job.experience || '未知')}</span>
                        <span>${escapeHtml(job.education || '未知')}</span>
                    </div>
                    <div class="job-company">${escapeHtml(job.company_name || '未知公司')}</div>
                    ${job.detail_url ? `<a href="${escapeHtml(job.detail_url)}" target="_blank" class="job-detail-link" onclick="event.stopPropagation()">查看岗位详情</a>` : ''}
                </div>
                <div class="job-salary">${escapeHtml(job.job_salary || '面议')}</div>
            </div>
        `;
    });
    
    jobList.innerHTML = html;
}

function renderPagination(data) {
    const pagination = document.getElementById('pagination');
    
    if (data.pages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    
    html += `<button ${!data.has_prev ? 'disabled' : ''} onclick="loadJobs(${currentPage - 1})">上一页</button>`;
    
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(data.pages, currentPage + 2);
    
    if (startPage > 1) {
        html += `<button onclick="loadJobs(1)">1</button>`;
        if (startPage > 2) {
            html += `<span class="page-info">...</span>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="${i === currentPage ? 'active' : ''}" onclick="loadJobs(${i})">${i}</button>`;
    }
    
    if (endPage < data.pages) {
        if (endPage < data.pages - 1) {
            html += `<span class="page-info">...</span>`;
        }
        html += `<button onclick="loadJobs(${data.pages})">${data.pages}</button>`;
    }
    
    html += `<button ${!data.has_next ? 'disabled' : ''} onclick="loadJobs(${currentPage + 1})">下一页</button>`;
    
    pagination.innerHTML = html;
}

function showJobDetail(jobId) {
    fetch(`/dashboard/jobs/${jobId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const job = data.data;
                const modalBody = document.getElementById('modalBody');
                
                modalBody.innerHTML = `
                    <div class="job-detail-section">
                        <div class="detail-grid">
                            <div class="detail-item">
                                <span class="label">职位名称：</span>
                                <span class="value">${escapeHtml(job.job_name)}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">薪资范围：</span>
                                <span class="value" style="color: #f56c6c;">${escapeHtml(job.job_salary || '面议')}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">工作地点：</span>
                                <span class="value">${escapeHtml(job.location || '未知')}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">工作经验：</span>
                                <span class="value">${escapeHtml(job.experience || '未知')}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">学历要求：</span>
                                <span class="value">${escapeHtml(job.education || '未知')}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">公司名称：</span>
                                <span class="value">${escapeHtml(job.company_name || '未知')}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">所属行业：</span>
                                <span class="value">${escapeHtml(job.industry || '未知')}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">公司性质：</span>
                                <span class="value">${escapeHtml(job.company_type || '未知')}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">公司规模：</span>
                                <span class="value">${escapeHtml(job.company_size || '未知')}</span>
                            </div>
                        </div>
                        ${job.detail_url ? `<div class="detail-link-wrapper"><a href="${escapeHtml(job.detail_url)}" target="_blank" class="detail-link">查看岗位详情页</a></div>` : ''}
                    </div>
                    <div class="job-detail-section">
                        <h4>职位描述</h4>
                        <p>${escapeHtml(job.job_description || '暂无描述')}</p>
                    </div>
                `;
                
                document.getElementById('modalTitle').textContent = job.job_name;
                document.getElementById('jobDetailModal').classList.add('show');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showFlashMessage('加载岗位详情失败', 'danger');
        });
}

function closeModal() {
    document.getElementById('jobDetailModal').classList.remove('show');
}

document.addEventListener('click', function(e) {
    const modal = document.getElementById('jobDetailModal');
    if (e.target === modal) {
        closeModal();
    }
});

function startCrawler() {
    const keyword = document.getElementById('crawler-keyword').value.trim();
    const maxJobs = document.getElementById('crawler-count').value;
    
    if (!keyword) {
        showFlashMessage('请输入搜索关键词', 'warning');
        return;
    }
    
    const startBtn = document.getElementById('startCrawlerBtn');
    const stopBtn = document.getElementById('stopCrawlerBtn');
    
    startBtn.disabled = true;
    stopBtn.disabled = false;
    
    fetch('/api/crawler/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            keyword: keyword,
            max_jobs: parseInt(maxJobs)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showFlashMessage(data.message, 'success');
            document.getElementById('crawlerStatus').style.display = 'block';
            startStatusCheck();
        } else {
            showFlashMessage(data.message, 'danger');
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showFlashMessage('启动爬虫失败', 'danger');
        startBtn.disabled = false;
        stopBtn.disabled = true;
    });
}

function stopCrawler() {
    fetch('/api/crawler/stop', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        showFlashMessage(data.message, 'info');
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function startStatusCheck() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    statusCheckInterval = setInterval(checkCrawlerStatus, 2000);
}

function checkCrawlerStatus() {
    fetch('/api/crawler/status')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const status = data.data;
                
                document.getElementById('statusMessage').textContent = status.message;
                
                if (status.total > 0) {
                    const progress = Math.round((status.progress / status.total) * 100);
                    document.getElementById('crawlerProgress').style.width = progress + '%';
                    document.getElementById('progressText').textContent = progress + '%';
                }
                
                if (!status.is_running) {
                    clearInterval(statusCheckInterval);
                    statusCheckInterval = null;
                    
                    document.getElementById('startCrawlerBtn').disabled = false;
                    document.getElementById('stopCrawlerBtn').disabled = true;
                    
                    setTimeout(() => {
                        loadJobs(1);
                    }, 1000);
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function showPlaceholder(message) {
    showFlashMessage(message, 'info');
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
