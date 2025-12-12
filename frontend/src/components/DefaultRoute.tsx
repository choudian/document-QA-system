import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { getDefaultRoute } from '@/utils/getDefaultRoute'

const DefaultRoute = () => {
  const [route, setRoute] = useState<string | null>(null)

  useEffect(() => {
    getDefaultRoute().then(setRoute)
  }, [])

  if (route === null) {
    // 加载中，可以显示一个加载提示
    return <div style={{ textAlign: 'center', padding: '50px' }}>加载中...</div>
  }

  return <Navigate to={route} replace />
}

export default DefaultRoute
