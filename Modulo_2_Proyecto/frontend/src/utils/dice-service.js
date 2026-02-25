/**
 * Dice Service
 * Handles rolling dice and displaying results
 */

export class DiceService {
  /**
   * Roll dice based on a formula like "1d20+5" or "2d6"
   * @param {string} formula - Dice formula
   * @returns {Object} - Result containing total, rolls, and modifier
   */
  static roll(formula) {
    const diceRegex = /^(\d+)d(\d+)([+-]\d+)?$/i
    const match = formula.trim().match(diceRegex)

    if (!match) {
      throw new Error(`Invalid dice formula: ${formula}`)
    }

    const count = parseInt(match[1], 10)
    const sides = parseInt(match[2], 10)
    const modifier = match[3] ? parseInt(match[3], 10) : 0

    const rolls = []
    let total = 0

    for (let i = 0; i < count; i++) {
      const roll = Math.floor(Math.random() * sides) + 1
      rolls.push(roll)
      total += roll
    }

    total += modifier

    return {
      total,
      rolls,
      modifier,
      sides,
      count,
      formula
    }
  }

  /**
   * Show an animated roll result in the UI
   * @param {Object} result - Result from roll()
   * @param {string} title - Optional title for the roll (e.g. "Attack Roll")
   */
  static async showRollResult(result, title = 'Roll Result') {
    // Create overlay
    const overlay = document.createElement('div')
    overlay.className = 'dice-roll-overlay'
    
    const isCrit = result.sides === 20 && result.rolls[0] === 20
    const isFail = result.sides === 20 && result.rolls[0] === 1

    overlay.innerHTML = `
      <div class="dice-roll-content ${isCrit ? 'is-crit' : ''} ${isFail ? 'is-fail' : ''}">
        <div class="dice-roll-header">${title}</div>
        <div class="dice-roll-formula">${result.formula}</div>
        <div class="dice-roll-animation">
          <span class="dice-roll-number">?</span>
        </div>
        <div class="dice-roll-total" style="display: none">
          ${result.total}
        </div>
        <div class="dice-roll-details" style="display: none">
          (${result.rolls.join(' + ')})${result.modifier !== 0 ? (result.modifier > 0 ? ' + ' + result.modifier : ' - ' + Math.abs(result.modifier)) : ''}
        </div>
      </div>
    `

    document.body.appendChild(overlay)

    const numberEl = overlay.querySelector('.dice-roll-number')
    const totalEl = overlay.querySelector('.dice-roll-total')
    const detailsEl = overlay.querySelector('.dice-roll-details')

    // Animation
    let frames = 0
    const maxFrames = 15
    const interval = setInterval(() => {
      numberEl.textContent = Math.floor(Math.random() * result.sides) + 1
      frames++
      if (frames >= maxFrames) {
        clearInterval(interval)
        numberEl.textContent = result.total
        numberEl.classList.add('is-final')
        
        setTimeout(() => {
          totalEl.style.display = 'block'
          detailsEl.style.display = 'block'
        }, 200)

        // Auto remove after 3 seconds
        setTimeout(() => {
          overlay.classList.add('is-fading')
          setTimeout(() => overlay.remove(), 500)
        }, 3000)
      }
    }, 50, frames)

    // Click to dismiss faster
    overlay.addEventListener('click', () => {
      overlay.remove()
    })

    return result
  }
}

