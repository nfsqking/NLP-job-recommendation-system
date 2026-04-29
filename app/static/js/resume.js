/* 简历模块 JavaScript */

var itemTemplates = {
    education: `
        <div class="item-row" data-type="education">
            <div class="form-row">
                <div class="form-group">
                    <label>学校名称</label>
                    <input type="text" name="education_school" class="form-control" placeholder="请输入学校名称" maxlength="200">
                </div>
                <div class="form-group">
                    <label>专业</label>
                    <input type="text" name="education_major" class="form-control" placeholder="请输入专业名称" maxlength="100">
                </div>
            </div>
            <button type="button" class="btn btn-delete" onclick="removeItem(this, 'education')">删除</button>
        </div>
    `,
    internship: `
        <div class="item-row" data-type="internship">
            <div class="form-row">
                <div class="form-group">
                    <label>公司名称</label>
                    <input type="text" name="internship_company" class="form-control" placeholder="请输入实习公司名称（选填）" maxlength="200">
                </div>
                <div class="form-group">
                    <label>职位</label>
                    <input type="text" name="internship_position" class="form-control" placeholder="请输入实习职位（选填）" maxlength="100">
                </div>
            </div>
            <div class="form-group full-width">
                <label>工作内容</label>
                <textarea name="internship_content" class="form-control" rows="3" placeholder="请描述实习工作内容（选填）" maxlength="1000"></textarea>
            </div>
            <button type="button" class="btn btn-delete" onclick="removeItem(this, 'internship')">删除</button>
        </div>
    `,
    work: `
        <div class="item-row" data-type="work">
            <div class="form-row">
                <div class="form-group">
                    <label>公司名称</label>
                    <input type="text" name="work_company" class="form-control" placeholder="请输入工作公司名称（选填）" maxlength="200">
                </div>
                <div class="form-group">
                    <label>职位</label>
                    <input type="text" name="work_position" class="form-control" placeholder="请输入工作职位（选填）" maxlength="100">
                </div>
            </div>
            <div class="form-group full-width">
                <label>工作内容</label>
                <textarea name="work_content" class="form-control" rows="3" placeholder="请描述工作内容（选填）" maxlength="1000"></textarea>
            </div>
            <button type="button" class="btn btn-delete" onclick="removeItem(this, 'work')">删除</button>
        </div>
    `,
    project: `
        <div class="item-row" data-type="project">
            <div class="form-group">
                <label>项目名称</label>
                <input type="text" name="project_name" class="form-control" placeholder="请输入项目名称（选填）" maxlength="200">
            </div>
            <div class="form-group full-width">
                <label>项目内容</label>
                <textarea name="project_content" class="form-control" rows="3" placeholder="请描述项目内容（选填）" maxlength="1000"></textarea>
            </div>
            <button type="button" class="btn btn-delete" onclick="removeItem(this, 'project')">删除</button>
        </div>
    `
};

function addItem(type) {
    var container = document.getElementById(type + '-container');
    var div = document.createElement('div');
    div.innerHTML = itemTemplates[type].trim();
    var itemRow = div.firstChild;
    container.appendChild(itemRow);
    updateDeleteButtons(type);
}

function removeItem(btn, type) {
    var container = document.getElementById(type + '-container');
    var items = container.querySelectorAll('.item-row');
    
    if (type === 'education' && items.length <= 1) {
        alert('教育经历至少保留一条');
        return;
    }
    
    var itemRow = btn.closest('.item-row');
    itemRow.remove();
    updateDeleteButtons(type);
}

function updateDeleteButtons(type) {
    var container = document.getElementById(type + '-container');
    var items = container.querySelectorAll('.item-row');
    var deleteButtons = container.querySelectorAll('.btn-delete');
    
    if (type === 'education') {
        deleteButtons.forEach(function(btn, index) {
            btn.style.display = items.length > 1 ? 'inline-block' : 'none';
        });
    } else {
        deleteButtons.forEach(function(btn) {
            btn.style.display = 'inline-block';
        });
    }
}

function clearContainer(type) {
    var container = document.getElementById(type + '-container');
    container.innerHTML = '';
}

