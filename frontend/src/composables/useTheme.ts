import { ref, watch, onMounted } from 'vue'
import { useDark } from '@vueuse/core'

export type ThemeType = 'default' | 'forest' | 'latte' | 'geek' | 'apple'

const currentTheme = ref<ThemeType>('default')
const isDark = useDark()

export function useTheme() {
  const initTheme = () => {
    const savedTheme = localStorage.getItem('insight_theme') as ThemeType
    if (savedTheme) {
      currentTheme.value = savedTheme
    }
    applyTheme(currentTheme.value)
  }

  const applyTheme = (theme: ThemeType) => {
    const html = document.documentElement
    // Remove all existing theme classes
    html.classList.remove('theme-forest', 'theme-latte', 'theme-geek', 'theme-apple')
    
    if (theme !== 'default') {
      html.classList.add(`theme-${theme}`)
    }
    
    // Geek theme forces dark mode visually, but we might just let it be handled by CSS
    if (theme === 'geek') {
      // isDark.value = true // Optional: force dark mode toggle
    }
  }

  const setTheme = (theme: ThemeType) => {
    currentTheme.value = theme
    localStorage.setItem('insight_theme', theme)
    applyTheme(theme)
  }

  return {
    isDark,
    currentTheme,
    setTheme,
    initTheme
  }
}
