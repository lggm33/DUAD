/**
 * Footer Component
 * Reusable footer for the application
 */

/**
 * @typedef {Object} FooterLink
 * @property {string} href - Link URL
 * @property {string} label - Link text
 */

/**
 * @typedef {Object} FooterOptions
 * @property {FooterLink[]} [links] - Navigation links to display
 * @property {boolean} [showLinks=true] - Whether to show the links section
 */

const DEFAULT_LINKS = [
  { href: '#features', label: 'Features' },
  { href: '#roles', label: 'Roles' },
  { href: '#about', label: 'About' }
]

/**
 * Renders the footer component
 * @param {FooterOptions} options
 * @returns {string} HTML string
 */
export function Footer(options = {}) {
  const { links = DEFAULT_LINKS, showLinks = true } = options
  const currentYear = new Date().getFullYear()

  const linksHtml = showLinks ? `
    <div class="footer-links">
      ${links.map(link => `<a href="${link.href}">${link.label}</a>`).join('\n      ')}
    </div>
  ` : ''

  return `
    <footer class="footer">
      <div class="footer-content">
        <div class="footer-brand">
          <img src="/logo.png" alt="Lyfter DnD" class="footer-logo" />
          <p>Enhancing your D&D experience</p>
        </div>
        ${linksHtml}
      </div>
      <div class="footer-bottom">
        <p>&copy; ${currentYear} Lyfter DnD. All rights reserved.</p>
      </div>
    </footer>
  `
}

