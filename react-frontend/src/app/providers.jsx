import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../context/AuthContext'
import { ProductProvider } from '../context/ProductContext'

export function AppProviders({ children }) {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ProductProvider>{children}</ProductProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
