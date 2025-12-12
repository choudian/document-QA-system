import { useState, useEffect } from 'react'
import { getTokenPayload, TokenPayload } from '@/utils/token'

export function useCurrentUser() {
  const [user, setUser] = useState<TokenPayload | null>(null)

  useEffect(() => {
    const payload = getTokenPayload()
    setUser(payload)
  }, [])

  return user
}

