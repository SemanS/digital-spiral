import { IssueGlance, Text, useProductContext, render } from '@forge/ui';

const Glance = () => {
  const { platformContext } = useProductContext();
  const issueKey = platformContext?.issueKey as string | undefined;

  return (
    <IssueGlance>
      <Text>Digital Spiral: Suggestions ready{issueKey ? ` for ${issueKey}` : ''}</Text>
    </IssueGlance>
  );
};

export const run = render(<Glance />);
