import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Button,
} from '@mui/material';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { label: '공고 목록', path: '/' },
  ];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Box
            component="img"
            src="/logo.png"
            alt="인턴 로니"
            sx={{
              height: 40,
              width: 'auto',
              mr: 2,
              objectFit: 'contain',
            }}
          />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            인턴 로니
          </Typography>
          {menuItems.map((item) => (
            <Button
              key={item.path}
              color="inherit"
              onClick={() => navigate(item.path)}
              sx={{
                mx: 1,
                backgroundColor:
                  location.pathname === item.path
                    ? 'rgba(255, 255, 255, 0.1)'
                    : 'transparent',
              }}
            >
              {item.label}
            </Button>
          ))}
        </Toolbar>
      </AppBar>
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4, flex: 1 }}>
        {children}
      </Container>
    </Box>
  );
};

export default Layout;