function loadData() {
    var data = typeof resumeData !== 'undefined' ? resumeData : {};
    
    if (data.education && data.education.length > 0) {
        data.education.forEach(function(item, index) {
            addItem('education');
            var container = document.getElementById('education-container');
            var lastItem = container.lastElementChild;
            lastItem.querySelector('input[name="education_school"]').value = item.school || '';
            lastItem.querySelector('input[name="education_major"]').value = item.major || '';
        });
    } else {
        addItem('education');
    }
    
    if (data.internship && data.internship.length > 0) {
        data.internship.forEach(function(item, index) {
            addItem('internship');
            var container = document.getElementById('internship-container');
            var lastItem = container.lastElementChild;
            lastItem.querySelector('input[name="internship_company"]').value = item.company || '';
            lastItem.querySelector('input[name="internship_position"]').value = item.position || '';
            lastItem.querySelector('textarea[name="internship_content"]').value = item.content || '';
        });
    }
    
    if (data.work && data.work.length > 0) {
        data.work.forEach(function(item, index) {
            addItem('work');
            var container = document.getElementById('work-container');
            var lastItem = container.lastElementChild;
            lastItem.querySelector('input[name="work_company"]').value = item.company || '';
            lastItem.querySelector('input[name="work_position"]').value = item.position || '';
            lastItem.querySelector('textarea[name="work_content"]').value = item.content || '';
        });
    }
    
    if (data.project && data.project.length > 0) {
        data.project.forEach(function(item, index) {
            addItem('project');
            var container = document.getElementById('project-container');
            var lastItem = container.lastElementChild;
            lastItem.querySelector('input[name="project_name"]').value = item.name || '';
            lastItem.querySelector('textarea[name="project_content"]').value = item.content || '';
        });
    }
}

function fillFormWithData(data) {
    if (!data) return;
    
    if (data.resume_name) {
        document.getElementById('resume_name').value = data.resume_name;
    }
    
    clearContainer('education');
    clearContainer('internship');
    clearContainer('work');
    clearContainer('project');
    
    if (data.education && data.education.length > 0) {
        data.education.forEach(function(item) {
            addItem('education');
            var container = document.getElementById('education-container');
            var lastItem = container.lastElementChild;
            lastItem.querySelector('input[name="education_school"]').value = item.school || '';
            lastItem.querySelector('input[name="education_major"]').value = item.major || '';
        });
    } else {
        addItem('education');
    }
    
    if (data.internship && data.internship.length > 0) {
        data.internship.forEach(function(item) {
            addItem('internship');
            var container = document.getElementById('internship-container');
            var lastItem = container.lastElementChild;
            lastItem.querySelector('input[name="internship_company"]').value = item.company || '';
            lastItem.querySelector('input[name="internship_position"]').value = item.position || '';
            lastItem.querySelector('textarea[name="internship_content"]').value = item.content || '';
        });
    }
    
    if (data.work && data.work.length > 0) {
        data.work.forEach(function(item) {
            addItem('work');
            var container = document.getElementById('work-container');
            var lastItem = container.lastElementChild;
            lastItem.querySelector('input[name="work_company"]').value = item.company || '';
            lastItem.querySelector('input[name="work_position"]').value = item.position || '';
            lastItem.querySelector('textarea[name="work_content"]').value = item.content || '';
        });
    }
    
    if (data.project && data.project.length > 0) {
        data.project.forEach(function(item) {
            addItem('project');
            var container = document.getElementById('project-container');
            var lastItem = container.lastElementChild;
            lastItem.querySelector('input[name="project_name"]').value = item.name || '';
            lastItem.querySelector('textarea[name="project_content"]').value = item.content || '';
        });
    }
    
    if (data.skills) {
        document.getElementById('skills').value = data.skills;
    }
    
    if (data.self_evaluation) {
        document.getElementById('self_evaluation').value = data.self_evaluation;
    }
}

