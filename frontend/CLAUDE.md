# Frontend Development

## Frontend-Specific Commands

```bash
# npm Package Management
npm install package-name              # Add runtime dependency
npm install --save-dev package-name   # Add dev dependency
npm uninstall package-name            # Remove dependency
npm outdated                          # Check for updates
npm update                           # Update packages

# Development & Build Variations
npm run dev -- --port 3001          # Run on different port
npm run dev -- --host 0.0.0.0       # Expose to network
npm run build -- --mode development  # Development build
npm run preview -- --port 4000      # Preview on different port

# Code Quality
npm run lint -- --fix               # Auto-fix ESLint issues
npm run lint -- --quiet             # Show only errors
npx tsc --noEmit                     # Type check without build
```

## React/TypeScript Patterns

**Frontend-Specific Style Rules:**
- **ES modules only** (import/export, not require)
- **Destructure imports**: `import { useState, useEffect } from 'react'`
- **Functional components** with hooks (no classes)
- **TypeScript mandatory** for all new code
- **2-space indentation**
- **Trailing commas** in objects/arrays

### Component Structure Pattern
```typescript
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

interface ComponentProps {
  id: string;
  onUpdate?: (data: any) => void;
  className?: string;
}

const ComponentName: React.FC<ComponentProps> = ({
  id,
  onUpdate,
  className = ''
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) loadData();
  }, [id]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      // API call logic
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return <div className={`component-name ${className}`}>Content</div>;
};

export default ComponentName;
```

## Frontend-Specific State Management

### Zustand Store Pattern
```typescript
// stores/exampleStore.ts
import { create } from 'zustand';

interface ExampleState {
  items: Item[];
  loading: boolean;
  setItems: (items: Item[]) => void;
  addItem: (item: Item) => void;
  clearItems: () => void;
}

export const useExampleStore = create<ExampleState>((set) => ({
  items: [],
  loading: false,
  setItems: (items) => set({ items }),
  addItem: (item) => set((state) => ({
    items: [...state.items, item]
  })),
  clearItems: () => set({ items: [] })
}));
```

### Custom Hook Pattern
```typescript
// hooks/useExample.ts
import { useState, useCallback } from 'react';
import { exampleApi } from '../services/api';

export const useExample = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      return await exampleApi.getData(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { fetchData, loading, error };
};
```

## React Performance Patterns

### Memoization
```typescript
import { memo, useMemo, useCallback } from 'react';

const ExpensiveComponent = memo<{ data: Data[] }>(({ data }) => {
  const processedData = useMemo(() =>
    data.filter(item => item.active).sort((a, b) => a.name.localeCompare(b.name)),
    [data]
  );

  return <div>{/* Render processed data */}</div>;
});

const ParentComponent = () => {
  const [items, setItems] = useState<Item[]>([]);

  const handleClick = useCallback((id: string) => {
    setItems(prev => prev.map(item =>
      item.id === id ? { ...item, selected: !item.selected } : item
    ));
  }, []);

  return <ExpensiveComponent data={items} onClick={handleClick} />;
};
```

### Code Splitting
```typescript
import { lazy, Suspense } from 'react';

const LazyComponent = lazy(() => import('./HeavyComponent'));

function App() {
  return (
    <Suspense fallback={<div>Loading component...</div>}>
      <LazyComponent />
    </Suspense>
  );
}
```

## Vite-Specific Configuration

### Environment Variables
```typescript
// Access Vite env vars
const apiUrl = import.meta.env.VITE_API_URL;
const isDev = import.meta.env.DEV;
const isProd = import.meta.env.PROD;
```

### Build Optimization
```bash
# Analyze bundle
npm run build && npx vite-bundle-analyzer

# Build with custom mode
npm run build -- --mode staging
```
