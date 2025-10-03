// AI Assistant Chat Interface

const API_BASE = window.location.origin;
const TENANT_ID = 'demo';

let selectedProjects = []; // Changed from currentProject to support multi-select
let currentIssue = null;
let messages = [];
let autocompleteActive = false;
let autocompleteType = null;
let autocompleteQuery = '';
let autocompleteStartPos = 0;
let selectedSuggestionIndex = -1;

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendButton = document.getElementById('sendButton');
const autocompleteDropdown = document.getElementById('autocompleteDropdown');
const projectList = document.getElementById('projectList');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadProjects();
    setupEventListeners();
});

// Load projects
async function loadProjects() {
    try {
        const response = await fetch(`${API_BASE}/v1/pulse/projects`, {
            headers: { 'X-Tenant-Id': TENANT_ID }
        });
        const data = await response.json();

        projectList.innerHTML = '';

        // Add "All Projects" option
        const allProjectsLi = document.createElement('li');
        allProjectsLi.className = 'project-item all-projects';
        allProjectsLi.dataset.key = 'ALL';
        allProjectsLi.innerHTML = `
            <div class="project-key">🌐</div>
            <div class="project-name">All Projects</div>
        `;
        allProjectsLi.addEventListener('click', () => toggleAllProjects());
        projectList.appendChild(allProjectsLi);

        // Add separator
        const separator = document.createElement('li');
        separator.className = 'project-separator';
        projectList.appendChild(separator);

        // Add individual projects
        data.projects.forEach(project => {
            const li = document.createElement('li');
            li.className = 'project-item';
            li.dataset.key = project.key;
            li.innerHTML = `
                <div class="project-key">${project.key}</div>
                <div class="project-name">${project.name}</div>
            `;
            li.addEventListener('click', () => toggleProject(project.key));
            projectList.appendChild(li);
        });
    } catch (error) {
        console.error('Failed to load projects:', error);
    }
}

// Toggle project selection
function toggleProject(projectKey) {
    const index = selectedProjects.indexOf(projectKey);

    if (index > -1) {
        // Deselect
        selectedProjects.splice(index, 1);
    } else {
        // Select
        selectedProjects.push(projectKey);
    }

    updateProjectUI();

    if (selectedProjects.length > 0) {
        const projectsText = selectedProjects.length === 1 ? selectedProjects[0] : `${selectedProjects.length} projektov`;
        addMessage('assistant', `Vybral si: ${projectsText}. Teraz môžeš používať / pre vyhľadávanie issues.`);
    }
}

// Toggle all projects
function toggleAllProjects() {
    const allProjectsItem = document.querySelector('.project-item.all-projects');

    if (allProjectsItem.classList.contains('active')) {
        // Deselect all
        selectedProjects = [];
    } else {
        // Select all
        selectedProjects = ['ALL'];
    }

    updateProjectUI();

    if (selectedProjects.includes('ALL')) {
        addMessage('assistant', 'Vybral si všetky projekty. Queries budú fungovať nad všetkými projektami.');
    }
}

// Update project UI
function updateProjectUI() {
    const allProjectsItem = document.querySelector('.project-item.all-projects');
    const isAllSelected = selectedProjects.includes('ALL');

    // Update "All Projects" item
    allProjectsItem.classList.toggle('active', isAllSelected);

    // Update individual project items
    document.querySelectorAll('.project-item:not(.all-projects)').forEach(item => {
        const projectKey = item.dataset.key;
        const isSelected = selectedProjects.includes(projectKey);
        item.classList.toggle('active', isSelected && !isAllSelected);

        // Disable individual selection if "All" is selected
        if (isAllSelected) {
            item.style.opacity = '0.5';
            item.style.pointerEvents = 'none';
        } else {
            item.style.opacity = '1';
            item.style.pointerEvents = 'auto';
        }
    });
}

// Setup event listeners
function setupEventListeners() {
    chatInput.addEventListener('input', handleInput);
    chatInput.addEventListener('keydown', handleKeyDown);
    sendButton.addEventListener('click', sendMessage);
    
    // Close autocomplete when clicking outside
    document.addEventListener('click', (e) => {
        if (!autocompleteDropdown.contains(e.target) && e.target !== chatInput) {
            hideAutocomplete();
        }
    });
}

