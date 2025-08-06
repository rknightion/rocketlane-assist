# Page Components

## Page Structure Pattern
```typescript
const PageComponent: React.FC = () => {
  const navigate = useNavigate();
  const { selectedUserId } = useConfigStore();
  
  // Redirect if no user selected
  useEffect(() => {
    if (!selectedUserId) {
      navigate('/settings');
    }
  }, [selectedUserId, navigate]);

  return (
    <div className="page">
      <Header />
      <main className="page-content">
        {/* Page content */}
      </main>
    </div>
  );
};
```

## Page Components
- `Home.tsx` - Dashboard with project overview
- `ProjectList.tsx` - Project listing and search
- `ProjectDetail.tsx` - Individual project view  
- `Settings.tsx` - Configuration and user selection
- `Timesheets.tsx` - Time tracking interface

## Page Rules
- **User validation** - redirect to settings if no user selected
- **Loading states** - show loading while fetching data
- **Error handling** - user-friendly error messages
- **Navigation** - use React Router programmatically
- **Page titles** - update document.title for each page