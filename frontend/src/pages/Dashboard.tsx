import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
} from '@mui/material';
import {
  Announcement,
  CheckCircle,
  Pending,
  Block,
} from '@mui/icons-material';
import { useStats } from '../hooks/useStats';
import LoadingSpinner from '../components/LoadingSpinner';

const Dashboard: React.FC = () => {
  const { stats, loading } = useStats();

  const statCards = [
    {
      title: '전체 공고',
      value: stats.total,
      icon: <Announcement sx={{ fontSize: 40 }} />,
      color: '#1976d2',
    },
    {
      title: '승인됨',
      value: stats.approved,
      icon: <CheckCircle sx={{ fontSize: 40 }} />,
      color: '#2e7d32',
    },
    {
      title: '대기 중',
      value: stats.pending,
      icon: <Pending sx={{ fontSize: 40 }} />,
      color: '#ed6c02',
    },
    {
      title: '거부됨',
      value: stats.rejected,
      icon: <Block sx={{ fontSize: 40 }} />,
      color: '#d32f2f',
    },
  ];

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        대시보드
      </Typography>
      <Grid container spacing={3} sx={{ mt: 2 }}>
        {statCards.map((card, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      {card.title}
                    </Typography>
                    <Typography variant="h4" component="div" sx={{ color: card.color }}>
                      {card.value}
                    </Typography>
                  </Box>
                  <Box sx={{ color: card.color }}>{card.icon}</Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default Dashboard;

