/**
 * Game Creator Templates
 * Pure functions that return HTML strings for each section
 */

import {
  ATTRIBUTE_METHODS,
  CREATION_MODES,
  DEFAULT_ACTIONS,
  CRITICAL_HIT_RULES,
  AVAILABLE_RACES,
  AVAILABLE_CLASSES
} from './constants.js'

/**
 * Escape HTML to prevent XSS
 */
export function escapeHtml(text) {
  if (!text) return ''
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

/**
 * Loading state template
 */
export function loadingTemplate() {
  return `
    <div class="gc-loading">
      <span class="loader loader-lg"></span>
      <span>Loading game options...</span>
    </div>
  `
}

/**
 * Error message template
 */
export function errorTemplate(message) {
  return `
    <div class="gc-error">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="15" y1="9" x2="9" y2="15"></line>
        <line x1="9" y1="9" x2="15" y2="15"></line>
      </svg>
      <span>${escapeHtml(message)}</span>
    </div>
  `
}

/**
 * Basic info section template
 */
export function basicInfoTemplate(formData, templates, selectedTemplateId) {
  return `
    <div class="gc-section">
      <div class="gc-section-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="16" x2="12" y2="12"></line>
          <line x1="12" y1="8" x2="12.01" y2="8"></line>
        </svg>
        Basic Information
      </div>
      
      <div class="gc-form-group">
        <label class="gc-label" for="gc-game-name">
          Game Name <span style="color: var(--color-error)">*</span>
        </label>
        <input 
          type="text" 
          id="gc-game-name" 
          class="gc-input" 
          placeholder="Enter your adventure name..."
          value="${escapeHtml(formData.name)}"
          required
          minlength="3"
          maxlength="100"
        />
      </div>

      <div class="gc-form-group">
        <label class="gc-label" for="gc-template">
          Ruleset Template
          <span class="gc-label-hint">(optional)</span>
        </label>
        <select id="gc-template" class="gc-select">
          ${templates.map(t => `
            <option value="${t.id}" ${selectedTemplateId === t.id ? 'selected' : ''}>
              ${escapeHtml(t.name)}
            </option>
          `).join('')}
        </select>
        ${selectedTemplateId ? `
          <div class="gc-template-info">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
            Template rules will be used as base. You can customize below.
          </div>
        ` : ''}
      </div>
    </div>
  `
}

/**
 * Character rules collapsible section template
 */
export function characterRulesTemplate(formData, isOpen) {
  const { character } = formData

  return `
    <div class="gc-collapsible ${isOpen ? 'is-open' : ''}" data-section="character">
      <div class="gc-collapsible-header">
        <div class="gc-collapsible-header-left">
          <div class="gc-collapsible-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
          </div>
          <h3 class="gc-collapsible-title">Character Rules</h3>
        </div>
        <svg class="gc-collapsible-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </div>
      <div class="gc-collapsible-content">
        ${characterRulesFormContent(character)}
      </div>
    </div>
  `
}

/**
 * Character rules form content
 */
function characterRulesFormContent(character) {
  return `
    ${creationModeSection(character)}
    ${levelSection(character)}
    ${attributeMethodSection(character)}
    ${racesSection(character)}
    ${classesSection(character)}
    ${togglesSection(character)}
  `
}

/**
 * Creation mode radio group
 */
function creationModeSection(character) {
  return `
    <div class="gc-form-group">
      <label class="gc-label">Character Approval</label>
      <div class="gc-radio-group">
        ${CREATION_MODES.map(mode => `
          <label class="gc-radio">
            <input 
              type="radio" 
              name="creation_mode" 
              value="${mode.value}"
              ${character.creation_mode === mode.value ? 'checked' : ''}
            />
            <span class="gc-radio-label">${mode.label}</span>
          </label>
        `).join('')}
      </div>
    </div>
  `
}

/**
 * Level configuration section
 */
function levelSection(character) {
  return `
    <div class="gc-row">
      <div class="gc-form-group">
        <label class="gc-label" for="gc-start-level">Starting Level</label>
        <input 
          type="number" 
          id="gc-start-level" 
          class="gc-input" 
          min="1" 
          max="20" 
          value="${character.level.default}"
        />
      </div>

      <div class="gc-form-group">
        <label class="gc-label" for="gc-max-level">Max Level</label>
        <input 
          type="number" 
          id="gc-max-level" 
          class="gc-input" 
          min="1" 
          max="20" 
          value="${character.level.max}"
        />
      </div>
    </div>
  `
}

/**
 * Attribute method section
 */
function attributeMethodSection(character) {
  return `
    <div class="gc-form-group">
      <label class="gc-label" for="gc-attr-method">Attribute Generation Method</label>
      <select id="gc-attr-method" class="gc-select">
        ${ATTRIBUTE_METHODS.map(method => `
          <option value="${method.value}" ${character.attributes.method === method.value ? 'selected' : ''}>
            ${method.label}
          </option>
        `).join('')}
      </select>
    </div>

    <div class="gc-form-group" id="gc-point-buy-group" ${character.attributes.method !== 'point_buy' ? 'hidden' : ''}>
      <label class="gc-label" for="gc-point-buy-total">Point Buy Total</label>
      <div class="gc-number-input">
        <input 
          type="number" 
          id="gc-point-buy-total" 
          class="gc-input" 
          min="0" 
          max="100" 
          value="${character.attributes.point_buy.total_points}"
        />
        <span class="gc-number-unit">points</span>
      </div>
    </div>
  `
}

/**
 * Races configuration section
 */
function racesSection(character) {
  const allowAll = character.races?.allow_all !== false

  return `
    <div class="gc-subsection">
      <div class="gc-subsection-title">Allowed Races</div>
      
      <div class="gc-toggle-group">
        <span class="gc-toggle-label">Allow All Races</span>
        <label class="gc-toggle">
          <input type="checkbox" id="gc-races-allow-all" ${allowAll ? 'checked' : ''} />
          <span class="gc-toggle-slider"></span>
        </label>
      </div>

      <div id="gc-races-config" ${allowAll ? 'hidden' : ''}>
        <div class="gc-form-group">
          <label class="gc-label">Select Allowed Races</label>
          <div class="gc-checkbox-grid">
            ${AVAILABLE_RACES.map(race => `
              <label class="gc-checkbox-item">
                <input 
                  type="checkbox" 
                  name="allowed_races" 
                  value="${race}"
                  ${character.races?.allowed?.includes(race) ? 'checked' : ''}
                />
                <span>${race}</span>
              </label>
            `).join('')}
          </div>
        </div>
      </div>

      <div class="gc-form-group">
        <label class="gc-label">Banned Races <span class="gc-label-hint">(always blocked)</span></label>
        <div class="gc-checkbox-grid gc-checkbox-grid-banned">
          ${AVAILABLE_RACES.map(race => `
            <label class="gc-checkbox-item">
              <input 
                type="checkbox" 
                name="banned_races" 
                value="${race}"
                ${character.races?.banned?.includes(race) ? 'checked' : ''}
              />
              <span>${race}</span>
            </label>
          `).join('')}
        </div>
      </div>
    </div>
  `
}

/**
 * Classes configuration section
 */
function classesSection(character) {
  const allowAll = character.classes?.allow_all !== false

  return `
    <div class="gc-subsection">
      <div class="gc-subsection-title">Allowed Classes</div>
      
      <div class="gc-toggle-group">
        <span class="gc-toggle-label">Allow All Classes</span>
        <label class="gc-toggle">
          <input type="checkbox" id="gc-classes-allow-all" ${allowAll ? 'checked' : ''} />
          <span class="gc-toggle-slider"></span>
        </label>
      </div>

      <div id="gc-classes-config" ${allowAll ? 'hidden' : ''}>
        <div class="gc-form-group">
          <label class="gc-label">Select Allowed Classes</label>
          <div class="gc-checkbox-grid">
            ${AVAILABLE_CLASSES.map(cls => `
              <label class="gc-checkbox-item">
                <input 
                  type="checkbox" 
                  name="allowed_classes" 
                  value="${cls}"
                  ${character.classes?.allowed?.includes(cls) ? 'checked' : ''}
                />
                <span>${cls}</span>
              </label>
            `).join('')}
          </div>
        </div>
      </div>

      <div class="gc-form-group">
        <label class="gc-label">Banned Classes <span class="gc-label-hint">(always blocked)</span></label>
        <div class="gc-checkbox-grid gc-checkbox-grid-banned">
          ${AVAILABLE_CLASSES.map(cls => `
            <label class="gc-checkbox-item">
              <input 
                type="checkbox" 
                name="banned_classes" 
                value="${cls}"
                ${character.classes?.banned?.includes(cls) ? 'checked' : ''}
              />
              <span>${cls}</span>
            </label>
          `).join('')}
        </div>
      </div>
    </div>
  `
}

/**
 * Character toggles section
 */
function togglesSection(character) {
  return `
    <div class="gc-toggle-group">
      <span class="gc-toggle-label">Allow Multiclassing</span>
      <label class="gc-toggle">
        <input type="checkbox" id="gc-allow-multiclass" ${character.classes?.allow_multiclass ? 'checked' : ''} />
        <span class="gc-toggle-slider"></span>
      </label>
    </div>

    <div class="gc-toggle-group">
      <span class="gc-toggle-label">Require Character Backstory</span>
      <label class="gc-toggle">
        <input type="checkbox" id="gc-backstory-required" ${character.backstory?.required ? 'checked' : ''} />
        <span class="gc-toggle-slider"></span>
      </label>
    </div>

    <div class="gc-toggle-group">
      <span class="gc-toggle-label">Allow Custom Backgrounds</span>
      <label class="gc-toggle">
        <input type="checkbox" id="gc-custom-backgrounds" ${character.allow_custom_backgrounds ? 'checked' : ''} />
        <span class="gc-toggle-slider"></span>
      </label>
    </div>
  `
}

/**
 * Combat settings collapsible section template
 */
export function combatSettingsTemplate(formData, isOpen) {
  const { combat } = formData

  return `
    <div class="gc-collapsible ${isOpen ? 'is-open' : ''}" data-section="combat">
      <div class="gc-collapsible-header">
        <div class="gc-collapsible-header-left">
          <div class="gc-collapsible-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14.5 10c-.83 0-1.5-.67-1.5-1.5v-5c0-.83.67-1.5 1.5-1.5s1.5.67 1.5 1.5v5c0 .83-.67 1.5-1.5 1.5z"></path>
              <path d="M20.5 10H19V8.5c0-.83.67-1.5 1.5-1.5s1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"></path>
              <path d="M9.5 14c.83 0 1.5.67 1.5 1.5v5c0 .83-.67 1.5-1.5 1.5S8 21.33 8 20.5v-5c0-.83.67-1.5 1.5-1.5z"></path>
              <path d="M3.5 14H5v1.5c0 .83-.67 1.5-1.5 1.5S2 16.33 2 15.5 2.67 14 3.5 14z"></path>
              <path d="M14 14.5c0-.83.67-1.5 1.5-1.5h5c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5h-5c-.83 0-1.5-.67-1.5-1.5z"></path>
              <path d="M15.5 19H14v1.5c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5-.67-1.5-1.5-1.5z"></path>
              <path d="M10 9.5C10 8.67 9.33 8 8.5 8h-5C2.67 8 2 8.67 2 9.5S2.67 11 3.5 11h5c.83 0 1.5-.67 1.5-1.5z"></path>
              <path d="M8.5 5H10V3.5C10 2.67 9.33 2 8.5 2S7 2.67 7 3.5 7.67 5 8.5 5z"></path>
            </svg>
          </div>
          <h3 class="gc-collapsible-title">Combat Settings</h3>
        </div>
        <svg class="gc-collapsible-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </div>
      <div class="gc-collapsible-content">
        ${combatSettingsFormContent(combat)}
      </div>
    </div>
  `
}

/**
 * Combat settings form content
 */
function combatSettingsFormContent(combat) {
  return `
    ${turnTimeoutSection(combat)}
    ${disconnectionSection(combat)}
    ${combatRulesSection(combat)}
  `
}

/**
 * Turn timeout section
 */
function turnTimeoutSection(combat) {
  return `
    <div class="gc-toggle-group">
      <span class="gc-toggle-label">Enable Turn Timeout</span>
      <label class="gc-toggle">
        <input type="checkbox" id="gc-turn-timeout" ${combat.turn_timeout.enabled ? 'checked' : ''} />
        <span class="gc-toggle-slider"></span>
      </label>
    </div>

    <div id="gc-timeout-settings" ${!combat.turn_timeout.enabled ? 'hidden' : ''}>
      <div class="gc-row">
        <div class="gc-form-group">
          <label class="gc-label" for="gc-grace-period">Grace Period</label>
          <div class="gc-number-input">
            <input 
              type="number" 
              id="gc-grace-period" 
              class="gc-input" 
              min="10" 
              max="300" 
              value="${combat.turn_timeout.grace_period_seconds}"
            />
            <span class="gc-number-unit">seconds</span>
          </div>
        </div>

        <div class="gc-form-group">
          <label class="gc-label" for="gc-max-wait">Max Wait Time</label>
          <div class="gc-number-input">
            <input 
              type="number" 
              id="gc-max-wait" 
              class="gc-input" 
              min="30" 
              max="600" 
              value="${combat.turn_timeout.max_wait_seconds}"
            />
            <span class="gc-number-unit">seconds</span>
          </div>
        </div>
      </div>

      <div class="gc-form-group">
        <label class="gc-label" for="gc-default-action">Default Action on Timeout</label>
        <select id="gc-default-action" class="gc-select">
          ${DEFAULT_ACTIONS.map(action => `
            <option value="${action.value}" ${combat.turn_timeout.default_action === action.value ? 'selected' : ''}>
              ${action.label}
            </option>
          `).join('')}
        </select>
      </div>
    </div>
  `
}

/**
 * Disconnection settings section
 */
function disconnectionSection(combat) {
  return `
    <div class="gc-toggle-group">
      <span class="gc-toggle-label">Show Disconnect Status to Party</span>
      <label class="gc-toggle">
        <input type="checkbox" id="gc-show-disconnect" ${combat.disconnection.show_status_to_party ? 'checked' : ''} />
        <span class="gc-toggle-slider"></span>
      </label>
    </div>

    <div class="gc-toggle-group">
      <span class="gc-toggle-label">Allow DM to Control Disconnected Characters</span>
      <label class="gc-toggle">
        <input type="checkbox" id="gc-dm-control" ${combat.disconnection.allow_dm_control ? 'checked' : ''} />
        <span class="gc-toggle-slider"></span>
      </label>
    </div>

    <div class="gc-toggle-group">
      <span class="gc-toggle-label">Auto-pause Combat on Disconnect</span>
      <label class="gc-toggle">
        <input type="checkbox" id="gc-auto-pause" ${combat.disconnection.auto_pause_on_disconnect ? 'checked' : ''} />
        <span class="gc-toggle-slider"></span>
      </label>
    </div>
  `
}

/**
 * Combat rules section
 */
function combatRulesSection(combat) {
  return `
    <div class="gc-toggle-group">
      <span class="gc-toggle-label">Flanking Gives Advantage</span>
      <label class="gc-toggle">
        <input type="checkbox" id="gc-flanking" ${combat.flanking_gives_advantage ? 'checked' : ''} />
        <span class="gc-toggle-slider"></span>
      </label>
    </div>

    <div class="gc-form-group">
      <label class="gc-label" for="gc-critical-rule">Critical Hit Rule</label>
      <select id="gc-critical-rule" class="gc-select">
        ${CRITICAL_HIT_RULES.map(rule => `
          <option value="${rule.value}" ${combat.critical_hit_rule === rule.value ? 'selected' : ''}>
            ${rule.label}
          </option>
        `).join('')}
      </select>
    </div>
  `
}

/**
 * Render complete form
 */
export function renderFullForm(formData, options) {
  const { templates, selectedTemplateId, error, collapsibleStates } = options

  return `
    ${error ? errorTemplate(error) : ''}
    ${basicInfoTemplate(formData, templates, selectedTemplateId)}
    ${characterRulesTemplate(formData, collapsibleStates.character)}
    ${combatSettingsTemplate(formData, collapsibleStates.combat)}
  `
}

