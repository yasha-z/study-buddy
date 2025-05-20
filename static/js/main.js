document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const videoFeed = document.getElementById('video-feed');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const taskInput = document.getElementById('taskInput');
    const addTaskBtn = document.getElementById('addTaskBtn');
    const taskList = document.getElementById('taskList');
    const minutesDisplay = document.getElementById('minutes');
    const secondsDisplay = document.getElementById('seconds');
    const sessionCountDisplay = document.getElementById('sessionCount');
    const statusDisplay = document.getElementById('status');
    const taskTypeSelect = document.createElement('select');
    
    // Add task type selector
    taskTypeSelect.id = 'taskTypeSelect';
    taskTypeSelect.innerHTML = `
        <option value="reading">Reading</option>
        <option value="writing">Writing</option>
        <option value="problem_solving">Problem Solving</option>
        <option value="memorization">Memorization</option>
        <option value="research">Research</option>
    `;
    taskInput.parentNode.insertBefore(taskTypeSelect, addTaskBtn);

    // Add break suggestion element
    const breakSuggestionElement = document.createElement('div');
    breakSuggestionElement.id = 'breakSuggestion';
    breakSuggestionElement.className = 'break-suggestion';
    document.querySelector('.status-section').appendChild(breakSuggestionElement);

    // Constants
    const WORK_DURATION = 25 * 60; // 25 minutes in seconds
    const BREAK_DURATION = 5 * 60; // 5 minutes in seconds

    // Variables
    let isStudying = false;
    let currentSession = 1;
    let timer = null;
    let timeLeft = WORK_DURATION;
    let isBreak = false;
    let breakSuggestionInterval = null;

    // Add quote elements
    const quoteElement = document.getElementById('motivationalQuote');
    const quoteContent = quoteElement.querySelector('.quote-content');
    let quoteInterval = null;

    // Load tasks from server
    async function loadTasks() {
        const response = await fetch('/tasks');
        const tasks = await response.json();
        updateTaskList(tasks);
    }

    // Update task list display
    function updateTaskList(tasks) {
        taskList.innerHTML = '';
        Object.entries(tasks).forEach(([task, taskData]) => {
            const li = document.createElement('li');
            
            // Create checkbox
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.checked = taskData.completed;
            checkbox.addEventListener('change', () => updateTaskStatus(task, checkbox.checked));
            
            // Create task text container
            const taskContainer = document.createElement('div');
            taskContainer.className = 'task-container';
            
            // Create task text
            const taskText = document.createElement('span');
            taskText.className = 'task-text';
            taskText.textContent = task;
            if (taskData.completed) {
                taskText.style.textDecoration = 'line-through';
            }
            
            // Create task type badge
            const taskType = document.createElement('span');
            taskType.className = 'task-type';
            taskType.textContent = taskData.type;
            
            // Create session info if completed
            if (taskData.completed && taskData.completed_in_session) {
                const sessionInfo = document.createElement('span');
                sessionInfo.className = 'session-info';
                sessionInfo.textContent = `Completed in session ${taskData.completed_in_session}`;
            }
            
            // Assemble the task item
            taskContainer.appendChild(taskText);
            taskContainer.appendChild(taskType);
            if (taskData.completed && taskData.completed_in_session) {
                const sessionInfo = document.createElement('span');
                sessionInfo.className = 'session-info';
                sessionInfo.textContent = `Completed in session ${taskData.completed_in_session}`;
                taskContainer.appendChild(sessionInfo);
            }
            
            li.appendChild(checkbox);
            li.appendChild(taskContainer);
            taskList.appendChild(li);
        });
    }

    // Check for break suggestions
    async function checkBreakSuggestion() {
        try {
            const response = await fetch('/get_break_suggestion');
            const data = await response.json();
            
            if (data.has_suggestion) {
                breakSuggestionElement.innerHTML = `<i class="fas fa-coffee"></i> ${data.suggestion}`;
                breakSuggestionElement.classList.add('show');
            } else {
                breakSuggestionElement.classList.remove('show');
            }
        } catch (error) {
            console.error('Error checking break suggestion:', error);
        }
    }

    // Add new task
    async function addTask(task) {
        const taskType = taskTypeSelect.value;
        const response = await fetch('/tasks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ task, type: taskType }),
        });
        if (response.ok) {
            loadTasks();
            taskInput.value = '';
        }
    }

    // Update task status
    async function updateTaskStatus(task, completed) {
        const response = await fetch('/update_task', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                task, 
                completed,
                session: completed ? currentSession : null 
            }),
        });
        if (response.ok) {
            const result = await response.json();
            if (result.status === 'success' && result.completed_in_session) {
                statusDisplay.textContent = `Task "${task}" completed in session ${result.completed_in_session}!`;
                setTimeout(() => {
                    if (!isBreak) {
                        statusDisplay.textContent = 'Working Session';
                    } else {
                        statusDisplay.textContent = 'Break Time!';
                    }
                }, 3000);
            }
            loadTasks();
        }
    }

    // Timer functions
    function updateTimerDisplay() {
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        minutesDisplay.textContent = minutes.toString().padStart(2, '0');
        secondsDisplay.textContent = seconds.toString().padStart(2, '0');
    }

    function startTimer() {
        timer = setInterval(() => {
            timeLeft--;
            updateTimerDisplay();

            if (timeLeft <= 0) {
                clearInterval(timer);
                if (isBreak) {
                    startWorkSession();
                } else {
                    startBreak();
                }
            }
        }, 1000);
    }

    // Function to update quote
    async function checkForQuote() {
        const response = await fetch('/get_quote');
        const data = await response.json();
        
        if (data.has_quote) {
            quoteContent.textContent = data.quote;
            quoteElement.classList.add('show');
        } else {
            quoteElement.classList.remove('show');
        }
    }

    // Update status display with icons
    function updateStatus(text, icon = 'info-circle') {
        statusDisplay.innerHTML = `<i class="fas fa-${icon}"></i> ${text}`;
    }

    function startWorkSession() {
        isBreak = false;
        timeLeft = WORK_DURATION;
        updateTimerDisplay();
        startTimer();
        updateStatus('Working Session', 'brain');
        sessionCountDisplay.innerHTML = `<i class="fas fa-sync-alt"></i> Pomodoro Round: ${currentSession}`;
    }

    function startBreak() {
        isBreak = true;
        timeLeft = BREAK_DURATION;
        updateTimerDisplay();
        startTimer();
        currentSession++;
        updateStatus('Break Time!', 'coffee');
    }

    // Event Listeners
    startBtn.addEventListener('click', async () => {
        if (!isStudying) {
            try {
                const response = await fetch('/start_monitoring', { method: 'POST' });
                const result = await response.json();
                
                if (result.status === 'success') {
                    isStudying = true;
                    startBtn.style.display = 'none';
                    stopBtn.style.display = 'block';
                    
                    // Start video feed
                    videoFeed.style.display = 'block';
                    videoFeed.src = '/video_feed?' + new Date().getTime();
                    
                    // Start intervals
                    quoteInterval = setInterval(checkForQuote, 1000);
                    breakSuggestionInterval = setInterval(checkBreakSuggestion, 5000);
                    startWorkSession();
                }
            } catch (error) {
                console.error('Error:', error);
                updateStatus('Error starting camera. Please try again.', 'exclamation-circle');
            }
        }
    });

    stopBtn.addEventListener('click', async () => {
        if (isStudying) {
            try {
                // Stop monitoring first
                await fetch('/stop_monitoring', { method: 'POST' });
                
                // Reset UI
                isStudying = false;
                startBtn.style.display = 'block';
                stopBtn.style.display = 'none';
                videoFeed.style.display = 'none';
                videoFeed.src = '';
                
                // Clear intervals
                clearInterval(timer);
                clearInterval(quoteInterval);
                clearInterval(breakSuggestionInterval);
                quoteElement.classList.remove('show');
                breakSuggestionElement.classList.remove('show');
                
                // Reset timer and status
                timeLeft = WORK_DURATION;
                updateTimerDisplay();
                currentSession = 1;
                updateStatus('Session stopped', 'stop-circle');
            } catch (error) {
                console.error('Error:', error);
                updateStatus('Error stopping session. Please refresh the page.', 'exclamation-circle');
            }
        }
    });

    addTaskBtn.addEventListener('click', () => {
        const task = taskInput.value.trim();
        if (task) {
            addTask(task);
        }
    });

    taskInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const task = taskInput.value.trim();
            if (task) {
                addTask(task);
            }
        }
    });

    // Initialize
    loadTasks();
}); 