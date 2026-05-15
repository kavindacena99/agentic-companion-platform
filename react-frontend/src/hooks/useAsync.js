/* eslint-disable react-hooks/exhaustive-deps */
import { useCallback, useEffect, useState } from 'react'
import { getApiErrorMessage } from '../services/apiClient'

export function useAsync(loader, dependencies = [], options = {}) {
  const [data, setData] = useState(options.initialData ?? null)
  const [loading, setLoading] = useState(Boolean(options.immediate ?? true))
  const [error, setError] = useState('')

  const run = useCallback(async (...args) => {
    setLoading(true)
    setError('')
    try {
      const result = await loader(...args)
      setData(result)
      return result
    } catch (caughtError) {
      const message = getApiErrorMessage(caughtError)
      setError(message)
      throw caughtError
    } finally {
      setLoading(false)
    }
  }, dependencies)

  useEffect(() => {
    if (options.immediate === false) {
      setLoading(false)
      return
    }
    run()
  }, [run, options.immediate])

  return { data, setData, loading, error, setError, run }
}
