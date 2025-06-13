// frontend/src/shared/hooks/useWithdrawFees.ts
import { useState, useEffect } from 'react'
import { useProfile } from './useProfile'

export interface WithdrawFeeInfo {
  days_since_deposit: number
  commission_rate: number
  commission_amount: number
  final_amount: number
  execute_days: number
  description: string
}

export interface PoolWithdrawInfo {
  pool_name: string
  user_balance: number
  days_since_first_deposit: number
  standard_mode: WithdrawFeeInfo
  express_mode: WithdrawFeeInfo
}

export interface WithdrawFeesData {
  pool_withdrawals: PoolWithdrawInfo[]
  balance_withdrawal: {
    available_balance: number
    commission_rate: number
    processing_time: string
    description: string
    min_amounts: Record<string, number>
  }
  fee_tiers: Record<number, number>
  express_fee: number
}

export const useWithdrawFees = () => {
  const { profile } = useProfile()
  const [feesData, setFeesData] = useState<WithdrawFeesData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchFeesData = async () => {
    if (!profile?.user_id) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/withdraw/fees/${profile.user_id}`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setFeesData(data)
    } catch (err) {
      console.error('Failed to fetch withdraw fees:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch fees')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchFeesData()
  }, [profile?.user_id])

  const getPoolFees = (poolName: string) => {
    return feesData?.pool_withdrawals.find(p => p.pool_name === poolName)
  }

  const calculateFees = (amount: number, mode: 'standard' | 'express', poolName?: string) => {
    if (!feesData) return null

    if (poolName) {
      const poolInfo = getPoolFees(poolName)
      if (!poolInfo) return null

      const feeInfo = mode === 'express' ? poolInfo.express_mode : poolInfo.standard_mode
      const commission = amount * feeInfo.commission_rate
      const finalAmount = amount - commission

      return {
        commission,
        finalAmount,
        commissionRate: feeInfo.commission_rate,
        executeDays: feeInfo.execute_days,
        description: feeInfo.description
      }
    } else {
      // Вывод с баланса - без комиссии
      return {
        commission: 0,
        finalAmount: amount,
        commissionRate: 0,
        executeDays: 1,
        description: feesData.balance_withdrawal.description
      }
    }
  }

  return {
    feesData,
    loading,
    error,
    refetch: fetchFeesData,
    getPoolFees,
    calculateFees
  }
}