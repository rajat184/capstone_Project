document.addEventListener('DOMContentLoaded', () => {
  const sendBtn = document.getElementById('send')
  const cancelBtn = document.getElementById('cancel')
  const resetBtn = document.getElementById('reset')
  const instructionsEl = document.getElementById('instructions')
  const promptEl = document.getElementById('prompt')
  const insightsEl = document.getElementById('insights')
  const previewEl = document.getElementById('preview')
  
  let activeTaskId = null
  let statusCheckInterval = null
  let isWaitingForInput = false  // Track if we're waiting for user input
  let isUserTyping = false      // Track if user is actively typing
  let lastPrompt = ''           // Store last prompt to prevent duplicates

  const updateTaskStatus = async (taskId) => {
    try {
      const resp = await fetch(`/api/task-status/${taskId}`)
      const data = await resp.json()

      console.log('Task status data:', data)
      console.log('Has screenshot:', !!data.screenshot)

      if (data.status === 'error') {
        insightsEl.textContent = data.message
        clearInterval(statusCheckInterval)
        activeTaskId = null
        return
      }

      // Update screenshot if available
      if (data.screenshot) {
        console.log('Screenshot length:', data.screenshot.length)
        // Clear any existing content
        previewEl.innerHTML = '';
        // Create and add the new image
        const img = document.createElement('img');
        img.src = `data:image/png;base64,${data.screenshot}`;
        img.alt = 'Latest screenshot';
        img.style.display = 'block'; // Ensure image is displayed as block
        img.onload = () => console.log('Screenshot loaded successfully');
        img.onerror = () => console.error('Screenshot failed to load');
        previewEl.appendChild(img);
      } else if (!previewEl.querySelector('img')) {
        // Show placeholder if no image
        previewEl.innerHTML = '<div class="screenshot-placeholder">Screenshot preview will appear here</div>';
      }

      // Update terminal output if available (always safe)
      if (data.terminal_output) {
        document.getElementById('terminal').textContent = data.terminal_output
      }

      // If agent requests input, show prompt but do NOT overwrite user's typing
      if (data.needs_input && data.prompt) {
        // Only process new prompts
        if (!isWaitingForInput || lastPrompt !== data.prompt) {
          lastPrompt = data.prompt
          
          // Only update UI if user isn't actively typing
          if (!isUserTyping) {
            promptEl.placeholder = data.prompt
            insightsEl.textContent = data.prompt
          }
          
          isWaitingForInput = true
          promptEl.disabled = false
        }
        return
      }

      // If we are no longer waiting for input, allow insights to update
      if (!isWaitingForInput) {
        insightsEl.textContent = data.message || `Status: ${data.status}`
      }

      if (data.status === 'completed') {
        clearInterval(statusCheckInterval)
        activeTaskId = null
      }
    } catch (e) {
      console.error('Error checking task status:', e)
      // Only clear interval on serious error, keep activeTaskId so user can respond
      insightsEl.textContent = 'Error checking task status: ' + (e.message || e)
      clearInterval(statusCheckInterval)
      activeTaskId = null
    }
  }

  sendBtn.addEventListener('click', async () => {
    const instructions = instructionsEl.value.trim()
    if (!instructions) {
      insightsEl.textContent = 'Please enter instructions.'
      return
    }
    
    if (activeTaskId) {
      insightsEl.textContent = 'A task is already running. Please wait or reset.'
      return
    }
    
    insightsEl.textContent = 'Starting task...'
    sendBtn.disabled = true

    try {
      const resp = await fetch('/api/send-task', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({instructions})
      })
      const data = await resp.json()
      
      if (data.status === 'ok') {
        activeTaskId = data.task_id
        insightsEl.textContent = 'Task started. Waiting for updates...'
        
        // Start checking status
        statusCheckInterval = setInterval(
          () => updateTaskStatus(activeTaskId), 
          1000
        )
      } else {
        insightsEl.textContent = data.message || 'Error starting task'
      }
    } catch (e) {
      insightsEl.textContent = 'Error: ' + e.message
    } finally {
      sendBtn.disabled = false
    }
  })

  cancelBtn.addEventListener('click', () => {
    if (statusCheckInterval) {
      clearInterval(statusCheckInterval)
    }
    activeTaskId = null
    instructionsEl.value = ''
    promptEl.value = ''
    promptEl.disabled = true
    promptEl.placeholder = 'Type your response here and click Send...'
    isWaitingForInput = false
    insightsEl.textContent = 'Cancelled.'
    sendBtn.disabled = false
  })

  promptEl.addEventListener('keypress', async (e) => {
    if (e.key === 'Enter' && !e.shiftKey && activeTaskId) {
      const response = promptEl.value.trim()
      if (!response) return
      
      promptEl.disabled = true
      try {
        const resp = await fetch(`/api/respond-to-prompt/${activeTaskId}`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({response})
        })
        const data = await resp.json()
        
        if (data.status === 'ok') {
          isWaitingForInput = false  // Reset waiting state
          promptEl.value = ''
          promptEl.placeholder = 'Waiting for next prompt...'
          insightsEl.textContent = 'Response sent. Waiting for updates...'
        } else {
          promptEl.disabled = false
          insightsEl.textContent = data.message || 'Error sending response'
        }
      } catch (e) {
        promptEl.disabled = false
        insightsEl.textContent = 'Error: ' + e.message
      }
    }
  })

  resetBtn.addEventListener('click', () => {
    if (statusCheckInterval) {
      clearInterval(statusCheckInterval)
    }
    activeTaskId = null
    instructionsEl.value = ''
    promptEl.value = ''
    promptEl.disabled = true
    promptEl.placeholder = 'Type your response here and click Send...'
    isWaitingForInput = false
    isUserTyping = false
    lastPrompt = ''
    insightsEl.textContent = ''
    sendBtn.disabled = false
  })

  // Track when user starts/stops typing
  promptEl.addEventListener('focus', () => {
    isUserTyping = true
  })

  promptEl.addEventListener('blur', () => {
    isUserTyping = false
    // Restore prompt in placeholder if there's no user input
    if (lastPrompt && !promptEl.value) {
      promptEl.placeholder = lastPrompt
    }
  })

  // Additional safeguard for input handling
  promptEl.addEventListener('input', () => {
    if (!isUserTyping) {
      isUserTyping = true
    }
  })
})