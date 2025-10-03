export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public code?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class NetworkError extends Error {
  constructor(message: string = 'Network error occurred') {
    super(message);
    this.name = 'NetworkError';
  }
}

export class ValidationError extends Error {
  constructor(
    message: string,
    public errors?: Record<string, string[]>
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

export function handleApiError(error: unknown): never {
  if (error instanceof ApiError) {
    throw error;
  }

  if (error instanceof NetworkError) {
    throw error;
  }

  if (error instanceof ValidationError) {
    throw error;
  }

  // Handle axios errors
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const axiosError = error as {
      response?: { status: number; data?: { message?: string; errors?: Record<string, string[]> } };
      message: string;
    };

    if (axiosError.response) {
      const { status, data } = axiosError.response;

      if (status === 422 && data?.errors) {
        throw new ValidationError(data.message || 'Validation failed', data.errors);
      }

      throw new ApiError(
        data?.message || `Request failed with status ${status}`,
        status
      );
    }

    throw new NetworkError(axiosError.message);
  }

  // Unknown error
  throw new ApiError('An unexpected error occurred');
}