// Handle input
function handleInput(e) {
    const text = chatInput.value;
    const cursorPos = chatInput.selectionStart;
    
    // Check for @ or / trigger
    const beforeCursor = text.substring(0, cursorPos);
    const lastAtPos = beforeCursor.lastIndexOf('@');
    const lastSlashPos = beforeCursor.lastIndexOf('/');
    
    // Check if we're in an autocomplete context
    if (lastAtPos > -1 && (lastSlashPos === -1 || lastAtPos > lastSlashPos)) {
        const afterAt = beforeCursor.substring(lastAtPos + 1);
        if (!afterAt.includes(' ')) {
            autocompleteType = 'user';
            autocompleteQuery = afterAt;
            autocompleteStartPos = lastAtPos;
            showAutocomplete();
            return;
        }
    }
    
    if (lastSlashPos > -1 && (lastAtPos === -1 || lastSlashPos > lastAtPos)) {
        const afterSlash = beforeCursor.substring(lastSlashPos + 1);
        if (!afterSlash.includes(' ')) {
            autocompleteType = 'issue';
            autocompleteQuery = afterSlash;
            autocompleteStartPos = lastSlashPos;
            showAutocomplete();
            return;
        }
    }
    
    hideAutocomplete();
}

// Handle key down
function handleKeyDown(e) {
    if (!autocompleteActive) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
        return;
    }
    
    const suggestions = autocompleteDropdown.querySelectorAll('.autocomplete-item');
    
    if (e.key === 'ArrowDown') {
        e.preventDefault();
        selectedSuggestionIndex = Math.min(selectedSuggestionIndex + 1, suggestions.length - 1);
        updateSelectedSuggestion();
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        selectedSuggestionIndex = Math.max(selectedSuggestionIndex - 1, -1);
        updateSelectedSuggestion();
    } else if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault();
        if (selectedSuggestionIndex >= 0 && suggestions[selectedSuggestionIndex]) {
            selectSuggestion(suggestions[selectedSuggestionIndex].dataset.id);
        }
    } else if (e.key === 'Escape') {
        hideAutocomplete();
    }
}

// Show autocomplete
async function showAutocomplete() {
    if (!autocompleteType || autocompleteQuery.length < 1) {
        hideAutocomplete();
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/v1/ai-assistant/autocomplete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Tenant-Id': TENANT_ID
            },
            body: JSON.stringify({
                query: autocompleteQuery,
                type: autocompleteType,
                project_keys: selectedProjects // Changed to support multi-select
            })
        });
        
        const data = await response.json();
        
        if (data.suggestions.length === 0) {
            hideAutocomplete();
            return;
        }
        
        autocompleteDropdown.innerHTML = '';
        data.suggestions.forEach((suggestion, index) => {
            const div = document.createElement('div');
            div.className = 'autocomplete-item';
            div.dataset.id = suggestion.id;
            div.innerHTML = `
                <div class="autocomplete-primary">${suggestion.display}</div>
                <div class="autocomplete-secondary">${suggestion.secondary}</div>
            `;
            div.addEventListener('click', () => selectSuggestion(suggestion.id));
            autocompleteDropdown.appendChild(div);
        });
        
        selectedSuggestionIndex = -1;
        autocompleteActive = true;
        autocompleteDropdown.classList.add('show');
    } catch (error) {
        console.error('Autocomplete failed:', error);
        hideAutocomplete();
    }
}

// Hide autocomplete
function hideAutocomplete() {
    autocompleteActive = false;
    autocompleteDropdown.classList.remove('show');
    selectedSuggestionIndex = -1;
}

// Update selected suggestion
function updateSelectedSuggestion() {
    const suggestions = autocompleteDropdown.querySelectorAll('.autocomplete-item');
    suggestions.forEach((item, index) => {
        item.classList.toggle('selected', index === selectedSuggestionIndex);
    });
}

// Select suggestion
function selectSuggestion(id) {
    const text = chatInput.value;
    const beforeTrigger = text.substring(0, autocompleteStartPos);
    const afterCursor = text.substring(chatInput.selectionStart);
    
    const trigger = autocompleteType === 'user' ? '@' : '/';
    chatInput.value = beforeTrigger + trigger + id + ' ' + afterCursor;
    
    const newCursorPos = beforeTrigger.length + trigger.length + id.length + 1;
    chatInput.setSelectionRange(newCursorPos, newCursorPos);
    
    hideAutocomplete();
    chatInput.focus();
}

