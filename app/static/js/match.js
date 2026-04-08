document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    initJobSelection();
    initSearch();
    initMatchActions();
    initScoreCircles();
    initDetailView();
});

function initTabs() {
    const tabBtns = document.querySelectorAll('.match-tabs .tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            
            tabBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            if (tabName === 'select') {
                document.getElementById('selectTab').classList.add('active');
            } else {
                document.getElementById('resultTab').classList.add('active');
            }
        });
    });
}

function initJobSelection() {
    const selectAllBtn = document.getElementById('selectAllBtn');
    const invertSelectBtn = document.getElementById('invertSelectBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function() {
            const checkboxes = document.querySelectorAll('.job-checkbox');
            const allChecked = Array.from(checkboxes).every(cb => cb.checked);
            checkboxes.forEach(cb => cb.checked = !allChecked);
            updateAnalyzeButton();
            updateSelectAllBtnText();
        });
    }
    
    if (invertSelectBtn) {
        invertSelectBtn.addEventListener('click', function() {
            const checkboxes = document.querySelectorAll('.job-checkbox');
            checkboxes.forEach(cb => cb.checked = !cb.checked);
            updateAnalyzeButton();
        });
    }
    
    document.querySelectorAll('.job-checkbox').forEach(cb => {
        cb.addEventListener('change', updateAnalyzeButton);
    });
    
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', startAnalysis);
    }
}

function updateAnalyzeButton() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    const checkedCount = document.querySelectorAll('.job-checkbox:checked').length;
    
    if (analyzeBtn) {
        analyzeBtn.disabled = checkedCount === 0;
        analyzeBtn.textContent = checkedCount > 0 
            ? `开始相似度分析 (${checkedCount}个岗位)` 
            : '开始相似度分析';
    }
}

function updateSelectAllBtnText() {
    const selectAllBtn = document.getElementById('selectAllBtn');
    const checkboxes = document.querySelectorAll('.job-checkbox');
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);
    
    if (selectAllBtn) {
        selectAllBtn.textContent = allChecked ? '取消全选' : '全选';
    }
}

function initSearch() {
    const searchBtn = document.getElementById('searchBtn');
    const resetSearchBtn = document.getElementById('resetSearchBtn');
    
    if (searchBtn) {
        searchBtn.addEventListener('click', searchJobs);
    }
    
    if (resetSearchBtn) {
        resetSearchBtn.addEventListener('click', function() {
            document.getElementById('searchKeyword').value = '';
            document.getElementById('searchLocation').value = '';
            location.reload();
        });
    }
}

