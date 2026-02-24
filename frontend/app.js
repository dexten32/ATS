document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const jdInput = document.getElementById('jd-input');
    const analyzeBtn = document.getElementById('analyze-btn');
    const clearJdBtn = document.getElementById('clear-jd-btn');
    const fileInfo = document.getElementById('file-info');
    const resultSection = document.getElementById('result-section');
    const loader = document.getElementById('loader');

    let selectedFile = null;

    // Drag and Drop Logic
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('active');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('active');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('active');
        if (e.dataTransfer.files.length) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFileSelect(e.target.files[0]);
        }
    });

    function handleFileSelect(file) {
        selectedFile = file;
        fileInfo.textContent = `Selected: ${file.name}`;
        fileInfo.classList.add('active');
    }

    // Clear JD Logic
    clearJdBtn?.addEventListener('click', () => {
        jdInput.value = '';
        console.log("Job Description cleared");
    });

    // Analysis Logic
    analyzeBtn.addEventListener('click', async () => {
        const jd = jdInput.value.trim();

        if (!selectedFile) {
            alert('Please upload a resume first.');
            return;
        }
        if (!jd) {
            alert('Please paste a job description.');
            return;
        }

        // Prepare Data
        const formData = new FormData();
        formData.append('resume_file', selectedFile);
        formData.append('job_description', jd);

        // Show Loader
        loader.classList.remove('hidden');
        analyzeBtn.disabled = true;

        try {
            const response = await fetch('/api/v1/analyze', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Failed to analyze resume');

            const data = await response.json();
            displayResults(data);
        } catch (error) {
            console.error(error);
            alert('Error connecting to backend. Make sure it is running at localhost:8000');
        } finally {
            loader.classList.add('hidden');
            analyzeBtn.disabled = false;
        }
    });

    function displayResults(data) {
        resultSection.classList.remove('hidden');

        // Update Score Circular Progress
        const scoreValue = document.getElementById('score-value');
        const scoreProgress = document.getElementById('score-progress');
        const finalScore = data.score;

        let currentScore = 0;
        const timer = setInterval(() => {
            if (currentScore >= finalScore) {
                clearInterval(timer);
            }
            scoreValue.textContent = `${Math.round(currentScore)}%`;
            scoreProgress.style.background = `conic-gradient(#6366f1 ${currentScore * 3.6}deg, #1e293b 0deg)`;
            currentScore++;
        }, 15);

        // Update Detail Bars
        document.getElementById('skill-bar').style.width = `${data.skill_match}%`;
        document.getElementById('ds-bar').style.width = `${data.domain_seniority_match}%`;
        document.getElementById('semantic-bar').style.width = `${data.semantic_match}%`;
        document.getElementById('exp-bar').style.width = `${data.exp_match}%`;

        // Update Maturity Breakdown
        const dMat = data.detailed_maturity;
        if (dMat) {
            document.getElementById('arch-bar').style.width = `${dMat.architecture}%`;
            document.getElementById('prod-bar').style.width = `${dMat.production}%`;
            document.getElementById('soft-bar').style.width = `${dMat.soft_skills}%`;
            document.getElementById('fe-bar').style.width = `${dMat.frontend}%`;
        }

        // Confidence Badge & Value
        const badge = document.getElementById('confidence-badge');
        badge.textContent = `${data.confidence} Confidence`;
        badge.style.background = data.confidence === 'High' ? '#22c55e' : (data.confidence === 'Medium' ? '#f59e0b' : '#ef4444');

        const confValText = document.getElementById('confidence-value');
        if (confValText) {
            confValText.textContent = `${Math.round(data.confidence_value)}% Parsing Certainty`;
            confValText.style.display = 'block';
            confValText.style.fontSize = '0.8rem';
            confValText.style.opacity = '0.7';
            confValText.style.marginTop = '0.5rem';
        }

        // Feedback
        const feedbackContainer = document.getElementById('feedback-content');
        feedbackContainer.innerHTML = '';

        if (data.feedback.suggestions.length) {
            const h4 = document.createElement('h4');
            h4.textContent = 'A.I. Strategic Insights:';
            feedbackContainer.appendChild(h4);

            data.feedback.suggestions.forEach(s => {
                const item = document.createElement('div');
                item.className = 'feedback-item';
                item.style.padding = '0.8rem';
                item.style.background = 'rgba(255,255,255,0.03)';
                item.style.borderLeft = '3px solid #6366f1';
                item.style.marginBottom = '0.5rem';
                item.style.borderRadius = '4px';
                item.style.fontSize = '0.9rem';
                item.textContent = s;
                feedbackContainer.appendChild(item);
            });
        }

        if (data.feedback.strengths.length) {
            const h4 = document.createElement('h4');
            h4.textContent = 'Top Matched Skills:';
            h4.style.marginTop = '1rem';
            feedbackContainer.appendChild(h4);

            const strengthBox = document.createElement('div');
            strengthBox.style.display = 'flex';
            strengthBox.style.flexWrap = 'wrap';
            strengthBox.style.gap = '0.5rem';
            strengthBox.style.marginTop = '0.5rem';

            data.feedback.strengths.forEach(skill => {
                const s = document.createElement('span');
                s.className = 'badge';
                s.style.background = 'rgba(99, 102, 241, 0.2)';
                s.style.color = '#a5b4fc';
                s.textContent = skill;
                strengthBox.appendChild(s);
            });
            feedbackContainer.appendChild(strengthBox);
        }

        // Scroll to results
        resultSection.scrollIntoView({ behavior: 'smooth' });
    }
});