// Send message
async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;
    
    // Add user message
    addMessage('user', text);
    chatInput.value = '';
    
    // Show loading
    const loadingId = addLoadingMessage();
    
    // Disable input
    chatInput.disabled = true;
    sendButton.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/v1/ai-assistant/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Tenant-Id': TENANT_ID
            },
            body: JSON.stringify({
                messages: messages,
                project_keys: selectedProjects, // Changed to support multi-select
                issue_key: currentIssue
            })
        });
        
        const data = await response.json();

        console.log('Chat response:', data); // Debug log

        // Remove loading
        removeLoadingMessage(loadingId);

        // Add assistant response with content (final response after tool calls)
        const finalContent = data.content || data.message;

        if (!finalContent) {
            console.error('No content in response:', data);
            addMessage('assistant', 'Prepáč, odpoveď neobsahuje žiadny obsah.');
        } else {
            addMessage('assistant', finalContent, data.tool_calls);
        }

    } catch (error) {
        console.error('Chat failed:', error);
        console.error('Error stack:', error.stack);
        removeLoadingMessage(loadingId);
        addMessage('assistant', `Prepáč, nastala chyba: ${error.message}`);
    } finally {
        chatInput.disabled = false;
        sendButton.disabled = false;
        chatInput.focus();
    }
}

