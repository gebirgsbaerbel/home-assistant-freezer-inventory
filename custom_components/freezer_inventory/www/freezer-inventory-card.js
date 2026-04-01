class FreezerInventoryCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._items = [];
    this._formOpen = false;
    this._todoEntityId = null;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('entity is required (e.g. sensor.freezer_inventory)');
    }
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    const state = hass.states[this._config?.entity];
    const items = state?.attributes?.items ?? [];
    this._todoEntityId = state?.attributes?.todo_entity_id ?? this._config?.todo_entity ?? null;
    if (JSON.stringify(items) !== JSON.stringify(this._items)) {
      this._items = items;
      if (!this._formOpen) this._render();
    }
  }

  _formatDate(iso) {
    if (!iso) return '';
    try {
      const [y, m, d] = iso.split('-').map(Number);
      return new Date(y, m - 1, d).toLocaleDateString(undefined, { month: 'short', year: '2-digit' });
    } catch {
      return iso;
    }
  }

  _defaultDate() {
    const d = new Date();
    d.setMonth(d.getMonth() + 3);
    return d.toISOString().split('T')[0];
  }

  _escapeHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  _render() {
    if (!this._config) return;

    const items = this._items;
    const c = this._config;
    const cardBg      = c.card_background ?? '';
    const rowBg       = c.row_color       ?? 'var(--secondary-background-color)';
    const textColor   = c.text_color      ?? 'var(--primary-text-color)';
    const dateColor   = c.secondary_color ?? 'var(--secondary-text-color)';
    const circleColor = c.accent_color    ?? 'var(--primary-color)';

    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        ha-card { overflow: hidden; ${cardBg ? `background: ${cardBg};` : ''} }
        .header {
          display: flex;
          align-items: center;
          padding: 16px 16px 8px;
        }
        .header-title {
          flex-grow: 1;
          font-size: var(--ha-card-header-font-size, 1.1em);
          font-weight: 500;
          color: ${textColor};
        }
        .add-btn {
          background: none;
          border: none;
          cursor: pointer;
          color: ${circleColor};
          padding: 4px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background 0.15s;
          -webkit-tap-highlight-color: transparent;
        }
        .add-btn:hover { background: ${rowBg}; }
        .form-section {
          padding: 0 12px 12px;
          display: ${this._formOpen ? 'flex' : 'none'};
          flex-direction: column;
          gap: 8px;
        }
        .form-row {
          display: flex;
          gap: 8px;
        }
        .form-input {
          flex-grow: 1;
          background: ${rowBg};
          border: none;
          border-radius: 8px;
          padding: 10px 12px;
          color: ${textColor};
          font-size: 1em;
          outline: none;
          font-family: inherit;
          color-scheme: dark;
        }
        .form-input:focus { box-shadow: 0 0 0 2px ${circleColor}; }
        .form-input-small { width: 64px; flex-grow: 0; }
        .form-buttons {
          display: flex;
          gap: 8px;
          justify-content: flex-end;
        }
        .btn {
          border: none;
          border-radius: 20px;
          padding: 8px 18px;
          font-size: 0.9em;
          font-weight: 600;
          cursor: pointer;
          transition: opacity 0.15s;
          font-family: inherit;
        }
        .btn:hover { opacity: 0.8; }
        .btn-confirm { background: ${circleColor}; color: #fff; }
        .btn-cancel { background: ${rowBg}; color: ${textColor}; }
        .list {
          padding: 8px 12px 12px;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .row {
          display: flex;
          align-items: center;
          background: ${rowBg};
          border-radius: 32px;
          padding: 0px 10px;
          cursor: pointer;
          user-select: none;
          transition: opacity 0.15s, transform 0.1s;
          -webkit-tap-highlight-color: transparent;
          min-height: 58px;
        }
        .row:hover { opacity: 0.8; }
        .row:active { transform: scale(0.98); }
        .count-circle {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: ${circleColor};
          color: #ffffff;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.1em;
          font-weight: 600;
          flex-shrink: 0;
          margin-right: 14px;
        }
        .item-text {
          flex-grow: 1;
          overflow: hidden;
        }
        .item-name {
          font-size: 1em;
          font-weight: 700;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          color: ${textColor};
        }
        .item-date {
          font-size: 1em;
          color: ${dateColor};
          flex-shrink: 0;
          margin-left: 10px;
          margin-right: 10px;
        }
        .empty {
          text-align: center;
          color: ${dateColor};
          padding: 24px;
          font-size: 0.9em;
        }
      </style>
      <ha-card>
        <div class="header">
          <span class="header-title">${this._escapeHtml(c.title ?? 'Freezer')}</span>
          <button class="add-btn" id="add-btn" aria-label="Add item">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
              <path fill="currentColor" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
            </svg>
          </button>
        </div>
        <div class="form-section" id="form-section">
          <div class="form-row">
            <input class="form-input" id="f-name" type="text" placeholder="Item name" />
            <input class="form-input form-input-small" id="f-portions" type="number" min="1" value="1" />
          </div>
          <input class="form-input" id="f-date" type="date" value="${this._defaultDate()}" />
          <div class="form-buttons">
            <button class="btn btn-cancel" id="btn-cancel">Cancel</button>
            <button class="btn btn-confirm" id="btn-confirm">Add</button>
          </div>
        </div>
        ${items.length
          ? `<div class="list">${items.map((item, i) => `
              <div class="row" data-i="${i}">
                <div class="count-circle">${item.portions}</div>
                <div class="item-text">
                  <div class="item-name">${this._escapeHtml(item.description)}</div>
                </div>
                ${item.expiration ? `<div class="item-date">${this._formatDate(item.expiration)}</div>` : ''}
              </div>`).join('')}
            </div>`
          : '<div class="empty">Freezer is empty ❄️</div>'
        }
      </ha-card>`;

    this.shadowRoot.getElementById('add-btn').addEventListener('click', () => {
      this._formOpen = true;
      this._render();
      this.shadowRoot.getElementById('f-name')?.focus();
    });

    this.shadowRoot.getElementById('btn-cancel').addEventListener('click', () => {
      this._formOpen = false;
      this._render();
    });

    this.shadowRoot.getElementById('btn-confirm').addEventListener('click', () => this._submitForm());

    this.shadowRoot.getElementById('f-name')?.addEventListener('keydown', e => {
      if (e.key === 'Enter') this._submitForm();
      if (e.key === 'Escape') { this._formOpen = false; this._render(); }
    });

    this.shadowRoot.querySelectorAll('.row').forEach(el => {
      el.addEventListener('click', () => {
        const item = this._items[+el.dataset.i];
        if (item && this._hass) {
          this._hass.callService('freezer_inventory', 'freezer_minus', {
            item: item.description,
            portions: item.portions,
          });
        }
      });
    });

    window.dispatchEvent(new Event('resize'));
  }

  async _submitForm() {
    const nameEl     = this.shadowRoot.getElementById('f-name');
    const portionsEl = this.shadowRoot.getElementById('f-portions');
    const dateEl     = this.shadowRoot.getElementById('f-date');

    const name     = nameEl?.value?.trim();
    const portions = parseInt(portionsEl?.value ?? '1', 10);
    const date     = dateEl?.value;

    if (!name) { nameEl?.focus(); return; }
    if (!this._todoEntityId || !this._hass) return;

    await this._hass.callService('todo', 'add_item', {
      entity_id: this._todoEntityId,
      item: name,
      description: String(isNaN(portions) || portions < 1 ? 1 : portions),
      ...(date ? { due_date: date } : {}),
    });

    this._formOpen = false;
    this._render();
  }

  getLayoutOptions() {
    const rows = this._config?.rows ?? Math.max(2, this._items.length + 1);
    return {
      grid_rows: rows,
      grid_columns: 4,
      grid_min_rows: rows,
    };
  }

  static getStubConfig() {
    return { entity: 'sensor.freezer_inventory' };
  }
}

customElements.define('freezer-inventory-card', FreezerInventoryCard);

window.customCards ??= [];
window.customCards.push({
  type: 'freezer-inventory-card',
  name: 'Freezer Inventory',
  description: 'Shows freezer items with expiration dates and portion counts',
});
