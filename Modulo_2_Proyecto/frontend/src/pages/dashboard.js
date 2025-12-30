import template from './dashboard.html?raw'
import { Footer } from '../components/index.js'

export function dashboardPage(app) {
  app.innerHTML = template + Footer()
}