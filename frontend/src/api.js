import { frappeRequest } from 'frappe-ui'

export function call(method, params = {}) {
  return frappeRequest({ url: `/api/method/${method}`, method: 'POST', params })
}
