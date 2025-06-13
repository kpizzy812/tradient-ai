export interface PoolInfo {
  name: string
  coefficient: number
  yield_range: [number, number]
  description: string
  min_invest: number
  user_balance: number
  reinvest: boolean
}
