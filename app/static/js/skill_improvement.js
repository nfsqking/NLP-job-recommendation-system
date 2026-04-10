document.addEventListener('DOMContentLoaded', function() {
    initGenerateButtons();
    initViewButtons();
    initDetailButtons();
    initCloseButton();
});

function initGenerateButtons() {
    document.querySelectorAll('.generate-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const jobId = this.dataset.jobId;
            generateSuggestion(jobId);
        });
    });
}

function initViewButtons() {
    document.querySelectorAll('.view-suggestion-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const jobId = this.dataset.jobId;
            viewSuggestion(jobId);
        });
    });
}

function initDetailButtons() {
    document.querySelectorAll('.view-detail-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const jobId = this.dataset.jobId;
            showJobDetail(jobId);
        });
    });
}

function initCloseButton() {
    const closeBtn = document.getElementById('closeSuggestionBtn');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            document.getElementById('suggestionPanel').style.display = 'none';
        });
    }
}

function generateSuggestion(jobId) {
    const job = jobData[jobId];
    const jobName = job ? job.job_name : '';
    const companyName = job ? job.company_name : '';
    
    const panel = document.getElementById('suggestionPanel');
    const jobNameEl = document.getElementById('suggestionJobName');
    const contentEl = document.getElementById('suggestionContent');
    
    if (jobName && companyName) {
        jobNameEl.textContent = `${jobName} - ${companyName}`;
    } else if (jobName) {
        jobNameEl.textContent = jobName;
    } else {
        jobNameEl.textContent = '';
    }
    
    contentEl.innerHTML = '<div class="streaming-indicator">正在生成建议...</div>';
    panel.style.display = 'block';
    panel.scrollIntoView({ behavior: 'smooth' });
    
    fetch('/api/suggestion/stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            job_id: parseInt(jobId)
        })
    })
    .then(response => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullContent = '';
        
        function scrollToBottom() {
            contentEl.scrollTop = contentEl.scrollHeight;
        }
        
        function read() {
            reader.read().then(({ done, value }) => {
                if (done) {
                    updateButtonToView(jobId);
                    scrollToBottom();
                    return;
                }
                
                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');
                
                lines.forEach(line => {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.slice(6).trim();
                        if (dataStr === '[DONE]') {
                            if (fullContent && typeof marked !== 'undefined') {
                                contentEl.innerHTML = marked.parse(fullContent);
                            }
                            updateButtonToView(jobId);
                            scrollToBottom();
                            return;
                        }
                        
                        try {
                            const data = JSON.parse(dataStr);
                            if (data.error) {
                                contentEl.innerHTML = `<div class="error-message">生成失败：${escapeHtml(data.error)}</div>`;
                            } else if (data.existing) {
                                fullContent = data.suggestion;
                                if (typeof marked !== 'undefined') {
                                    contentEl.innerHTML = marked.parse(fullContent);
                                } else {
                                    contentEl.textContent = fullContent;
                                }
                                scrollToBottom();
                            } else if (data.content) {
                                fullContent += data.content;
                                if (typeof marked !== 'undefined') {
                                    contentEl.innerHTML = marked.parse(fullContent);
                                } else {
                                    contentEl.textContent = fullContent;
                                }
                                scrollToBottom();
                            }
                        } catch (e) {
                            console.error('Parse error:', e);
                        }
                    }
                });
                
                read();
            });
        }
        
        read();
    })
    .catch(error => {
        console.error('Error:', error);
        contentEl.innerHTML = `<div class="error-message">生成出错，请重试</div>`;
    });
}

function updateButtonToView(jobId) {
    const jobItem = document.querySelector(`.job-item[data-job-id="${jobId}"]`);
    if (jobItem) {
        const actionsDiv = jobItem.querySelector('.job-actions');
        const generateBtn = actionsDiv.querySelector('.generate-btn');
        if (generateBtn) {
            const viewBtn = document.createElement('button');
            viewBtn.className = 'btn btn-sm btn-primary view-suggestion-btn';
            viewBtn.dataset.jobId = jobId;
            viewBtn.textContent = '查看建议';
            viewBtn.addEventListener('click', function() {
                viewSuggestion(jobId);
            });
            generateBtn.replaceWith(viewBtn);
        }
    }
}

function viewSuggestion(jobId) {
    const job = jobData[jobId];
    const jobName = job ? job.job_name : '';
    const companyName = job ? job.company_name : '';
    
    fetch(`/api/suggestion/get?job_id=${jobId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displaySuggestion(
                    data.suggestion.suggestion_text,
                    jobName,
                    companyName
                );
            } else {
                alert('获取建议失败：' + (data.message || '未知错误'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('获取建议出错，请重试');
        });
}

function displaySuggestion(suggestionText, jobName, companyName) {
    const panel = document.getElementById('suggestionPanel');
    const jobNameEl = document.getElementById('suggestionJobName');
    const contentEl = document.getElementById('suggestionContent');
    
    if (jobName && companyName) {
        jobNameEl.textContent = `${jobName} - ${companyName}`;
    } else if (jobName) {
        jobNameEl.textContent = jobName;
    } else {
        jobNameEl.textContent = '';
    }
    
    if (typeof marked !== 'undefined' && suggestionText) {
        contentEl.innerHTML = marked.parse(suggestionText);
    } else {
        contentEl.textContent = suggestionText || '';
    }
    
    panel.style.display = 'block';
    panel.scrollIntoView({ behavior: 'smooth' });
}

function showJobDetail(jobId) {
    const job = jobData[jobId];
    if (!job) {
        alert('未找到岗位信息');
        return;
    }
    
    document.getElementById('modalTitle').textContent = job.job_name;
    
    let html = `
        <div class="job-detail">
            <div class="detail-header">
                <div class="company-info">
                    <h4>${escapeHtml(job.company_name)}</h4>
                    <p>${escapeHtml(job.industry)} ${job.company_type ? '| ' + escapeHtml(job.company_type) : ''} ${job.company_size ? '| ' + escapeHtml(job.company_size) : ''}</p>
                </div>
            </div>
            <div class="detail-info">
                <div class="info-row">
                    <span class="label">薪资：</span>
                    <span class="value">${escapeHtml(job.job_salary)}</span>
                </div>
                <div class="info-row">
                    <span class="label">地点：</span>
                    <span class="value">${escapeHtml(job.location)}</span>
                </div>
                <div class="info-row">
                    <span class="label">经验：</span>
                    <span class="value">${escapeHtml(job.experience)}</span>
                </div>
                <div class="info-row">
                    <span class="label">学历：</span>
                    <span class="value">${escapeHtml(job.education)}</span>
                </div>
            </div>
            ${job.detail_url ? `<div class="detail-link-wrapper"><a href="${escapeHtml(job.detail_url)}" target="_blank" class="detail-link">查看岗位详情页</a></div>` : ''}
            <div class="detail-desc">
                <h5>岗位描述</h5>
                <div class="desc-content">${escapeHtml(job.job_description || '暂无描述')}</div>
            </div>
        </div>
    `;
    
    document.getElementById('modalBody').innerHTML = html;
    document.getElementById('jobDetailModal').classList.add('show');
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

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
