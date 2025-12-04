const CONSOLE_HISTORY_KEY = 'vantage_console_history';
const MAX_HISTORY_ENTRIES = 100;

class ConsoleBuffer {
  constructor() {
    this.history = this._load();
    this.container = this._renderContainer();
    this._patchConsole();
  }

  _load() {
    try {
      const data = localStorage.getItem(CONSOLE_HISTORY_KEY);
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  }

  _save() {
    try {
      localStorage.setItem(CONSOLE_HISTORY_KEY, JSON.stringify(this.history));
    } catch (error) {
      // ignore storage failures
    }
  }

  _push(entry) {
    this.history.push(entry);
    if (this.history.length > MAX_HISTORY_ENTRIES) {
      this.history.shift();
    }
    this._save();
    this._renderList();
  }

  _renderContainer() {
    const container = document.createElement('details');
    container.style.position = 'fixed';
    container.style.bottom = '12px';
    container.style.right = '12px';
    container.style.zIndex = 9999;
    container.style.maxWidth = '320px';
    container.style.fontSize = '0.75rem';
    container.style.color = '#e0e0e0';
    container.style.background = 'rgba(0,0,0,0.65)';
    container.style.border = '1px solid rgba(255,255,255,0.2)';
    container.style.borderRadius = '4px';
    container.style.padding = '0';
    container.innerHTML = `
      <summary style="margin:0;padding:8px;cursor:pointer;">Console history (${this.history.length})</summary>
      <div class="history-list" style="max-height:220px;overflow:auto;padding:8px;"></div>
    `;
    document.body.appendChild(container);
    this._renderList(container);
    return container;
  }

  _renderList(container = this.container) {
    if (!container) return;
    const list = container.querySelector('.history-list');
    if (!list) return;
    list.innerHTML = this.history
      .slice()
      .reverse()
      .map(
        (entry) =>
          `<div style="margin-bottom:6px;"><strong style="color:${entry.typeColor};">${entry.type}</strong> ${entry.text}</div>`
      )
      .join('');
    const summary = (container || this.container)?.querySelector('summary');
    if (summary) summary.textContent = `Console history (${this.history.length})`;
  }

  _patchConsole() {
    ['log', 'info', 'warn', 'error'].forEach((type) => {
      const original = console[type].bind(console);
      console[type] = (...args) => {
        try {
          const text = args.map((arg) => (typeof arg === 'object' ? JSON.stringify(arg) : String(arg))).join(' ');
          this._push({
            type: type.toUpperCase(),
            text,
            timestamp: Date.now(),
            typeColor: type === 'error' ? '#ff6b6b' : type === 'warn' ? '#f1c40f' : '#8ce5ff',
          });
        } catch {
          // ignore
        }
        return original(...args);
      };
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.__CONSOLE_BUFFER = new ConsoleBuffer();
});
