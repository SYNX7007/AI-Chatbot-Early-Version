class AppState {
  constructor() {
    this.currentUser = null;
    this.currentConversation = null;
    this.currentSection = 'chat';
    this.conversations = [];
    this.users = [];
    this.departments = [];
    this.systemSettings = {
      companyName: "Ankit Solutions",
      blockedKeywords: [
        "personal", "entertainment", "games", "external_news",
        "game of the year", "sports", "movies"
      ],
      maxConversationLength: 100,
      sessionTimeout: 3600000
    };
    this.activityLog = [];

    this.init();
  }

  init() {
    // Try to load from localStorage
    const savedState = localStorage.getItem('Ankit_ai_state');
    if (savedState) {
      try {
        const parsed = JSON.parse(savedState);
        if (parsed.conversations) this.conversations = parsed.conversations;
        if (parsed.users) this.users = parsed.users;
        if (parsed.departments) this.departments = parsed.departments;
        if (parsed.systemSettings) this.systemSettings = parsed.systemSettings;
        if (parsed.activityLog) this.activityLog = parsed.activityLog;
      } catch (e) {
        console.error('Error loading saved state:', e);
      }
    }

    // Load current user and token if available
    const user = localStorage.getItem('currentUser');
    if (user) this.currentUser = JSON.parse(user);
  }

  save() {
    try {
      localStorage.setItem('Ankit_ai_state', JSON.stringify({
        conversations: this.conversations,
        users: this.users,
        departments: this.departments,
        systemSettings: this.systemSettings,
        activityLog: this.activityLog
      }));
      if (this.currentUser) {
        localStorage.setItem('currentUser', JSON.stringify(this.currentUser));
      } else {
        localStorage.removeItem('currentUser');
      }
    } catch (e) {
      console.error('Error saving state:', e);
    }
  }

  async login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    try {
      const response = await fetch('http://localhost:8000/token', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: formData.toString()
      });

      if (!response.ok) throw new Error('Login failed');

      const data = await response.json();
      localStorage.setItem('access_token', data.access_token);
      this.currentUser = data.user;
      this.addActivity(`User ${this.currentUser.name} logged in`);
      this.save();
      return true;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  }

  logout() {
    localStorage.removeItem('access_token');
    this.addActivity(`User ${this.currentUser?.name} logged out`);
    this.currentUser = null;
    this.currentConversation = null;
    this.save();
  }

  addActivity(description) {
    this.activityLog.unshift({
      id: Date.now(),
      description,
      timestamp: new Date().toISOString(),
      userId: this.currentUser?.id
    });
    this.save();
  }

  getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  }

  async fetchDepartments() {
    try {
      const res = await fetch('http://localhost:8000/departments', {
        headers: this.getAuthHeaders()
      });
      if (!res.ok) throw new Error('Failed to load departments');
      this.departments = await res.json();
      return this.departments;
    } catch (e) {
      console.error('Error loading departments:', e);
      return [];
    }
  }

  async fetchConversations() {
    try {
      const res = await fetch('http://localhost:8000/conversations', {
        headers: this.getAuthHeaders()
      });
      if (!res.ok) throw new Error('Failed to load conversations');
      this.conversations = await res.json();
      return this.conversations;
    } catch (e) {
      console.error('Error loading conversations:', e);
      return [];
    }
  }

  async sendMessage(message, department) {
    if (this.isPromptBlocked(message)) {
      throw new Error("I can only answer questions related to company data and procedures. Please ask about topics relevant to your department.");
    }
    const body = {content: message, department};
    const res = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(body)
    });
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || 'Chat failed');
    }
    const data = await res.json();
    return data.response;
  }

  isPromptBlocked(message) {
    const lower = message.toLowerCase();
    const blocked = this.systemSettings.blockedKeywords || [];
    return blocked.some(bk => lower.includes(bk.toLowerCase()));
  }
}

// UI Controller class to manage DOM and events
class UIController {
  constructor(appState) {
    this.appState = appState;
    this.init();
  }

