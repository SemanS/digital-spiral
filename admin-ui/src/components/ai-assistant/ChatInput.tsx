'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface Suggestion {
  id: string;
  label: string;
  value: string;
  type: 'user' | 'issue';
}

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled?: boolean;
  isLoading?: boolean;
  selectedProject?: string;
}

export function ChatInput({ value, onChange, onSend, disabled, isLoading, selectedProject }: ChatInputProps) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [autocompleteType, setAutocompleteType] = useState<'user' | 'issue' | null>(null);
  const [autocompleteQuery, setAutocompleteQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Detect @ or / at cursor position
    const cursorPos = inputRef.current?.selectionStart || 0;
    const textBeforeCursor = value.substring(0, cursorPos);
    const lastAtIndex = textBeforeCursor.lastIndexOf('@');
    const lastSlashIndex = textBeforeCursor.lastIndexOf('/');

    if (lastAtIndex > lastSlashIndex && lastAtIndex >= 0) {
      const query = textBeforeCursor.substring(lastAtIndex + 1);
      if (!query.includes(' ')) {
        setAutocompleteType('user');
        setAutocompleteQuery(query);
        fetchSuggestions('user', query);
        return;
      }
    }

    if (lastSlashIndex > lastAtIndex && lastSlashIndex >= 0) {
      const query = textBeforeCursor.substring(lastSlashIndex + 1);
      if (!query.includes(' ')) {
        setAutocompleteType('issue');
        setAutocompleteQuery(query);
        fetchSuggestions('issue', query);
        return;
      }
    }

    setShowSuggestions(false);
    setAutocompleteType(null);
  }, [value]);

  const fetchSuggestions = async (type: 'user' | 'issue', query: string) => {
    // Allow empty query to show all suggestions
    // if (query.length < 1) {
    //   setSuggestions([]);
    //   setShowSuggestions(false);
    //   return;
    // }

    try {
      const response = await fetch('/api/ai-assistant/autocomplete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type,
          query,
          project_keys: selectedProject && selectedProject !== 'all' ? [selectedProject] : []
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Autocomplete response:', data);

        // Map orchestrator response format to frontend format
        const mappedSuggestions = (data.suggestions || []).map((s: any) => ({
          id: s.id,
          label: s.display || s.label || '',
          value: s.id || s.value || '',
          type: s.type,
        }));

        console.log('Mapped suggestions:', mappedSuggestions);
        setSuggestions(mappedSuggestions);
        setShowSuggestions(mappedSuggestions.length > 0);
        setSelectedIndex(0);
      }
    } catch (error) {
      console.error('Autocomplete error:', error);
    }
  };

  const applySuggestion = (suggestion: Suggestion) => {
    const cursorPos = inputRef.current?.selectionStart || 0;
    const textBeforeCursor = value.substring(0, cursorPos);
    const textAfterCursor = value.substring(cursorPos);

    let newText = '';
    if (autocompleteType === 'user') {
      const lastAtIndex = textBeforeCursor.lastIndexOf('@');
      newText = textBeforeCursor.substring(0, lastAtIndex) + suggestion.value + textAfterCursor;
    } else if (autocompleteType === 'issue') {
      const lastSlashIndex = textBeforeCursor.lastIndexOf('/');
      newText = textBeforeCursor.substring(0, lastSlashIndex) + suggestion.value + textAfterCursor;
    }

    onChange(newText);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (showSuggestions) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % suggestions.length);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + suggestions.length) % suggestions.length);
      } else if (e.key === 'Enter' && suggestions.length > 0) {
        e.preventDefault();
        applySuggestion(suggestions[selectedIndex]);
      } else if (e.key === 'Escape') {
        setShowSuggestions(false);
      }
    } else if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="relative">
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute bottom-full left-0 right-0 mb-2 max-h-60 overflow-y-auto rounded-lg border bg-white shadow-lg">
          {suggestions.map((suggestion, index) => (
            <button
              key={suggestion.id}
              onClick={() => applySuggestion(suggestion)}
              className={`w-full px-4 py-2 text-left text-sm hover:bg-gray-100 ${index === selectedIndex ? 'bg-gray-100' : ''
                }`}
            >
              <div className="font-medium">{suggestion.label}</div>
              <div className="text-xs text-gray-500">{suggestion.value}</div>
            </button>
          ))}
        </div>
      )}
      <div className="flex gap-2">
        <Input
          ref={inputRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message... (use @ for users, / for issues)"
          disabled={disabled}
          className="flex-1"
        />
        <Button onClick={onSend} disabled={disabled || isLoading || !value.trim()}>
          {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </Button>
      </div>
      <p className="mt-2 text-xs text-gray-500">
        Tip: Use <strong>@</strong> for users and <strong>/</strong> for issues (e.g., @john,
        /SCRUM-123)
      </p>
    </div>
  );
}

