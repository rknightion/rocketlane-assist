# Frontend - React TypeScript

## Package Management
```bash
npm install package-name              # Add dependency
npm install --save-dev package-name   # Add dev dependency  
npm outdated && npm update            # Check & update
```

## Development  
```bash
npm run dev -- --port 3001           # Alt port
npm run dev -- --host 0.0.0.0        # Network access
npm run lint -- --fix                # Fix & lint
npx tsc --noEmit                      # Type check only
```

## Style Rules
- **ES modules only** (import/export)
- **Destructure imports**: `import { useState } from 'react'`  
- **Functional components** with hooks
- **TypeScript mandatory**, 2-space indent

## Component Pattern
```typescript
interface Props {
  id: string;
  onUpdate?: (data: any) => void;
}

const Component: React.FC<Props> = ({ id, onUpdate }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      // API call
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  return <div>Content</div>;
};
```

## State Management (Zustand)
```typescript
import { create } from 'zustand';

interface Store {
  items: Item[];
  setItems: (items: Item[]) => void;
  addItem: (item: Item) => void;
}

export const useStore = create<Store>((set) => ({
  items: [],
  setItems: (items) => set({ items }),
  addItem: (item) => set((state) => ({ items: [...state.items, item] }))
}));
```

## Performance
- Use `memo`, `useMemo`, `useCallback` for expensive operations
- Lazy load: `const Component = lazy(() => import('./Component'))`
- Vite env: `import.meta.env.VITE_API_URL`

## Project-Specific Rules  
- **All API calls** through `services/api.ts`
- **User context required** - check `configStore.selectedUserId`
- **Error handling** - use consistent error states
- **Navigation** - use React Router programmatic navigation
