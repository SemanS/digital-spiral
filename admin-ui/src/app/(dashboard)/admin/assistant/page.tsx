'use client';

import { useState, useRef, useEffect } from 'react';
import { Loader2, AlertCircle, Bot } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ChatMessage } from '@/components/ai-assistant/ChatMessage';
import { ChatInput } from '@/components/ai-assistant/ChatInput';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  toolCalls?: ToolCall[];
}

interface ToolCall {
  name: string;
  args: Record<string, any>;
  result?: any;
}

interface Project {
  key: string;
  name: string;
}

export default function AIAssistantPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedProject, setSelectedProject] = useState<string>('all');
  const [projects, setProjects] = useState<Project[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch projects on mount
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        setLoadingProjects(true);
        const response = await fetch('/api/ai-assistant/projects?tenant_id=insight-bridge');
        const data = await response.json();

        console.log('Fetched projects:', data);

        if (data.projects && Array.isArray(data.projects)) {
          setProjects(data.projects);

          // If no project selected and projects available, select first one
          if (selectedProject === 'all' && data.projects.length > 0) {
            setSelectedProject(data.projects[0].key);
          }
        }
      } catch (error) {
        console.error('Failed to fetch projects:', error);
      } finally {
        setLoadingProjects(false);
      }
    };

    fetchProjects();
  }, []);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/ai-assistant/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: messages.concat(userMessage).map((m) => ({
            role: m.role,
            content: m.content,
          })),
          project_keys: selectedProject && selectedProject !== 'all' ? [selectedProject] : [],
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      const assistantMessage: Message = {
        role: 'assistant',
        content: data.message || data.content || 'No response',
        timestamp: new Date(),
        toolCalls: data.tool_calls || [],
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Chat error:', err);
      setError(err instanceof Error ? err.message : 'Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };



  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col">
      {/* Header */}
      <div className="border-b bg-white p-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">AI Assistant</h1>
            <p className="text-sm text-gray-500">
              Chat with AI to manage your Jira instances
            </p>
          </div>
          <div className="flex items-center gap-4">
            <Select value={selectedProject} onValueChange={setSelectedProject} disabled={loadingProjects}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder={loadingProjects ? "Loading..." : "Select project"} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All projects</SelectItem>
                {projects.map((project) => (
                  <SelectItem key={project.key} value={project.key}>
                    {project.key} - {project.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto bg-gray-50 p-4">
        <div className="mx-auto max-w-4xl space-y-4">
          {messages.length === 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Welcome to AI Assistant!</CardTitle>
                <CardDescription>
                  I can help you manage your Jira instances. Try asking me to:
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="rounded-lg bg-blue-50 p-3 text-sm">
                  <strong>Search:</strong> "Vyhľadaj všetky bugs s vysokou prioritou"
                </div>
                <div className="rounded-lg bg-blue-50 p-3 text-sm">
                  <strong>Comment:</strong> "Pridaj komentár do /SCRUM-229 že pracujem na tom"
                </div>
                <div className="rounded-lg bg-blue-50 p-3 text-sm">
                  <strong>Transition:</strong> "Presuň /SCRUM-230 do In Progress"
                </div>
                <div className="rounded-lg bg-blue-50 p-3 text-sm">
                  <strong>Assign:</strong> "Prirad /SCRUM-231 používateľovi @john"
                </div>
              </CardContent>
            </Card>
          )}

          {messages.map((message, index) => (
            <ChatMessage key={index} message={message} />
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="flex gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-200 text-gray-700">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="rounded-lg bg-white p-4 shadow-sm">
                  <Loader2 className="h-4 w-4 animate-spin" />
                </div>
              </div>
            </div>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t bg-white p-4">
        <div className="mx-auto max-w-4xl">
          <ChatInput
            value={input}
            onChange={setInput}
            onSend={sendMessage}
            disabled={isLoading}
            isLoading={isLoading}
            selectedProject={selectedProject}
          />
        </div>
      </div>
    </div>
  );
}

