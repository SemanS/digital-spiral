'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { InstanceDetailsStep } from './wizard/InstanceDetailsStep';
import { InstanceAuthStep } from './wizard/InstanceAuthStep';
import { InstanceValidateStep } from './wizard/InstanceValidateStep';
import { InstanceSaveStep } from './wizard/InstanceSaveStep';
import type { CreateInstanceFormData } from '@/lib/schemas/instance';

const steps = [
  { id: 1, name: 'Details', description: 'Basic information' },
  { id: 2, name: 'Authentication', description: 'Credentials' },
  { id: 3, name: 'Validate', description: 'Test connection' },
  { id: 4, name: 'Save', description: 'Review and save' },
];

interface WizardData {
  name: string;
  baseUrl: string;
  projectFilter?: string;
  authMethod: 'api_token' | 'oauth';
  email: string;
  apiToken: string;
}

export function InstanceFormWizard() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [wizardData, setWizardData] = useState<Partial<WizardData>>({
    authMethod: 'api_token',
  });
  const [isTestSuccessful, setIsTestSuccessful] = useState(false);

  // Load from session storage on mount
  useEffect(() => {
    const saved = sessionStorage.getItem('instanceWizardData');
    if (saved) {
      try {
        setWizardData(JSON.parse(saved));
      } catch (error) {
        console.error('Failed to parse saved wizard data:', error);
      }
    }
  }, []);

  // Save to session storage on data change
  useEffect(() => {
    sessionStorage.setItem('instanceWizardData', JSON.stringify(wizardData));
  }, [wizardData]);

  const handleNext = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleCancel = () => {
    if (confirm('Are you sure you want to cancel? All progress will be lost.')) {
      sessionStorage.removeItem('instanceWizardData');
      router.push('/admin/instances');
    }
  };

  const handleComplete = () => {
    sessionStorage.removeItem('instanceWizardData');
    router.push('/admin/instances');
  };

  const updateWizardData = (data: Partial<WizardData>) => {
    setWizardData((prev) => ({ ...prev, ...data }));
  };

  const progress = (currentStep / steps.length) * 100;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Step Indicator */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-center flex-1">
              <div className="flex flex-col items-center flex-1">
                <div
                  className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors',
                    currentStep > step.id
                      ? 'bg-primary border-primary text-primary-foreground'
                      : currentStep === step.id
                      ? 'border-primary text-primary'
                      : 'border-muted text-muted-foreground'
                  )}
                >
                  {currentStep > step.id ? (
                    <Check className="h-5 w-5" />
                  ) : (
                    <span>{step.id}</span>
                  )}
                </div>
                <div className="mt-2 text-center">
                  <p
                    className={cn(
                      'text-sm font-medium',
                      currentStep >= step.id ? 'text-foreground' : 'text-muted-foreground'
                    )}
                  >
                    {step.name}
                  </p>
                  <p className="text-xs text-muted-foreground hidden sm:block">
                    {step.description}
                  </p>
                </div>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={cn(
                    'h-0.5 flex-1 mx-2 transition-colors',
                    currentStep > step.id ? 'bg-primary' : 'bg-muted'
                  )}
                />
              )}
            </div>
          ))}
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      {/* Step Content */}
      <Card>
        <CardHeader>
          <CardTitle>{steps[currentStep - 1].name}</CardTitle>
          <CardDescription>{steps[currentStep - 1].description}</CardDescription>
        </CardHeader>
        <CardContent>
          {currentStep === 1 && (
            <InstanceDetailsStep
              data={wizardData}
              onNext={(data) => {
                updateWizardData(data);
                handleNext();
              }}
            />
          )}
          {currentStep === 2 && (
            <InstanceAuthStep
              data={wizardData}
              onNext={(data) => {
                updateWizardData(data);
                handleNext();
              }}
              onBack={handleBack}
            />
          )}
          {currentStep === 3 && (
            <InstanceValidateStep
              data={wizardData as WizardData}
              onNext={() => {
                setIsTestSuccessful(true);
                handleNext();
              }}
              onBack={handleBack}
              onTestSuccess={() => setIsTestSuccessful(true)}
            />
          )}
          {currentStep === 4 && (
            <InstanceSaveStep
              data={wizardData as CreateInstanceFormData}
              onComplete={handleComplete}
              onBack={handleBack}
            />
          )}
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={handleCancel}>
          Cancel
        </Button>
        <div className="text-sm text-muted-foreground">
          Step {currentStep} of {steps.length}
        </div>
      </div>
    </div>
  );
}

