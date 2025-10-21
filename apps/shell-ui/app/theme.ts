'use client'

import { createTheme } from '@mui/material/styles'

// Kyros brand colors
const kyrosBlue = {
  main: '#1976d2',      // Primary blue
  light: '#42a5f5',
  dark: '#1565c0',
  contrastText: '#fff',
}

const kyrosAccent = {
  main: '#ff6f00',      // Accent orange
  light: '#ffa040',
  dark: '#c43e00',
  contrastText: '#fff',
}

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: kyrosBlue,
    secondary: kyrosAccent,
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
    text: {
      primary: 'rgba(0, 0, 0, 0.87)',
      secondary: 'rgba(0, 0, 0, 0.6)',
    },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
    },
    h6: {
      fontSize: '1.25rem',
      fontWeight: 500,
    },
  },
  components: {
    MuiAppBar: {
      defaultProps: {
        elevation: 1,
      },
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          color: 'rgba(0, 0, 0, 0.87)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#fafafa',
          borderRight: '1px solid rgba(0, 0, 0, 0.12)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',  // Disable uppercase transform
          borderRadius: 8,
        },
      },
    },
  },
})
