// Configuration - CHANGE THIS TO YOUR CLOUD RUN URL ONCE DEPLOYED!
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:8080' 
    : 'https://agentic-qa-fuzzer-251754336920.asia-south1.run.app';

// DOM Elements
const targetUrlInput = document.getElementById('targetUrl');
const fuzzBtn = document.getElementById('fuzzBtn');
const btnText = document.querySelector('.btn-text');
const spinner = document.querySelector('.spinner');

const resultsSection = document.getElementById('resultsSection');
const statusBadge = document.getElementById('statusBadge');
const resultMessage = document.getElementById('resultMessage');
const toolCallsCount = document.getElementById('toolCallsCount');
const codeContainer = document.getElementById('codeContainer');
const codeBlock = document.getElementById('codeBlock');
const downloadBtn = document.getElementById('downloadBtn');

let currentTestCode = null;

// Event Listeners
fuzzBtn.addEventListener('click', initiateFuzzing);
downloadBtn.addEventListener('click', downloadTestFile);

async function initiateFuzzing() {
    const targetUrl = targetUrlInput.value.trim();
    if (!targetUrl) {
        alert('Please enter a Target API URL.');
        return;
    }

    // Set UI state to loading
    setLoadingState(true);
    resultsSection.classList.add('hidden');
    codeContainer.classList.add('hidden');
    currentTestCode = null;

    try {
        const response = await fetch(`${API_BASE_URL}/api/fuzz`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_url: targetUrl })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to execute fuzzing session');
        }

        renderResults(data);
    } catch (error) {
        console.error('Error:', error);
        renderError(error.message);
    } finally {
        setLoadingState(false);
    }
}

function renderResults(data) {
    resultsSection.classList.remove('hidden');
    toolCallsCount.textContent = data.tool_calls_made;
    resultMessage.textContent = data.message;

    if (data.success && data.generated_test_code) {
        statusBadge.textContent = 'Vulnerability Found';
        statusBadge.className = 'badge success';
        
        currentTestCode = data.generated_test_code;
        codeBlock.textContent = currentTestCode;
        codeContainer.classList.remove('hidden');
    } else {
        statusBadge.textContent = 'No Crash Detected';
        statusBadge.className = 'badge';
    }
}

function renderError(message) {
    resultsSection.classList.remove('hidden');
    statusBadge.textContent = 'Error';
    statusBadge.className = 'badge error';
    resultMessage.textContent = message;
    toolCallsCount.textContent = '-';
}

function setLoadingState(isLoading) {
    targetUrlInput.disabled = isLoading;
    fuzzBtn.disabled = isLoading;
    
    if (isLoading) {
        btnText.textContent = 'Fuzzing in Progress...';
        spinner.classList.remove('hidden');
    } else {
        btnText.textContent = 'Commence Fuzzing';
        spinner.classList.add('hidden');
    }
}

function downloadTestFile() {
    if (!currentTestCode) return;
    
    const blob = new Blob([currentTestCode], { type: 'text/x-python' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    
    a.href = url;
    a.download = 'test_vulnerability.py';
    document.body.appendChild(a);
    a.click();
    
    // Cleanup
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
