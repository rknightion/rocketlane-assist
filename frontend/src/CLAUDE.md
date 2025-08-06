# Frontend Source - Components & Hooks

## Compound Components
```typescript
const TabsContext = React.createContext<{activeTab: string; setActiveTab: (tab: string) => void} | null>(null);

export const Tabs: React.FC<{children: React.ReactNode; defaultTab: string}> = ({children, defaultTab}) => {
  const [activeTab, setActiveTab] = useState(defaultTab);
  return (
    <TabsContext.Provider value={{activeTab, setActiveTab}}>
      <div className="tabs">{children}</div>
    </TabsContext.Provider>
  );
};

export const Tab: React.FC<{value: string; children: React.ReactNode}> = ({value, children}) => {
  const context = useContext(TabsContext);
  if (!context) throw new Error('Tab must be used within Tabs');
  
  return (
    <button
      className={`tab ${context.activeTab === value ? 'active' : ''}`}
      onClick={() => context.setActiveTab(value)}
    >
      {children}
    </button>
  );
};
```

## API Client Hook
```typescript
export const useApiClient = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const request = useCallback(async <T>(apiCall: () => Promise<T>): Promise<T | null> => {
    try {
      setLoading(true);
      setError(null);
      return await apiCall();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { request, loading, error };
};
```

## Button Composition
```typescript
interface BaseButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
  disabled?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
}

const BaseButton: React.FC<BaseButtonProps> = ({variant = 'primary', disabled, children, onClick}) => (
  <button className={`btn btn-${variant}`} onClick={onClick} disabled={disabled}>
    {children}
  </button>
);

const SaveButton: React.FC<{onSave: () => void; isSaving?: boolean}> = ({onSave, isSaving}) => (
  <BaseButton variant="primary" disabled={isSaving} onClick={onSave}>
    {isSaving ? 'Saving...' : 'Save'}
  </BaseButton>
);
```

## Source Rules
- **Component composition** over inheritance
- **Custom hooks** for reusable logic
- **Context** for compound components
- **Error boundaries** for error handling
- **Virtual scrolling** for large lists (react-window)
