'use client'

import React, { useState } from 'react'
import { Copy, Check } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { vibrate } from '@/shared/vibration'
import { useTranslations } from 'next-intl'

interface CopyButtonProps {
  value: string
  className?: string
  iconSize?: number
  toastSuccess?: boolean
}

export const CopyButton: React.FC<CopyButtonProps> = ({
  value,
  className = '',
  iconSize = 20,
  toastSuccess = true,
}) => {
  const t = useTranslations('common')
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value)
      vibrate()
      if (toastSuccess) toast.success(t('copied'))
      setCopied(true)
      setTimeout(() => setCopied(false), 1600)
    } catch (e) {
      toast.error(t('copy_error'))
    }
  }

  return (
    <button
      onClick={handleCopy}
      aria-label={t('copy')}
      className={`transition text-white hover:text-blue-500 ${className}`}
    >
      {copied ? (
        <Check size={iconSize} className="text-green-400" />
      ) : (
        <Copy size={iconSize} />
      )}
    </button>
  )
}