function initFileUpload() {
    var uploadBtn = document.getElementById('uploadBtn');
    var fileInput = document.getElementById('resumeFile');
    var fileName = document.getElementById('fileName');
    var uploadProgress = document.getElementById('uploadProgress');
    var progressFill = document.getElementById('progressFill');
    var progressText = document.getElementById('progressText');
    
    if (!uploadBtn || !fileInput) return;
    
    uploadBtn.addEventListener('click', function() {
        fileInput.click();
    });
    
    fileInput.addEventListener('change', function() {
        var file = fileInput.files[0];
        if (!file) return;
        
        var ext = file.name.split('.').pop().toLowerCase();
        if (ext !== 'pdf' && ext !== 'docx') {
            alert('请上传 .pdf 或 .docx 格式的文件');
            fileInput.value = '';
            return;
        }
        
        if (file.size > 10 * 1024 * 1024) {
            alert('文件大小不能超过 10MB');
            fileInput.value = '';
            return;
        }
        
        fileName.textContent = file.name;
        uploadProgress.style.display = 'block';
        progressFill.style.width = '30%';
        progressText.textContent = '正在解析文件...';
        
        var formData = new FormData();
        formData.append('file', file);
        
        fetch('/resume/api/parse', {
            method: 'POST',
            body: formData
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.success) {
                progressFill.style.width = '100%';
                progressText.textContent = '解析成功！';
                
                setTimeout(function() {
                    uploadProgress.style.display = 'none';
                    progressFill.style.width = '0%';
                }, 1500);
                
                fillFormWithData(data.data);
            } else {
                progressFill.style.width = '100%';
                progressFill.style.background = '#f56c6c';
                progressText.textContent = data.message || '解析失败';
                
                setTimeout(function() {
                    uploadProgress.style.display = 'none';
                    progressFill.style.width = '0%';
                    progressFill.style.background = '';
                }, 3000);
            }
        })
        .catch(function(error) {
            console.error('Error:', error);
            progressFill.style.width = '100%';
            progressFill.style.background = '#f56c6c';
            progressText.textContent = '网络错误，请重试';
            
            setTimeout(function() {
                uploadProgress.style.display = 'none';
                progressFill.style.width = '0%';
                progressFill.style.background = '';
            }, 3000);
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    loadData();
    initFileUpload();
    
    var resumeForm = document.getElementById('resumeForm');
    var resetBtn = document.getElementById('resetBtn');
    
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            if (confirm('确定要重置表单吗？所有未保存的内容将被清空。')) {
                var containers = ['education', 'internship', 'work', 'project'];
                containers.forEach(function(type) {
                    var container = document.getElementById(type + '-container');
                    container.innerHTML = '';
                });
                
                document.getElementById('skills').value = '';
                document.getElementById('self_evaluation').value = '';
                document.getElementById('resume_name').value = '';
                
                var fileInput = document.getElementById('resumeFile');
                var fileName = document.getElementById('fileName');
                if (fileInput) fileInput.value = '';
                if (fileName) fileName.textContent = '未选择文件';
                
                addItem('education');
            }
        });
    }
    
    if (resumeForm) {
        resumeForm.addEventListener('submit', function(e) {
            var educationContainer = document.getElementById('education-container');
            var educationItems = educationContainer.querySelectorAll('.item-row');
            var hasEducationError = false;
            
            educationItems.forEach(function(item) {
                var school = item.querySelector('input[name="education_school"]');
                var major = item.querySelector('input[name="education_major"]');
                
                if (!school.value.trim() || !major.value.trim()) {
                    hasEducationError = true;
                }
            });
            
            var skills = document.getElementById('skills');
            var selfEvaluation = document.getElementById('self_evaluation');
            
            if (hasEducationError) {
                e.preventDefault();
                alert('请填写完整的教育经历（学校名称和专业为必填项）');
                return false;
            }
            
            if (!skills.value.trim()) {
                e.preventDefault();
                alert('个人技能不能为空');
                return false;
            }
            
            if (!selfEvaluation.value.trim()) {
                e.preventDefault();
                alert('个人评价不能为空');
                return false;
            }
        });
    }
});

function showPlaceholder(message) {
    alert(message);
}
