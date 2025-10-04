'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Bot, Send, Loader2 } from 'lucide-react';

export default function AssistantPage() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([
    {
      role: 'assistant',
      content: 'Hello! I\'m your Digital Spiral AI Assistant. I can help you with analytics, queries, and insights about your Jira data. What would you like to know?',
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;

    const userMessage = query.trim();
    setQuery('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      // TODO: Call AI Assistant API
      // For now, simulate response
      await new Promise((resolve) => setTimeout(resolve, 1000));
      
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `I received your query: "${userMessage}". The AI Assistant API is not yet connected. This is a placeholder response.`,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an error processing your request. Please try again.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">AI Assistant</h1>
        <p className="text-muted-foreground mt-2">
          Ask questions about your Jira data and get AI-powered insights
        </p>
      </div>

      <Card className="h-[calc(100vh-16rem)]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Chat with Assistant
          </CardTitle>
          <CardDescription>
            Ask natural language questions about your Jira projects, sprints, and issues
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col h-[calc(100%-8rem)]">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto space-y-4 mb-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-muted rounded-lg px-4 py-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question... (e.g., 'Show me the most problematic sprints')"
              className="min-h-[60px] resize-none"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />
            <Button type="submit" disabled={!query.trim() || isLoading} size="icon" className="h-[60px] w-[60px]">
              {isLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </Button>
          </form>

          {/* Example Queries */}
          <div className="mt-4 pt-4 border-t">
            <p className="text-xs text-muted-foreground mb-2">Example queries:</p>
            <div className="flex flex-wrap gap-2">
              {[
                'Show me the most problematic sprints',
                'What are the top blockers this month?',
                'Which team members need help?',
                'Analyze sprint velocity trends',
              ].map((example) => (
                <Button
                  key={example}
                  variant="outline"
                  size="sm"
                  onClick={() => setQuery(example)}
                  disabled={isLoading}
                  className="text-xs"
                >
                  {example}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Info Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Natural Language Queries</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              Ask questions in plain English and get SQL-powered insights
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Semantic Search</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              Find similar issues, sprints, and patterns using AI embeddings
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">25+ Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              Access pre-built analytics for velocity, quality, and team health
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

