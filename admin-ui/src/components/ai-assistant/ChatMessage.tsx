'use client';

import { Bot, User } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface ToolCall {
  name: string;
  args: Record<string, any>;
  result?: any;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  toolCalls?: ToolCall[];
}

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  return (
    <div
      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`flex max-w-[80%] gap-3 ${
          message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
        }`}
      >
        <div
          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
            message.role === 'user'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 text-gray-700'
          }`}
        >
          {message.role === 'user' ? (
            <User className="h-4 w-4" />
          ) : (
            <Bot className="h-4 w-4" />
          )}
        </div>
        <div className="space-y-2">
          <div
            className={`rounded-lg p-4 ${
              message.role === 'user'
                ? 'bg-blue-500 text-white'
                : 'bg-white text-gray-900 shadow-sm'
            }`}
          >
            <p className="whitespace-pre-wrap text-sm">{message.content}</p>
          </div>
          {message.toolCalls && message.toolCalls.length > 0 && (
            <div className="space-y-2">
              {message.toolCalls.map((tool, toolIndex) => (
                <div
                  key={toolIndex}
                  className="rounded-lg border bg-gray-50 p-3 text-xs"
                >
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{tool.name}</Badge>
                    <span className="text-gray-500">
                      {JSON.stringify(tool.args)}
                    </span>
                  </div>
                  {tool.result && (
                    <pre className="mt-2 overflow-x-auto text-xs text-gray-600">
                      {JSON.stringify(tool.result, null, 2)}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          )}
          <p className="text-xs text-gray-400">
            {message.timestamp.toLocaleTimeString()}
          </p>
        </div>
      </div>
    </div>
  );
}

