# Source Code Components

## Component-Specific Development

### Compound Component Pattern
```typescript
// For complex UI components with multiple parts
interface TabsContextValue {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const TabsContext = React.createContext<TabsContextValue | null>(null);

export const Tabs: React.FC<{ children: React.ReactNode; defaultTab: string }> = ({
  children,
  defaultTab
}) => {
  const [activeTab, setActiveTab] = useState(defaultTab);

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className="tabs">{children}</div>
    </TabsContext.Provider>
  );
};

export const TabList: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="tab-list" role="tablist">{children}</div>
);

export const Tab: React.FC<{ value: string; children: React.ReactNode }> = ({
  value,
  children
}) => {
  const context = useContext(TabsContext);
  if (!context) throw new Error('Tab must be used within Tabs');

  return (
    <button
      className={`tab ${context.activeTab === value ? 'active' : ''}`}
      onClick={() => context.setActiveTab(value)}
      role="tab"
    >
      {children}
    </button>
  );
};

// Usage: <Tabs><TabList><Tab value="overview">Overview</Tab></TabList></Tabs>
```

### Form Component Patterns
```typescript
// Controlled form component with validation
interface FormField {
  name: string;
  value: string;
  error?: string;
  touched: boolean;
}

const useFormValidation = <T extends Record<string, any>>(
  initialValues: T,
  validationSchema: Record<keyof T, (value: any) => string | undefined>
) => {
  const [fields, setFields] = useState<Record<keyof T, FormField>>(
    Object.keys(initialValues).reduce((acc, key) => {
      acc[key as keyof T] = {
        name: key,
        value: initialValues[key],
        touched: false
      };
      return acc;
    }, {} as Record<keyof T, FormField>)
  );

  const updateField = (name: keyof T, value: any) => {
    setFields(prev => ({
      ...prev,
      [name]: {
        ...prev[name],
        value,
        error: validationSchema[name]?.(value),
        touched: true
      }
    }));
  };

  return { fields, updateField };
};
```

### API Client Hooks Pattern
```typescript
// hooks/useApiClient.ts - Centralized API interaction
export const useApiClient = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const request = useCallback(async <T>(
    apiCall: () => Promise<T>
  ): Promise<T | null> => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiCall();
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Request failed';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { request, loading, error, clearError: () => setError(null) };
};

// Usage in components
const ProjectDetail = ({ projectId }: { projectId: string }) => {
  const { request, loading, error } = useApiClient();
  const [project, setProject] = useState<Project | null>(null);

  useEffect(() => {
    const loadProject = async () => {
      const result = await request(() => projectApi.getProject(projectId));
      if (result) setProject(result);
    };
    loadProject();
  }, [projectId, request]);

  return (
    <div>
      {loading && <Spinner />}
      {error && <ErrorMessage message={error} />}
      {project && <ProjectInfo project={project} />}
    </div>
  );
};
```

## Source-Level Optimizations

### Component Composition for Reusability
```typescript
// Base components for consistent styling
interface BaseButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
}

const BaseButton: React.FC<BaseButtonProps> = ({
  variant = 'primary',
  size = 'md',
  disabled,
  children,
  onClick
}) => (
  <button
    className={`btn btn-${variant} btn-${size} ${disabled ? 'disabled' : ''}`}
    onClick={onClick}
    disabled={disabled}
  >
    {children}
  </button>
);

// Specialized buttons
const SaveButton: React.FC<{ onSave: () => void; isSaving?: boolean }> = ({
  onSave,
  isSaving
}) => (
  <BaseButton variant="primary" disabled={isSaving} onClick={onSave}>
    {isSaving ? 'Saving...' : 'Save'}
  </BaseButton>
);

const DeleteButton: React.FC<{ onDelete: () => void; confirmRequired?: boolean }> = ({
  onDelete,
  confirmRequired = true
}) => {
  const handleClick = () => {
    if (confirmRequired && !confirm('Are you sure?')) return;
    onDelete();
  };

  return (
    <BaseButton variant="danger" onClick={handleClick}>
      Delete
    </BaseButton>
  );
};
```

### Virtual Scrolling for Large Lists
```typescript
// utils/virtualScrolling.ts
import { FixedSizeList as List } from 'react-window';

interface VirtualListProps<T> {
  items: T[];
  height: number;
  itemHeight: number;
  renderItem: ({ index, style }: { index: number; style: React.CSSProperties }) => React.ReactElement;
}

export const VirtualList = <T,>({
  items,
  height,
  itemHeight,
  renderItem
}: VirtualListProps<T>) => (
  <List
    height={height}
    itemCount={items.length}
    itemSize={itemHeight}
    width="100%"
  >
    {renderItem}
  </List>
);

// Usage in components
const ProjectList = () => {
  const { projects } = useProjects();

  const renderProject = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div style={style}>
      <ProjectCard project={projects[index]} />
    </div>
  );

  return (
    <VirtualList
      items={projects}
      height={600}
      itemHeight={120}
      renderItem={renderProject}
    />
  );
};
```