function searchJobs() {
    const keyword = document.getElementById('searchKeyword').value.trim();
    const location = document.getElementById('searchLocation').value.trim();
    
    const params = new URLSearchParams();
    if (keyword) params.append('keyword', keyword);
    if (location) params.append('location', location);
    
    showLoading();
    
    fetch(`/api/jobs?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                renderJobList(data.jobs);
            } else {
                alert('搜索失败：' + (data.message || '未知错误'));
            }
        })
        .catch(error => {
            hideLoading();
            console.error('搜索出错:', error);
            alert('搜索出错，请重试');
        });
}

function renderJobList(jobs) {
    const container = document.getElementById('jobSelectList');
    const jobCount = document.getElementById('jobCount');
    
    if (!container) return;
    
    jobCount.textContent = `共 ${jobs.length} 条记录`;
    
    if (jobs.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>未找到符合条件的岗位</p></div>';
        return;
    }
    
    let html = '';
    jobs.forEach(job => {
        const isMatched = matchedJobIds && matchedJobIds.includes(job.id);
        html += `
            <div class="job-select-item" data-job-id="${job.id}">
                <label class="checkbox-wrapper">
                    <input type="checkbox" class="job-checkbox" value="${job.id}">
                    <span class="checkmark"></span>
                </label>
                <div class="job-info">
                    <div class="job-title">
                        <h4>${escapeHtml(job.job_name)}</h4>
                        <span class="company">${escapeHtml(job.company_name || '')}</span>
                    </div>
                    <div class="job-meta">
                        <span class="meta-item">${escapeHtml(job.job_salary || '面议')}</span>
                        <span class="meta-item">${escapeHtml(job.location || '未知')}</span>
                        <span class="meta-item">${escapeHtml(job.experience || '不限')}</span>
                    </div>
                </div>
                ${isMatched ? '<span class="matched-badge">已匹配</span>' : ''}
            </div>
        `;
    });
    
    container.innerHTML = html;
    
    document.querySelectorAll('.job-checkbox').forEach(cb => {
        cb.addEventListener('change', updateAnalyzeButton);
    });
    
    updateAnalyzeButton();
}

function initMatchActions() {
    const selectAllResultBtn = document.getElementById('selectAllResultBtn');
    const deleteSelectedBtn = document.getElementById('deleteSelectedBtn');
    const clearAllBtn = document.getElementById('clearAllBtn');
    
    if (selectAllResultBtn) {
        selectAllResultBtn.addEventListener('click', function() {
            const checkboxes = document.querySelectorAll('.result-checkbox');
            const allChecked = Array.from(checkboxes).every(cb => cb.checked);
            checkboxes.forEach(cb => cb.checked = !allChecked);
            updateDeleteButton();
        });
    }
    
    document.querySelectorAll('.result-checkbox').forEach(cb => {
        cb.addEventListener('change', updateDeleteButton);
    });
    
    if (deleteSelectedBtn) {
        deleteSelectedBtn.addEventListener('click', function() {
            const matchIds = Array.from(document.querySelectorAll('.result-checkbox:checked'))
                .map(cb => parseInt(cb.value));
            
            if (matchIds.length === 0) {
                alert('请选择要删除的记录');
                return;
            }
            
            showConfirm(`确定要删除选中的 ${matchIds.length} 条记录吗？`, function() {
                deleteMatches(matchIds);
            });
        });
    }
    
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', function() {
            showConfirm('确定要清空所有匹配记录吗？此操作不可恢复！', function() {
                clearAllMatches();
            });
        });
    }
}

function updateDeleteButton() {
    const deleteSelectedBtn = document.getElementById('deleteSelectedBtn');
    const checkedCount = document.querySelectorAll('.result-checkbox:checked').length;
    
    if (deleteSelectedBtn) {
        deleteSelectedBtn.disabled = checkedCount === 0;
    }
}

function startAnalysis() {
    const jobIds = Array.from(document.querySelectorAll('.job-checkbox:checked'))
        .map(cb => parseInt(cb.value));
    
    if (jobIds.length === 0) {
        alert('请选择至少一个岗位进行分析');
        return;
    }
    
    showLoadingOverlay();
    
    fetch('/api/match/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ job_ids: jobIds })
    })
    .then(response => response.json())
    .then(data => {
        hideLoadingOverlay();
        if (data.success) {
            alert(data.message);
            location.reload();
        } else {
            alert('分析失败：' + (data.message || '未知错误'));
        }
    })
    .catch(error => {
        hideLoadingOverlay();
        console.error('分析出错:', error);
        alert('分析出错，请重试');
    });
}

function deleteMatches(matchIds) {
    fetch('/api/match/delete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ match_ids: matchIds })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            matchIds.forEach(id => {
                const item = document.querySelector(`.match-result-item[data-match-id="${id}"]`);
                if (item) item.remove();
            });
            
            updateMatchCount();
            updateDeleteButton();
            
            if (document.querySelectorAll('.match-result-item').length === 0) {
                document.getElementById('matchResultList').innerHTML = 
                    '<div class="empty-state"><p>暂无匹配结果，请先选择岗位进行分析</p></div>';
            }
            
            alert(data.message);
        } else {
            alert('删除失败：' + (data.message || '未知错误'));
        }
    })
    .catch(error => {
        console.error('删除出错:', error);
        alert('删除出错，请重试');
    });
}

function clearAllMatches() {
    fetch('/api/match/clear', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('matchResultList').innerHTML = 
                '<div class="empty-state"><p>暂无匹配结果，请先选择岗位进行分析</p></div>';
            updateMatchCount();
            alert(data.message);
        } else {
            alert('清空失败：' + (data.message || '未知错误'));
        }
    })
    .catch(error => {
        console.error('清空出错:', error);
        alert('清空出错，请重试');
    });
}

function updateMatchCount() {
    const count = document.querySelectorAll('.match-result-item').length;
    document.getElementById('matchCount').textContent = `共 ${count} 条记录`;
    document.getElementById('resultCount').textContent = count;
}

function initScoreCircles() {
    document.querySelectorAll('.score-circle').forEach(el => {
        const score = parseFloat(el.dataset.score);
        let colorClass = 'low';
        if (score >= 70) {
            colorClass = 'high';
        } else if (score >= 40) {
            colorClass = 'medium';
        }
        el.classList.add(colorClass);
    });
}

function initDetailView() {
    document.querySelectorAll('.view-detail-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const jobId = this.dataset.jobId;
            showJobDetail(jobId);
        });
    });
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
            <div class="detail-desc">
                <h5>岗位描述</h5>
                <div class="desc-content">${escapeHtml(job.job_description || '暂无描述')}</div>
            </div>
        </div>
    `;
    
    document.getElementById('modalBody').innerHTML = html;
    document.getElementById('jobDetailModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('jobDetailModal').style.display = 'none';
}

function showConfirm(message, callback) {
    document.getElementById('confirmMessage').textContent = message;
    document.getElementById('confirmModal').style.display = 'flex';
    
    const confirmBtn = document.getElementById('confirmBtn');
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    
    newConfirmBtn.addEventListener('click', function() {
        closeConfirmModal();
        callback();
    });
}

function closeConfirmModal() {
    document.getElementById('confirmModal').style.display = 'none';
}

function showLoadingOverlay() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoadingOverlay() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

function showLoading() {
}

function hideLoading() {
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

document.getElementById('jobDetailModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});

document.getElementById('confirmModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeConfirmModal();
    }
});