// Add message
function addMessage(role, content, toolCalls = []) {
    messages.push({ role, content });
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? 'TY' : 'AI';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    const messageText = document.createElement('div');
    messageText.className = 'message-text';

    // Parse visualization blocks from AI response (only for assistant messages)
    if (role === 'assistant') {
        const visualizationParsed = parseVisualizationBlocks(content);

        if (visualizationParsed.hasVisualization) {
            // Add text before visualization
            if (visualizationParsed.textBefore) {
                const textDiv = document.createElement('div');
                textDiv.textContent = visualizationParsed.textBefore;
                messageText.appendChild(textDiv);
            }

            // Add visualization
            messageText.appendChild(visualizationParsed.visualization);

            // Add text after visualization
            if (visualizationParsed.textAfter) {
                const textDiv = document.createElement('div');
                textDiv.textContent = visualizationParsed.textAfter;
                textDiv.style.marginTop = '12px';
                messageText.appendChild(textDiv);
            }
        } else {
            // No visualization, just text
            messageText.textContent = content;
        }
    } else {
        // User message - just text
        messageText.textContent = content;
    }

    const messageTime = document.createElement('div');
    messageTime.className = 'message-time';
    messageTime.textContent = new Date().toLocaleTimeString('sk-SK', { hour: '2-digit', minute: '2-digit' });

    messageContent.appendChild(messageText);
    
    // Add tool calls if any
    if (toolCalls && toolCalls.length > 0) {
        toolCalls.forEach(tc => {
            const toolDiv = document.createElement('div');
            toolDiv.className = 'tool-call';

            const toolHeader = document.createElement('div');
            toolHeader.className = 'tool-call-name';
            toolHeader.textContent = `🔧 ${tc.function_name}`;
            toolDiv.appendChild(toolHeader);

            const toolStatus = document.createElement('div');
            toolStatus.className = 'tool-call-status';
            toolStatus.textContent = tc.result.success ? '✅ Úspešne vykonané' : '❌ Chyba: ' + tc.result.error;
            toolDiv.appendChild(toolStatus);

            // Display result data
            if (tc.result.success && tc.result.result) {
                const resultDiv = document.createElement('div');
                resultDiv.className = 'tool-call-result';
                resultDiv.appendChild(formatToolResult(tc.function_name, tc.result.result));
                toolDiv.appendChild(resultDiv);
            }

            // Add undo button for write operations with checkpoint
            if (tc.result.success && tc.result.checkpoint_id) {
                const undoButton = document.createElement('button');
                undoButton.className = 'undo-button';
                undoButton.textContent = '↶ Vrátiť späť';
                undoButton.onclick = () => rollbackCheckpoint(tc.result.checkpoint_id, toolDiv);
                toolDiv.appendChild(undoButton);
            }

            messageContent.appendChild(toolDiv);
        });
    }
    
    messageContent.appendChild(messageTime);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Add loading message
function addLoadingMessage() {
    const id = 'loading-' + Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    messageDiv.id = id;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = 'AI';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.innerHTML = `
        <div class="loading">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
    `;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return id;
}

// Remove loading message
function removeLoadingMessage(id) {
    const element = document.getElementById(id);
    if (element) {
        element.remove();
    }
}

// Parse visualization blocks from AI response
function parseVisualizationBlocks(content) {
    // Look for ```visualization:chart or ```visualization:table blocks
    const chartRegex = /```visualization:chart\s*\n([\s\S]*?)\n```/;
    const tableRegex = /```visualization:table\s*\n([\s\S]*?)\n```/;

    const chartMatch = content.match(chartRegex);
    const tableMatch = content.match(tableRegex);

    if (chartMatch) {
        try {
            const data = JSON.parse(chartMatch[1]);
            const textBefore = content.substring(0, chartMatch.index).trim();
            const textAfter = content.substring(chartMatch.index + chartMatch[0].length).trim();

            return {
                hasVisualization: true,
                textBefore,
                textAfter,
                visualization: createChartFromAI(data)
            };
        } catch (e) {
            console.error('Failed to parse chart visualization:', e);
        }
    }

    if (tableMatch) {
        try {
            const data = JSON.parse(tableMatch[1]);
            const textBefore = content.substring(0, tableMatch.index).trim();
            const textAfter = content.substring(tableMatch.index + tableMatch[0].length).trim();

            return {
                hasVisualization: true,
                textBefore,
                textAfter,
                visualization: createTableFromAI(data)
            };
        } catch (e) {
            console.error('Failed to parse table visualization:', e);
        }
    }

    return {
        hasVisualization: false
    };
}

// Create chart from AI-generated data
function createChartFromAI(data) {
    const container = document.createElement('div');
    container.className = 'chart-container';

    if (data.title) {
        const titleRow = document.createElement('div');
        titleRow.style.display = 'flex';
        titleRow.style.justifyContent = 'space-between';
        titleRow.style.alignItems = 'center';
        titleRow.style.marginBottom = '16px';

        const title = document.createElement('h3');
        title.textContent = data.title;
        title.style.fontSize = '16px';
        title.style.fontWeight = '600';
        title.style.margin = '0';
        titleRow.appendChild(title);

        // Add action buttons
        const actionsDiv = document.createElement('div');
        actionsDiv.style.display = 'flex';
        actionsDiv.style.gap = '8px';

        // Download button
        const downloadBtn = document.createElement('button');
        downloadBtn.textContent = '💾 Uložiť';
        downloadBtn.className = 'chart-action-btn';
        downloadBtn.onclick = () => downloadChart(chartId, data.title);
        actionsDiv.appendChild(downloadBtn);

        // Share button
        const shareBtn = document.createElement('button');
        shareBtn.textContent = '🔗 Zdieľať';
        shareBtn.className = 'chart-action-btn';
        shareBtn.onclick = () => shareChart(chartId, data.title);
        actionsDiv.appendChild(shareBtn);

        titleRow.appendChild(actionsDiv);
        container.appendChild(titleRow);
    }

    const canvas = document.createElement('canvas');
    const chartId = 'ai-chart-' + Date.now();
    canvas.id = chartId;
    canvas.className = 'chart-canvas';
    container.appendChild(canvas);

    // Render chart after DOM insertion
    setTimeout(() => {
        const ctx = document.getElementById(chartId);
        if (!ctx) return;

        const chartType = data.chartType || 'bar';
        const colors = [
            'rgba(102, 126, 234, 0.8)',
            'rgba(118, 75, 162, 0.8)',
            'rgba(237, 100, 166, 0.8)',
            'rgba(255, 154, 158, 0.8)',
            'rgba(250, 208, 196, 0.8)'
        ];

        new Chart(ctx, {
            type: chartType,
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: data.datasetLabel || 'Hodnoty',
                    data: data.values || [],
                    backgroundColor: colors,
                    borderColor: colors.map(c => c.replace('0.8', '1')),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: chartType === 'doughnut'
                    }
                },
                scales: chartType === 'bar' ? {
                    y: {
                        beginAtZero: true
                    }
                } : {}
            }
        });
    }, 100);

    return container;
}

