/**
 * Navbar Component
 * Reusable navigation bar for the application
 */

/**
 * @typedef {Object} NavbarOptions
 * @property {boolean} [showAuthButtons=true] - Show sign in/sign up buttons
 * @property {boolean} [showLinks=true] - Show navigation links
 */

/**
 * Renders the navbar component
 * @param {NavbarOptions} options
 * @returns {string} HTML string
 */
export function Navbar(options = {}) {
  const { showAuthButtons = true, showLinks = true } = options

  const linksHtml = showLinks ? `
    <nav class="navbar-links">
      <a href="#features" class="nav-link">Features</a>
      <a href="#roles" class="nav-link">Roles</a>
      <a href="#about" class="nav-link">About</a>
    </nav>
  ` : ''

  const authButtonsHtml = showAuthButtons ? `
    <div class="navbar-actions">
      <a href="/sign-in" data-link class="btn btn-ghost">Sign In</a>
      <a href="/sign-up" data-link class="btn btn-primary">Get Started</a>
    </div>
  ` : ''

  return `
    <header class="navbar">
      <a href="/" data-link class="navbar-brand">
        <img src="/logo.png" alt="Lyfter DnD" class="navbar-logo" />
        <span class="brand-text">Lyfter</span>
      </a>
      ${linksHtml}
      ${authButtonsHtml}
    </header>
  `
}

