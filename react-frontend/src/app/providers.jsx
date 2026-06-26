import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../context/AuthContext'
import { ProductProvider } from '../context/ProductContext'
import { ThemeProvider } from '../context/ThemeContext'

export function AppProviders({ children }) {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <ProductProvider>{children}</ProductProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}
