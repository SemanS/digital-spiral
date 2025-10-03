# Admin UI - Digital Spiral

Admin UI for managing Digital Spiral source instances, users, and configuration.

---

## 📚 Overview

The Admin UI provides a web interface for:
- Managing source instances (Jira, GitHub, Asana, Linear, ClickUp)
- Testing connections
- Viewing sync status
- Managing users and permissions
- Monitoring system health

---

## 🏗️ Architecture

### Technology Stack

**Frontend:**
- React 18+ with TypeScript
- Tailwind CSS for styling
- React Query for data fetching
- React Router for navigation
- Zustand for state management

**Backend:**
- FastAPI endpoints (already implemented in `src/interfaces/api/admin/`)
- JWT authentication
- RESTful API

---

## 📁 Structure

```
src/interfaces/admin_ui/
├── README.md                    # This file
├── package.json                 # Dependencies
├── tsconfig.json               # TypeScript config
├── tailwind.config.js          # Tailwind config
├── vite.config.ts              # Vite config
├── public/                     # Static assets
├── src/
│   ├── main.tsx                # Entry point
│   ├── App.tsx                 # Main app component
│   ├── components/             # Reusable components
│   │   ├── Layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Footer.tsx
│   │   ├── SourceInstances/
│   │   │   ├── InstanceList.tsx
│   │   │   ├── InstanceForm.tsx
│   │   │   ├── InstanceCard.tsx
│   │   │   └── ConnectionTest.tsx
│   │   ├── Auth/
│   │   │   ├── LoginForm.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   └── Common/
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       ├── Modal.tsx
│   │       └── LoadingSpinner.tsx
│   ├── pages/                  # Page components
│   │   ├── Dashboard.tsx
│   │   ├── SourceInstances.tsx
│   │   ├── Users.tsx
│   │   ├── Settings.tsx
│   │   └── Login.tsx
│   ├── api/                    # API client
│   │   ├── client.ts
│   │   ├── instances.ts
│   │   └── auth.ts
│   ├── hooks/                  # Custom hooks
│   │   ├── useAuth.ts
│   │   ├── useInstances.ts
│   │   └── useToast.ts
│   ├── store/                  # State management
│   │   └── authStore.ts
│   ├── types/                  # TypeScript types
│   │   ├── instance.ts
│   │   └── user.ts
│   └── utils/                  # Utilities
│       ├── api.ts
│       └── formatters.ts
└── tests/                      # Tests
    └── components/
```

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
cd src/interfaces/admin_ui
npm install
```

### Development

```bash
npm run dev
```

Runs on http://localhost:5173

### Build

```bash
npm run build
```

Builds to `dist/` directory

### Test

```bash
npm run test
```

---

## 📱 Features

### 1. Dashboard

- System health overview
- Active instances count
- Recent sync status
- Quick actions

### 2. Source Instances

**List View:**
- All configured instances
- Status indicators (active/inactive)
- Connection status
- Last sync time
- Quick actions (edit, delete, test)

**Create/Edit Form:**
- Source type selection (Jira, GitHub, Asana, Linear, ClickUp)
- Instance name
- Base URL
- Authentication configuration
- Test connection button

**Connection Test:**
- Real-time connection testing
- Success/failure feedback
- Error details

### 3. Users (Future)

- User list
- Role management
- Permissions

### 4. Settings (Future)

- System configuration
- API keys
- Notification settings

---

## 🎨 UI Components

### InstanceCard

```tsx
<InstanceCard
  instance={instance}
  onEdit={() => handleEdit(instance.id)}
  onDelete={() => handleDelete(instance.id)}
  onTest={() => handleTest(instance.id)}
/>
```

### InstanceForm

```tsx
<InstanceForm
  instance={instance}
  onSubmit={handleSubmit}
  onCancel={handleCancel}