// Create table from AI-generated data
function createTableFromAI(data) {
    const container = document.createElement('div');

    if (data.title) {
        const title = document.createElement('h3');
        title.textContent = data.title;
        title.style.marginBottom = '12px';
        title.style.fontSize = '16px';
        title.style.fontWeight = '600';
        container.appendChild(title);
    }

    const tableDiv = document.createElement('div');
    tableDiv.className = 'result-table';

    const table = document.createElement('table');

    // Create header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    (data.columns || []).forEach(col => {
        const th = document.createElement('th');
        th.textContent = col;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create body with lazy loading
    const tbody = document.createElement('tbody');
    table.appendChild(tbody);
    tableDiv.appendChild(table);
    container.appendChild(tableDiv);

    // Lazy loading implementation
    const rows = data.rows || [];
    let currentIndex = 0;
    const batchSize = 20;

    function loadMoreRows() {
        const endIndex = Math.min(currentIndex + batchSize, rows.length);
        const fragment = document.createDocumentFragment();

        for (let i = currentIndex; i < endIndex; i++) {
            const tr = document.createElement('tr');
            rows[i].forEach(cell => {
                const td = document.createElement('td');
                td.textContent = cell;
                tr.appendChild(td);
            });
            fragment.appendChild(tr);
        }

        tbody.appendChild(fragment);
        currentIndex = endIndex;

        // Show loading indicator if more rows available
        if (currentIndex < rows.length) {
            const loadingRow = document.createElement('tr');
            loadingRow.className = 'loading-row';
            const td = document.createElement('td');
            td.colSpan = data.columns.length;
            td.style.textAlign = 'center';
            td.style.padding = '12px';
            td.style.color = '#667eea';
            td.textContent = `Načítaných ${currentIndex} z ${rows.length} riadkov...`;
            loadingRow.appendChild(td);
            tbody.appendChild(loadingRow);
        }
    }

    // Initial load
    loadMoreRows();

    // Scroll listener for lazy loading
    if (rows.length > batchSize) {
        tableDiv.addEventListener('scroll', () => {
            if (currentIndex >= rows.length) return;

            const scrollTop = tableDiv.scrollTop;
            const scrollHeight = tableDiv.scrollHeight;
            const clientHeight = tableDiv.clientHeight;

            // Load more when scrolled to 80% of content
            if (scrollTop + clientHeight >= scrollHeight * 0.8) {
                const loadingRow = tbody.querySelector('.loading-row');
                if (loadingRow) loadingRow.remove();
                loadMoreRows();
            }
        });
    }

    return container;
}

// Download chart as PNG
function downloadChart(chartId, title) {
    const canvas = document.getElementById(chartId);
    if (!canvas) return;

    // Convert canvas to blob
    canvas.toBlob((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${title || 'chart'}.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });
}

