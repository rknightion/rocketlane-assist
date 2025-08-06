# UI Components

## Component Standards
- **Functional components** with hooks only
- **TypeScript interfaces** for all props
- **Error boundaries** for data components
- **Loading states** for async operations

## Reusable Components Pattern
```typescript
interface ComponentProps {
  id: string;
  onAction?: (data: any) => void;
  className?: string;
}

const Component: React.FC<ComponentProps> = ({ id, onAction, className = '' }) => {
  const [state, setState] = useState(initialState);
  
  return <div className={`component ${className}`}>Content</div>;
};
```

## Project-Specific Components
- **OnboardingWizard** - multi-step user setup
- Planned: ProjectCard, TaskList, SummaryWidget, SettingsPanel

## Component Rules  
- **User context aware** - check `selectedUserId` before data operations
- **Consistent styling** - use shared CSS classes
- **Accessibility** - ARIA labels and keyboard navigation
- **Error handling** - graceful degradation for API failures
- **Loading states** - skeleton screens for better UX