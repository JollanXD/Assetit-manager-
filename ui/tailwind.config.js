/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', 'src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        surface: {
          0: '#161616',
          50: '#1a1a1a',
          100: '#1e1e1e',
          200: '#242424',
          300: '#2a2a2a',
          400: '#333333',
          500: '#3a3a3a',
          600: '#444444',
          700: '#505050',
          800: '#5c5c5c',
        },
        accent: {
          DEFAULT: '#00A3FF',
          50: '#e5f6ff',
          100: '#b3e0ff',
          200: '#80ccff',
          300: '#4db8ff',
          400: '#1aa4ff',
          500: '#00A3FF',
          600: '#0080cc',
          700: '#006699',
          800: '#004d66',
        },
      },
      animation: {
        'fade-in': 'fadeIn 0.15s ease-out',
        'slide-in-right': 'slideInRight 0.2s cubic-bezier(0.16,1,0.3,1)',
        'slide-up': 'slideUp 0.2s cubic-bezier(0.16,1,0.3,1)',
        'scale-in': 'scaleIn 0.12s cubic-bezier(0.16,1,0.3,1)',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideInRight: {
          '0%': { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(8px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.96)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
};