// Share chart (copy image to clipboard)
async function shareChart(chartId, title) {
    const canvas = document.getElementById(chartId);
    if (!canvas) return;

    try {
        // Convert canvas to blob
        canvas.toBlob(async (blob) => {
            try {
                // Copy to clipboard
                await navigator.clipboard.write([
                    new ClipboardItem({
                        'image/png': blob
                    })
                ]);

                // Show success message
                alert('Graf bol skopírovaný do schránky! Môžeš ho vložiť do emailu, Slacku, atď.');
            } catch (err) {
                console.error('Failed to copy to clipboard:', err);

                // Fallback: download instead
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${title || 'chart'}.png`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);

                alert('Graf bol stiahnutý (clipboard nepodporovaný v tomto prehliadači)');
            }
        });
    } catch (err) {
        console.error('Failed to share chart:', err);
        alert('Nepodarilo sa zdieľať graf');
    }
}

// Visualization middleware - decides which visualization to use
function formatToolResult(functionName, result) {
    const container = document.createElement('div');

    // Determine visualization type based on function name and data
    const vizType = determineVisualizationType(functionName, result);

    switch (vizType) {
        case 'chart':
            return createChartVisualization(functionName, result);
        case 'table':
            return createTableVisualization(functionName, result);
        case 'cards':
            return createCardsVisualization(functionName, result);
        default:
            return createDefaultVisualization(functionName, result);
    }
}

// Determine which visualization type to use
function determineVisualizationType(functionName, result) {
    // Project metrics → Chart (bar/line chart)
    if (functionName === 'sql_get_project_metrics') {
        return 'chart';
    }

    // Stuck issues → Table
    if (functionName === 'sql_get_stuck_issues' && result.issues && result.issues.length > 0) {
        return 'table';
    }

    // Search results → Table
    if ((functionName === 'search_issues' || functionName === 'sql_search_issues_by_text') && result.issues && result.issues.length > 0) {
        return 'table';
    }

    // User workload → Chart + Table
    if (functionName === 'sql_get_user_workload') {
        return 'chart';
    }

    // Issue history → Table
    if (functionName === 'sql_get_issue_history' && result.history && result.history.length > 0) {
        return 'table';
    }

    // Comments → Cards
    if (functionName === 'get_comments' && result.comments) {
        return 'cards';
    }

    // Default → Cards
    return 'cards';
}

// Create chart visualization
function createChartVisualization(functionName, result) {
    const container = document.createElement('div');

    // Project metrics
    if (functionName === 'sql_get_project_metrics') {
        const title = document.createElement('div');
        title.className = 'result-title';
        title.textContent = `📊 Metriky projektu ${result.project_key || result.project_keys?.join(', ')}`;
        container.appendChild(title);

        // Create chart container
        const chartContainer = document.createElement('div');
        chartContainer.className = 'chart-container';

        const canvas = document.createElement('canvas');
        canvas.className = 'chart-canvas';
        const chartId = 'chart-' + Date.now();
        canvas.id = chartId;
        chartContainer.appendChild(canvas);
        container.appendChild(chartContainer);

        // Render chart after DOM insertion
        setTimeout(() => {
            const ctx = document.getElementById(chartId);
            if (ctx) {
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: ['Vytvorených', 'Uzavretých', 'Priemerný WIP', 'Lead time (dni)', 'Throughput/deň'],
                        datasets: [{
                            label: 'Metriky',
                            data: [
                                result.total_created,
                                result.total_closed,
                                result.avg_wip,
                                result.avg_lead_time_days,
                                result.throughput_per_day || 0
                            ],
                            backgroundColor: [
                                'rgba(102, 126, 234, 0.8)',
                                'rgba(118, 75, 162, 0.8)',
                                'rgba(255, 159, 64, 0.8)',
                                'rgba(75, 192, 192, 0.8)',
                                'rgba(153, 102, 255, 0.8)'
                            ],
                            borderColor: [
                                'rgba(102, 126, 234, 1)',
                                'rgba(118, 75, 162, 1)',
                                'rgba(255, 159, 64, 1)',
                                'rgba(75, 192, 192, 1)',
                                'rgba(153, 102, 255, 1)'
                            ],
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: {
                                display: false
                            },
                            title: {
                                display: true,
                                text: `Posledných ${result.days} dní`,
                                font: {
                                    size: 14
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            }
        }, 100);
    }

    // User workload
    else if (functionName === 'sql_get_user_workload') {
        const title = document.createElement('div');
        title.className = 'result-title';
        title.textContent = `👤 Workload: ${result.assignee}`;
        container.appendChild(title);

        const totalDiv = document.createElement('div');
        totalDiv.className = 'result-summary';
        totalDiv.textContent = `Celkom open issues: ${result.total_open}`;
        container.appendChild(totalDiv);

        if (result.by_status && Object.keys(result.by_status).length > 0) {
            // Create chart container
            const chartContainer = document.createElement('div');
            chartContainer.className = 'chart-container';

            const canvas = document.createElement('canvas');
            canvas.className = 'chart-canvas';
            const chartId = 'chart-' + Date.now();
            canvas.id = chartId;
            chartContainer.appendChild(canvas);
            container.appendChild(chartContainer);

            // Render pie chart
            setTimeout(() => {
                const ctx = document.getElementById(chartId);
                if (ctx) {
                    const statuses = Object.keys(result.by_status);
                    const counts = statuses.map(s => result.by_status[s].length);

                    new Chart(ctx, {
                        type: 'doughnut',
                        data: {
                            labels: statuses,
                            datasets: [{
                                data: counts,
                                backgroundColor: [
                                    'rgba(102, 126, 234, 0.8)',
                                    'rgba(118, 75, 162, 0.8)',
                                    'rgba(255, 159, 64, 0.8)',
                                    'rgba(75, 192, 192, 0.8)',
                                    'rgba(153, 102, 255, 0.8)',
                                    'rgba(255, 99, 132, 0.8)'
                                ],
                                borderWidth: 2
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: true,
                            plugins: {
                                legend: {
                                    position: 'bottom'
                                },
                                title: {
                                    display: true,
                                    text: 'Issues podľa statusu',
                                    font: {
                                        size: 14
                                    }
                                }
                            }
                        }
                    });
                }
            }, 100);
        }
    }

    return container;
}

// Create table visualization with lazy loading
function createTableVisualization(functionName, result) {
    const container = document.createElement('div');

    // Stuck issues
    if (functionName === 'sql_get_stuck_issues' && result.issues) {
        const title = document.createElement('div');
        title.className = 'result-title';
        title.textContent = `⚠️ Stuck issues (${result.total})`;
        container.appendChild(title);

        const tableDiv = document.createElement('div');
        tableDiv.className = 'result-table';

        // Create table with lazy loading
        const table = document.createElement('table');
        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th>Issue Key</th>
                <th>Summary</th>
                <th>Status</th>
                <th>Assignee</th>
                <th>Days Stuck</th>
            </tr>
        `;
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        table.appendChild(tbody);
        tableDiv.appendChild(table);
        container.appendChild(tableDiv);

        // Lazy loading implementation
        let currentIndex = 0;
        const batchSize = 20;
        const issues = result.issues;

        function loadMoreRows() {
            const endIndex = Math.min(currentIndex + batchSize, issues.length);
            const fragment = document.createDocumentFragment();

            for (let i = currentIndex; i < endIndex; i++) {
                const issue = issues[i];
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${issue.key}</strong></td>
                    <td>${issue.summary}</td>
                    <td><span class="table-badge status-progress">${issue.status}</span></td>
                    <td>${issue.assignee || 'Unassigned'}</td>
                    <td><span class="table-badge priority-high">${issue.days_stuck} dní</span></td>
                `;
                fragment.appendChild(tr);
            }

            tbody.appendChild(fragment);
            currentIndex = endIndex;

            // Show loading indicator if more rows available
            if (currentIndex < issues.length) {
                const loadingRow = document.createElement('tr');
                loadingRow.className = 'loading-row';
                loadingRow.innerHTML = `
                    <td colspan="5" style="text-align: center; padding: 12px; color: #667eea;">
                        Načítaných ${currentIndex} z ${issues.length} issues...
                    </td>
                `;
                tbody.appendChild(loadingRow);
            }
        }

        // Initial load
        loadMoreRows();

        // Scroll listener for lazy loading
        tableDiv.addEventListener('scroll', () => {
            if (currentIndex >= issues.length) return;

            const scrollTop = tableDiv.scrollTop;
            const scrollHeight = tableDiv.scrollHeight;
            const clientHeight = tableDiv.clientHeight;

            // Load more when scrolled to 80% of content
            if (scrollTop + clientHeight >= scrollHeight * 0.8) {
                // Remove loading row
                const loadingRow = tbody.querySelector('.loading-row');
                if (loadingRow) loadingRow.remove();

                loadMoreRows();
            }
        });
    }

    // Search results with lazy loading
    else if ((functionName === 'search_issues' || functionName === 'sql_search_issues_by_text') && result.issues) {
        const title = document.createElement('div');
        title.className = 'result-title';
        title.textContent = `🔍 Nájdené issues (${result.total})`;
        container.appendChild(title);

        const tableDiv = document.createElement('div');
        tableDiv.className = 'result-table';

        // Create table with lazy loading
        const table = document.createElement('table');
        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th>Issue Key</th>
                <th>Summary</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Assignee</th>
            </tr>
        `;
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        table.appendChild(tbody);
        tableDiv.appendChild(table);
        container.appendChild(tableDiv);

        // Lazy loading implementation
        let currentIndex = 0;
        const batchSize = 20;
        const issues = result.issues;

        function loadMoreRows() {
            const endIndex = Math.min(currentIndex + batchSize, issues.length);
            const fragment = document.createDocumentFragment();

            for (let i = currentIndex; i < endIndex; i++) {
                const issue = issues[i];
                const status = issue.status || '';
                const priority = issue.priority || '';
                const statusClass = status === 'Done' ? 'status-done' :
                                   status.includes('Progress') ? 'status-progress' : 'status-todo';
                const priorityClass = priority === 'High' ? 'priority-high' :
                                     priority === 'Medium' ? 'priority-medium' : 'priority-low';

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${issue.key}</strong></td>
                    <td>${issue.summary}</td>
                    <td><span class="table-badge ${statusClass}">${issue.status}</span></td>
                    <td><span class="table-badge ${priorityClass}">${issue.priority || 'None'}</span></td>
                    <td>${issue.assignee || 'Unassigned'}</td>
                `;
                fragment.appendChild(tr);
            }

            tbody.appendChild(fragment);
            currentIndex = endIndex;

            // Show loading indicator if more rows available
            if (currentIndex < issues.length) {
                const loadingRow = document.createElement('tr');
                loadingRow.className = 'loading-row';
                loadingRow.innerHTML = `
                    <td colspan="5" style="text-align: center; padding: 12px; color: #667eea;">
                        Načítaných ${currentIndex} z ${issues.length} issues...
                    </td>
                `;
                tbody.appendChild(loadingRow);
            }
        }

        // Initial load
        loadMoreRows();

        // Scroll listener for lazy loading
        tableDiv.addEventListener('scroll', () => {
            if (currentIndex >= issues.length) return;

            const scrollTop = tableDiv.scrollTop;
            const scrollHeight = tableDiv.scrollHeight;
            const clientHeight = tableDiv.clientHeight;

            // Load more when scrolled to 80% of content
            if (scrollTop + clientHeight >= scrollHeight * 0.8) {
                // Remove loading row
                const loadingRow = tbody.querySelector('.loading-row');
                if (loadingRow) loadingRow.remove();

                loadMoreRows();
            }
        });
    }

    // Issue history
    else if (functionName === 'sql_get_issue_history' && result.history) {
        const title = document.createElement('div');
        title.className = 'result-title';
        title.textContent = `📜 História (${result.total})`;
        container.appendChild(title);

        const tableDiv = document.createElement('div');
        tableDiv.className = 'result-table';

        const table = document.createElement('table');
        table.innerHTML = `
            <thead>
                <tr>
                    <th>From Status</th>
                    <th>To Status</th>
                    <th>Transitioned By</th>
                    <th>Date</th>
                </tr>
            </thead>
            <tbody>
                ${result.history.map(h => `
                    <tr>
                        <td><span class="table-badge status-todo">${h.from_status}</span></td>
                        <td><span class="table-badge status-progress">${h.to_status}</span></td>
                        <td>${h.transitioned_by}</td>
                        <td>${new Date(h.transitioned_at).toLocaleString('sk-SK')}</td>
                    </tr>
                `).join('')}
            </tbody>
        `;

        tableDiv.appendChild(table);
        container.appendChild(tableDiv);
    }

    return container;
}

// Create cards visualization (for comments, etc.)
function createCardsVisualization(functionName, result) {
    const container = document.createElement('div');

    // Comments
    if (functionName === 'get_comments' && result.comments) {
        const title = document.createElement('div');
        title.className = 'result-title';
        title.textContent = `💬 Komentáre (${result.total})`;
        container.appendChild(title);

        result.comments.forEach(comment => {
            const commentDiv = document.createElement('div');
            commentDiv.className = 'result-item';
            commentDiv.innerHTML = `
                <div class="result-item-header">
                    <strong>${comment.author}</strong>
                    <span class="result-item-date">${new Date(comment.created).toLocaleString('sk-SK')}</span>
                </div>
                <div class="result-item-body">${comment.body}</div>
            `;
            container.appendChild(commentDiv);
        });
    }

    return container;
}

// Create default visualization (fallback)
function createDefaultVisualization(functionName, result) {
    const container = document.createElement('div');

    const pre = document.createElement('pre');
    pre.className = 'result-json';
    pre.textContent = JSON.stringify(result, null, 2);
    container.appendChild(pre);

    return container;
}

// Rollback checkpoint
async function rollbackCheckpoint(checkpointId, toolDiv) {
    if (!confirm('Naozaj chceš vrátiť túto operáciu späť?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/v1/ai-assistant/rollback/${checkpointId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Tenant-Id': TENANT_ID
            }
        });

        const data = await response.json();

        if (data.success) {
            // Update UI to show rollback success
            const undoButton = toolDiv.querySelector('.undo-button');
            if (undoButton) {
                undoButton.textContent = '✅ Vrátené späť';
                undoButton.disabled = true;
                undoButton.style.opacity = '0.5';
            }

            // Add success message
            addMessage('assistant', `✅ ${data.message}`);
        } else {
            addMessage('assistant', `❌ Rollback zlyhal: ${data.error || 'Neznáma chyba'}`);
        }
    } catch (error) {
        console.error('Rollback failed:', error);
        addMessage('assistant', `❌ Rollback zlyhal: ${error.message}`);
    }
}

