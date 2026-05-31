/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Fraunces', 'Georgia', 'serif'],
        body: ['Fraunces', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        // Deep base
        void: '#0b0b0f',
        ink: '#11121a',
        smoke: '#16171f',
        ash: '#1d1e28',
        bone: '#2a2b36',

        // Text
        cream: '#e9e2cf',
        parchment: '#d8cfb6',
        mist: '#8e8a7d',
        ghost: '#5a5852',

        // Accents
        ember: '#ea580c',
        emberDim: '#9a3a06',
        gold: '#c9a96e',
        goldDim: '#8c7344',
        sage: '#5a8a7a',
        rose: '#b9472f',
        lilac: '#9d88b8',

        rule: 'rgba(201, 169, 110, 0.10)',
        ruleStrong: 'rgba(201, 169, 110, 0.22)',
      },
      letterSpacing: {
        tightest: '-0.045em',
        widest2: '0.22em',
      },
      fontSize: {
        '7xl': ['5rem', { lineHeight: '0.92' }],
        '8xl': ['6.5rem', { lineHeight: '0.9' }],
        '9xl': ['8rem', { lineHeight: '0.88' }],
      },
      animation: {
        'drift-a': 'drift-a 22s ease-in-out infinite alternate',
        'drift-b': 'drift-b 28s ease-in-out infinite alternate',
        'fade-up': 'fade-up 0.9s cubic-bezier(0.22, 1, 0.36, 1) both',
      },
      keyframes: {
        'drift-a': {
          '0%': { transform: 'translate(0, 0) scale(1)' },
          '100%': { transform: 'translate(-6vw, 6vh) scale(1.12)' },
        },
        'drift-b': {
          '0%': { transform: 'translate(0, 0) scale(1)' },
          '100%': { transform: 'translate(5vw, -5vh) scale(1.15)' },
        },
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(14px)', filter: 'blur(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)', filter: 'blur(0)' },
        },
      },
    },
  },
  plugins: [],
};
