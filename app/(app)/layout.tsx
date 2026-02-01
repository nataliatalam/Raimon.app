import RaimonShell from '../components/RaimonShell';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return <RaimonShell>{children}</RaimonShell>;
}
