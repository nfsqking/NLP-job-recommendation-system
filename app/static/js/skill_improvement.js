document.addEventListener('DOMContentLoaded', function() {
    initDetailButtons();
});

function initDetailButtons() {
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