  init() {
    this.bindEvents();
    if (this.appState.currentUser) {
      this.showDashboard();
    } else {
      this.showLoginPage();
    }
  }

  bindEvents() {
    document.getElementById('login-form').addEventListener('submit', e => {
      e.preventDefault();
      this.handleLogin();
    });

    document.getElementById('logout-btn').addEventListener('click', () => {
      this.handleLogout();
    });

    document.getElementById('send-btn').addEventListener('click', () => {
      this.handleSendMessage();
    });

    document.getElementById('message-input').addEventListener('keypress', e => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.handleSendMessage();
      }
    });

    document.getElementById('department-select').addEventListener('change', () => {
      this.toggleSendButton();
    });
  }

  async handleLogin() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const errorEl = document.getElementById('login-error');

    if (!username || !password) {
      errorEl.textContent = 'Please enter both username and password';
      errorEl.classList.remove('hidden');
      return;
    }

    const success = await this.appState.login(username, password);
    if (success) {
      errorEl.classList.add('hidden');
      await this.showDashboard();
    } else {
      errorEl.textContent = 'Invalid username or password';
      errorEl.classList.remove('hidden');
    }
  }

  handleLogout() {
    this.appState.logout();
    this.showLoginPage();
  }

  showLoginPage() {
    document.getElementById('login-page').classList.add('active');
    document.getElementById('login-page').classList.remove('hidden');
    document.getElementById('dashboard-page').classList.remove('active');
    document.getElementById('dashboard-page').classList.add('hidden');
  }

  async showDashboard() {
    document.getElementById('login-page').classList.remove('active');
    document.getElementById('login-page').classList.add('hidden');
    document.getElementById('dashboard-page').classList.add('active');
    document.getElementById('dashboard-page').classList.remove('hidden');

    document.getElementById('user-name').textContent = this.appState.currentUser.name;
    document.getElementById('user-role').textContent = this.appState.currentUser.role.toUpperCase();

    await this.loadDepartments();
    await this.loadConversations();

    this.showSection('chat');
  }

  async loadDepartments() {
    const select = document.getElementById('department-select');
    select.innerHTML = '';
    try {
      const departments = await this.appState.fetchDepartments();
      departments.forEach(dept => {
        const option = document.createElement('option');
        option.value = dept.key;
        option.textContent = dept.name;
        select.appendChild(option);
      });
    } catch (e) {
      console.error(e);
    }
  }

  async loadConversations() {
    const container = document.getElementById('conversations-list');
    container.innerHTML = '';
    try {
      const convos = await this.appState.fetchConversations();
      this.appState.conversations = convos;
      convos.forEach(conv => {
        const div = document.createElement('div');
        div.className = 'conversation-item';
        div.textContent = `${conv.department} - ${conv.user_message.substring(0, 30)}...`;
        div.addEventListener('click', () => {
          this.showConversation(conv);
        });
        container.appendChild(div);
      });
    } catch (e) {
      console.error(e);
    }
  }

  async handleSendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    if (!message) return;

    const deptSelect = document.getElementById('department-select');
    const department = deptSelect.value;
    if (!department) return alert('Please select a department');

    this.toggleSendButton(false);

    try {
      const aiResponse = await this.appState.sendMessage(message, department);
      this.appendMessage('user', message);
      this.appendMessage('assistant', aiResponse);
      input.value = '';
      input.focus();
    } catch (error) {
      alert(error.message);
    }

    this.toggleSendButton(true);
  }

  appendMessage(role, text) {
    const chatContainer = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;
    msgDiv.appendChild(contentDiv);
    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  showConversation(conversation) {
    this.appState.currentConversation = conversation;
    const chatContainer = document.getElementById('chat-messages');
    chatContainer.innerHTML = '';
    this.appendMessage('user', conversation.user_message);
    this.appendMessage('assistant', conversation.ai_response);
  }

  toggleSendButton(enable = true) {
    const sendBtn = document.getElementById('send-btn');
    sendBtn.disabled = !enable;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const appState = new AppState();
  const uiCtrl = new UIController(appState);
});
