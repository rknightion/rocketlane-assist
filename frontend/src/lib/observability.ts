import { 
  getWebInstrumentations, 
  initializeFaro,
  LogLevel,
  SessionInstrumentation,
  ConsoleInstrumentation,
  WebVitalsInstrumentation,
  ErrorsInstrumentation,
  ViewInstrumentation
} from '@grafana/faro-web-sdk';
import { TracingInstrumentation } from '@grafana/faro-web-tracing';

let faroInstance: ReturnType<typeof initializeFaro> | null = null;

export function initializeObservability() {
  if (faroInstance) {
    return faroInstance;
  }

  try {
    faroInstance = initializeFaro({
      url: 'https://faro-collector-prod-gb-south-1.grafana.net/collect/292365ab3438466b8e96120631d3f05f',
      app: {
        name: 'rocketlane-assistant',
        version: '1.0.0',
        environment: import.meta.env.PROD ? 'production' : 'development'
      },
      instrumentations: [
        // Core error tracking
        new ErrorsInstrumentation(),
        
        // Web performance metrics
        new WebVitalsInstrumentation(),
        
        // Console logging with filtered levels
        new ConsoleInstrumentation({
          disabledLevels: [LogLevel.DEBUG, LogLevel.TRACE] // Only capture info, warn, error in production
        }),
        
        // Session tracking for user journey analysis
        new SessionInstrumentation(),
        
        // View tracking for page navigation
        new ViewInstrumentation(),
        
        // Distributed tracing with backend correlation
        new TracingInstrumentation({
          instrumentationOptions: {
            // Enable trace context propagation to backend
            propagateTraceHeaderCorsUrls: [
              new RegExp('http://localhost:8000.*'),
              new RegExp('https://.*\\.rocketlane\\.com.*')
            ]
          }
        })
      ],
      
      // Enhanced error filtering
      beforeSend: (item) => {
        // Filter out sensitive data from errors and logs
        if (item.type === 'exception' || item.type === 'log') {
          const payload = item.payload as any;
          
          // Redact potential API keys or tokens
          if (payload.value && typeof payload.value === 'string') {
            payload.value = payload.value
              .replace(/sk-[a-zA-Z0-9]{40,}/g, 'sk-***')
              .replace(/Bearer [a-zA-Z0-9\-._~+\/]+=*/g, 'Bearer ***')
              .replace(/api[_-]?key["\s]*[:=]["\s]*["']?[a-zA-Z0-9\-._~+\/]+["']?/gi, 'api_key=***');
          }
          
          // Redact sensitive context data
          if (payload.context) {
            const sensitiveKeys = ['password', 'token', 'secret', 'apiKey', 'api_key'];
            Object.keys(payload.context).forEach(key => {
              if (sensitiveKeys.some(sensitive => key.toLowerCase().includes(sensitive))) {
                payload.context[key] = '***';
              }
            });
          }
        }
        
        return item;
      },
      
      // Ignore common non-critical errors
      ignoreErrors: [
        'ResizeObserver loop limit exceeded',
        'ResizeObserver loop completed with undelivered notifications',
        'Non-Error promise rejection captured'
      ],
      
      // Add initial session context
      session: {
        id: crypto.randomUUID(),
        attributes: {
          userAgent: navigator.userAgent,
          language: navigator.language,
          screenResolution: `${window.screen.width}x${window.screen.height}`
        }
      }
    });

    console.log('Grafana Faro initialized successfully');
  } catch (error) {
    console.error('Failed to initialize Grafana Faro:', error);
  }

  return faroInstance;
}

// Export utility functions for manual instrumentation
export function trackEvent(name: string, attributes?: Record<string, any>) {
  faroInstance?.api.pushEvent(name, attributes);
}

export function setUser(userId: string, email?: string, username?: string) {
  faroInstance?.api.setUser({
    id: userId,
    email,
    username
  });
}

export function clearUser() {
  faroInstance?.api.resetUser();
}

export function logError(error: Error, context?: Record<string, any>) {
  faroInstance?.api.pushError(error, { context });
}

export function measurePerformance(name: string, value: number, attributes?: Record<string, any>) {
  faroInstance?.api.pushMeasurement({
    type: 'custom',
    values: { [name]: value },
    ...(attributes && { context: attributes })
  });
}