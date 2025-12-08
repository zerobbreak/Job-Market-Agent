import { apiClient } from './api'

export async function track(event: string, properties?: Record<string, any>, page?: string) {
  try {
    await apiClient('/analytics', {
      method: 'POST',
      body: JSON.stringify({ event, properties, page }),
    })
  } catch (e) {
    console.warn('Analytics track failed', e)
  }
}