/>
```

### ConnectionTest

```tsx
<ConnectionTest
  instanceId={instance.id}
  onSuccess={() => showToast('Connection successful')}
  onError={(error) => showToast(error, 'error')}
/>
```

---

## 🔌 API Integration

### API Client

```typescript
// src/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default apiClient;
```

### Instances API

```typescript
// src/api/instances.ts
import apiClient from './client';
import { SourceInstance } from '../types/instance';

export const instancesApi = {
  list: () => apiClient.get<SourceInstance[]>('/admin/source-instances'),
  
  get: (id: string) => apiClient.get<SourceInstance>(`/admin/source-instances/${id}`),
  
  create: (data: CreateInstanceData) => 
    apiClient.post<SourceInstance>('/admin/source-instances', data),
  
  update: (id: string, data: UpdateInstanceData) =>
    apiClient.patch<SourceInstance>(`/admin/source-instances/${id}`, data),
  
  delete: (id: string) =>
    apiClient.delete(`/admin/source-instances/${id}`),
  
  testConnection: (id: string) =>
    apiClient.post(`/admin/source-instances/${id}/test-connection`),
};
```

---

## 🎯 State Management

### Auth Store (Zustand)

```typescript
// src/store/authStore.ts
import create from 'zustand';

interface AuthState {
  token: string | null;
  user: User | null;
  login: (token: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('token'),
  user: null,
  
  login: (token, user) => {
    localStorage.setItem('token', token);
    set({ token, user });
  },
  
  logout: () => {
    localStorage.removeItem('token');
    set({ token: null, user: null });
  },
}));
```

---

## 🔒 Authentication

### Protected Routes

```typescript
// src/components/Auth/ProtectedRoute.tsx
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

export const ProtectedRoute = ({ children }) => {
  const token = useAuthStore((state) => state.token);
  
  if (!token) {
    return <Navigate to="/login" />;
  }
  
  return children;
};
```

### Usage

```typescript
<Route
  path="/instances"
  element={
    <ProtectedRoute>
      <SourceInstances />
    </ProtectedRoute>
  }
/>
```

---

## 📊 Data Fetching

### React Query

```typescript
// src/hooks/useInstances.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { instancesApi } from '../api/instances';

export const useInstances = () => {
  return useQuery({
    queryKey: ['instances'],
    queryFn: () => instancesApi.list(),
  });
};

export const useCreateInstance = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: instancesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instances'] });
    },
  });
};
```

---

## 🎨 Styling

### Tailwind CSS

```tsx
<div className="bg-white rounded-lg shadow-md p-6">
  <h2 className="text-2xl font-bold mb-4">Source Instances</h2>
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {instances.map((instance) => (
      <InstanceCard key={instance.id} instance={instance} />
    ))}
  </div>
</div>
```

---

## 🧪 Testing

### Component Tests

```typescript
// tests/components/InstanceCard.test.tsx
import { render, screen } from '@testing-library/react';
import { InstanceCard } from '../../src/components/SourceInstances/InstanceCard';

describe('InstanceCard', () => {
  it('renders instance name', () => {
    const instance = {
      id: '123',
      name: 'Test Instance',
      source_type: 'jira',
      is_active: true,
    };
    
    render(<InstanceCard instance={instance} />);
    expect(screen.getByText('Test Instance')).toBeInTheDocument();
  });
});
```

---

## 📝 Environment Variables

```env
# .env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=Digital Spiral Admin
```

---

## 🚀 Deployment

### Build for Production

```bash
npm run build
```

### Serve with Nginx

```nginx
server {
    listen 80;
    server_name admin.digital-spiral.com;
    
    root /var/www/admin-ui/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

---

## 📚 Resources

- [React Documentation](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [React Query](https://tanstack.com/query/latest)
- [Zustand](https://github.com/pmndrs/zustand)

---

**Status:** 📝 Specification Complete  
**Implementation:** ⏳ To Be Implemented  
**Last Updated:** 2025-10-03

