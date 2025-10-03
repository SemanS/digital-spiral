import { NextRequest, NextResponse } from 'next/server';

const ORCHESTRATOR_URL = process.env.NEXT_PUBLIC_ORCHESTRATOR_URL || 'http://localhost:7010';

export async function GET(request: NextRequest) {
  try {
    // Get tenant_id from query params or use default
    const searchParams = request.nextUrl.searchParams;
    const tenantId = searchParams.get('tenant_id') || 'insight-bridge';

    console.log('Fetching projects for tenant:', tenantId);

    // Call orchestrator projects endpoint
    const response = await fetch(`${ORCHESTRATOR_URL}/v1/pulse/projects?tenant_id=${tenantId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Orchestrator projects error:', response.status, errorText);
      throw new Error(`Orchestrator returned ${response.status}: ${errorText}`);
    }

    const data = await response.json();
    console.log('Projects response:', data);

    return NextResponse.json(data);
  } catch (error) {
    console.error('Projects API error:', error);
    return NextResponse.json(
      { 
        error: error instanceof Error ? error.message : 'Failed to fetch projects',
        projects: []
      },
      { status: 500 }
    );
  }
}

