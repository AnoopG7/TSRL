import { Toaster } from 'sonner';
import { useThemeStore } from '../../store/useThemeStore';

export function ThemedToaster() {
  const theme = useThemeStore((s) => s.theme);
  return <Toaster position="bottom-right" theme={theme} richColors closeButton />;
}
