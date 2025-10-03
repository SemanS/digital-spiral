import { InstanceFormWizard } from '@/components/instances/InstanceFormWizard';

export default function NewInstancePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Add Jira Instance</h1>
        <p className="text-muted-foreground mt-2">
          Follow the steps below to add a new Jira Cloud instance
        </p>
      </div>
      <InstanceFormWizard />
    </div>
  );
}

