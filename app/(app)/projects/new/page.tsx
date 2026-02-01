'use client';

import { useRouter } from 'next/navigation';
import CreateProject from '../../../components/CreateProject/CreateProject';

export default function NewProjectPage() {
  const router = useRouter();

  return (
    <CreateProject
      onCreated={() => {
        router.push('/projects');
      }}
    />
  );
}
