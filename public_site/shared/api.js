/**
 * BotThongMinh — API fetch wrapper with CSRF support.
 */
const apex = {
  baseUrl: '',

  async fetch(path, options = {}) {
    const url = this.baseUrl + path;
    const defaults = {
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'same-origin',
    };
    const config = { ...defaults, ...options };
    if (options.body && typeof options.body === 'object') {
      config.body = JSON.stringify(options.body);
    }
    const response = await window.fetch(url, config);
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
  },

  get(path) {
    return this.fetch(path, { method: 'GET' });
  },

  post(path, body) {
    return this.fetch(path, { method: 'POST', body });
  },

  put(path, body) {
    return this.fetch(path, { method: 'PUT', body });
  },

  delete(path) {
    return this.fetch(path, { method: 'DELETE' });
  },
};
