export interface HealthCheck {
  status: string
  checks: {
    db: string
    redis: string
  }
}


