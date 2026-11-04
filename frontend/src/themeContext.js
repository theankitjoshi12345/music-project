import { createContext, useContext } from 'react'

export const themes = [
  { id: 'violet', name: 'Violet Jam', description: 'Lavender, peach & a little lime' },
  { id: 'peach', name: 'Peach Pop', description: 'Warm peach & berry pink' },
  { id: 'mint', name: 'Mint Groove', description: 'Fresh mint & sunshine yellow' },
]
export const ThemeContext = createContext({ theme: 'violet', setTheme() {} })
export function useTheme() { return useContext(ThemeContext) }
