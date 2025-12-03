import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Layout from './components/Layout';
import AnnouncementList from './pages/AnnouncementList';
import AnnouncementDetail from './pages/AnnouncementDetail';
import CompetitorTrends from './pages/CompetitorTrends';
import Settings from './pages/Settings';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<AnnouncementList />} />
            <Route path="/announcements" element={<AnnouncementList />} />
            <Route path="/announcements/:id" element={<AnnouncementDetail />} />
            <Route path="/competitors" element={<CompetitorTrends />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App;


