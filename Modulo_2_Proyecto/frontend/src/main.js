import './styles/index.css'
import './styles/app.css'
import './styles/inventory.css'
import './styles/pages/profile.css'
import './styles/pages/notes.css'
import { 
  registerRoute, 
  registerProtectedRoute, 
  registerGuestRoute,
  registerDynamicProtectedRoute,
  initRouter 
} from './router.js'
import { landingPage } from './pages/landing.js'
import { signInPage } from './pages/sign-in.js'
import { signUpPage } from './pages/sign-up.js'
import { dashboardPage } from './pages/dashboard.js'
import { profilePage } from './pages/profile.js'
import { gamePage } from './pages/game/index.js'
import { joinPage } from './pages/join.js'
import { historyPage } from './pages/history.js'
import { inventoryPage } from './pages/inventory.js'
import { notesPage } from './pages/notes.js'

const app = document.querySelector('#app')

// Public routes (accessible to everyone)
registerRoute('/', () => landingPage(app))

// Guest-only routes (redirect to dashboard if already logged in)
registerGuestRoute('/sign-in', () => signInPage(app))
registerGuestRoute('/sign-up', () => signUpPage(app))

// Protected routes (redirect to sign-in if not authenticated)
registerProtectedRoute('/dashboard', () => dashboardPage(app))
registerProtectedRoute('/profile', () => profilePage(app))

// Dynamic protected routes
registerDynamicProtectedRoute('/game/:id', () => gamePage(app))
registerDynamicProtectedRoute('/game/:id/history', () => historyPage(app))
registerDynamicProtectedRoute('/game/:id/inventory', () => inventoryPage(app))
registerDynamicProtectedRoute('/game/:id/notes', () => notesPage(app))
registerDynamicProtectedRoute('/join/:code', () => joinPage(app))

// 404 fallback
registerRoute('/404', () => landingPage(app))

// Initialize router
initRouter()
