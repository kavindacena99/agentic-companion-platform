import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { agentService } from '../services/agentService'
import { profileService } from '../services/profileService'
import { subscriptionService } from '../services/subscriptionService'
import { usageService } from '../services/usageService'

const ProductContext = createContext(null)

export function ProductProvider({ children }) {
  const [profile, setProfile] = useState(null)
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [usage, setUsage] = useState(null)
  const [subscription, setSubscription] = useState(null)

  const refreshProfile = useCallback(async () => {
    const data = await profileService.getProfile()
    setProfile(data)
    return data
  }, [])

  const refreshSelectedAgent = useCallback(async () => {
    const data = await agentService.getSelectedAgent()
    setSelectedAgent(data)
    return data
  }, [])

  const refreshUsage = useCallback(async () => {
    const data = await usageService.getUsage()
    setUsage(data)
    return data
  }, [])

  const refreshSubscription = useCallback(async () => {
    const data = await subscriptionService.getCurrentSubscription()
    setSubscription(data)
    return data
  }, [])

  const refreshProductState = useCallback(async () => {
    const results = await Promise.allSettled([
      refreshProfile(),
      refreshSelectedAgent(),
      refreshUsage(),
      refreshSubscription(),
    ])
    return results
  }, [refreshProfile, refreshSelectedAgent, refreshUsage, refreshSubscription])

  const value = useMemo(
    () => ({
      profile,
      selectedAgent,
      usage,
      subscription,
      setProfile,
      setSelectedAgent,
      setUsage,
      setSubscription,
      refreshProfile,
      refreshSelectedAgent,
      refreshUsage,
      refreshSubscription,
      refreshProductState,
    }),
    [
      profile,
      selectedAgent,
      usage,
      subscription,
      refreshProfile,
      refreshSelectedAgent,
      refreshUsage,
      refreshSubscription,
      refreshProductState,
    ],
  )

  return <ProductContext.Provider value={value}>{children}</ProductContext.Provider>
}

export function useProduct() {
  const context = useContext(ProductContext)
  if (!context) {
    throw new Error('useProduct must be used inside ProductProvider')
  }
  return context
}
