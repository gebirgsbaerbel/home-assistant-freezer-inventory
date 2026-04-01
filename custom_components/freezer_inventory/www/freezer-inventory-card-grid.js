class FreezerInventoryCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._items = [];
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
    if (JSON.stringify(items) !== JSON.stringify(this._items)) {
      this._items = items;
      this._render();
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
    const title = this._config.title;

    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        ha-card { overflow: hidden; }
        .header {
          padding: 16px 16px 0;
          font-size: var(--ha-card-header-font-size, 1.1em);
          font-weight: 500;
          color: var(--ha-card-header-color, var(--primary-text-color));
        }
        .grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
          gap: 8px;
          padding: 12px;
        }
        .tile {
          background: var(--secondary-background-color);
          border-radius: 12px;
          padding: 12px 8px;
          text-align: center;
          cursor: pointer;
          user-select: none;
          transition: opacity 0.15s, transform 0.1s;
          -webkit-tap-highlight-color: transparent;
        }
        .tile:hover { opacity: 0.8; }
        .tile:active { transform: scale(0.94); }
        .tile-icon { font-size: 1.5em; margin-bottom: 4px; }
        .tile-name {
          font-size: 1.2em;
          font-weight: 500;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          text-align: left;
        }
        .tile-label {
          font-size: 0.8em;
          color: var(--secondary-text-color);
          margin-top: 2px;
          text-align: left;
        }
        .empty {
          text-align: center;
          color: var(--secondary-text-color);
          padding: 24px;
          font-size: 0.9em;
        }
      </style>
      <ha-card>
        ${items.length
          ? `<div class="grid">${items.map((item, i) => `
              <div class="tile" data-i="${i}">
                <div class="tile-name">${this._escapeHtml(item.description)}</div>
                <div class="tile-label">${item.portions} <ha-icon icon="mdi:food-takeout-box-outline"></ha-icon>${item.expiration ? ' · ' + this._formatDate(item.expiration) : ''}</div>
              </div>`).join('')}
            </div>`
          : '<div class="empty">Freezer is empty ❄️</div>'
        }
      </ha-card>`;

    this.shadowRoot.querySelectorAll('.tile').forEach(el => {
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

    // Notify HA that the card size may have changed
    window.dispatchEvent(new Event('resize'));
  }

  getCardSize() {
    const rows = Math.max(1, Math.ceil(this._items.length / 3));
    const titleRows = this._config?.title != null ? 1 : 0;
    return rows * 2 + titleRows + 1;
  }

  getLayoutOptions() {
    const tileRows = Math.max(1, Math.ceil(this._items.length / 3));
    const rows = this._config?.rows ?? Math.ceil(tileRows * 1.34);
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
