import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Sparkles, 
  RefreshCw, 
  HelpCircle, 
  ChevronDown, 
  ChevronUp, 
  Check, 
  Copy,
  TrendingUp,
  Target,
  Scale
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface CampaignChatProps {
  runId: string | null;
  className?: string;
}

const SUGGESTED_PROMPTS = [
  {
    icon: <TrendingUp className="w-3.5 h-3.5 text-orange-500" />,
    text: "What was our true causal impact & uplift?"
  },
  {
    icon: <Scale className="w-3.5 h-3.5 text-blue-500" />,
    text: "Why is AIPW different from the naive difference?"
  },
  {
    icon: <Target className="w-3.5 h-3.5 text-green-500" />,
    text: "Which demographic segments performed best?"
  },
  {
    icon: <Sparkles className="w-3.5 h-3.5 text-purple-500" />,
    text: "Give me 3 strategic recommendations for our next campaign."
  }
];

export const CampaignChat: React.FC<CampaignChatProps> = ({ runId, className = '' }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: runId
        ? "Hello! I'm your CampaignIQ AI Analyst. I have reviewed your causal inference results. Ask me anything about your campaign's uplift, confounding variables, target segments, or next-step recommendations!"
        : "Hello! I'm your CampaignIQ AI Analyst. You can ask me questions about causal inference, campaign ROI, or upload a dataset above to analyze your campaign's true impact!",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [isMinimized, setIsMinimized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    if (runId) {
      setMessages(prev => [
        ...prev,
        {
          id: 'grounded-' + runId,
          role: 'assistant',
          content: `🎯 **Analysis results loaded!** I am now grounded in your specific run data (\`Run #${runId.slice(0, 8)}\`). You can ask me to explain your ATE, confidence intervals, top demographic segments, or balance diagnostics.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    }
  }, [runId]);

  const handleSend = async (textToSend?: string) => {
    const question = (textToSend || input).trim();
    if (!question || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: question,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMessage]);
    if (!textToSend) setInput('');
    setIsLoading(true);

    try {
      const history = messages
        .filter(m => m.id !== 'welcome' && !m.id.startsWith('grounded-'))
        .map(m => ({ role: m.role, content: m.content }));

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          runId: runId || null,
          message: question,
          history
        })
      });

      const data = await response.json();
      if (!response.ok || data.status === 'error') {
        throw new Error(data.message || 'Failed to get answer');
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `⚠️ Sorry, I encountered an issue retrieving the answer: ${err.message}. Please verify the backend is running.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleClear = () => {
    setMessages([
      {
        id: 'welcome-reset',
        role: 'assistant',
        content: runId
          ? `Conversation cleared. I am grounded in \`Run #${runId.slice(0, 8)}\`. What would you like to explore?`
          : "Conversation cleared. How can I assist you with your campaign analysis?",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
  };

  return (
    <Card className={`border border-border/60 shadow-xl overflow-hidden bg-card/95 backdrop-blur-sm transition-all duration-300 ${className}`}>
      <CardHeader className="px-6 py-4 border-b border-border/40 bg-muted/30 flex flex-row items-center justify-between space-y-0">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-red-500 to-orange-500 text-white shadow-md shadow-red-500/20">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-base font-semibold">CampaignIQ AI Analyst</CardTitle>
              {runId ? (
                <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20 text-xs font-normal gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                  Grounded: #{runId.slice(0, 6)}
                </Badge>
              ) : (
                <Badge variant="outline" className="text-xs font-normal text-muted-foreground">
                  General Q&A
                </Badge>
              )}
            </div>
            <CardDescription className="text-xs mt-0.5">
              Interactive Q&A powered by causal inference data and AI
            </CardDescription>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
            onClick={handleClear}
            title="Clear conversation"
          >
            <RefreshCw className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
            onClick={() => setIsMinimized(!isMinimized)}
            title={isMinimized ? "Expand chat" : "Minimize chat"}
          >
            {isMinimized ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </Button>
        </div>
      </CardHeader>

      {!isMinimized && (
        <CardContent className="p-0 flex flex-col h-[520px]">
          <div className="flex-1 overflow-y-auto p-6 space-y-5">
            {messages.map((m) => {
              const isUser = m.role === 'user';
              return (
                <div
                  key={m.id}
                  className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-medium shadow-sm ${
                      isUser
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-gradient-to-tr from-red-500/20 to-orange-500/20 text-red-600 border border-red-500/20'
                    }`}
                  >
                    {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>

                  <div className={`group relative max-w-[82%] space-y-1.5 ${isUser ? 'items-end' : 'items-start'}`}>
                    <div
                      className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                        isUser
                          ? 'bg-primary text-primary-foreground rounded-tr-none shadow-sm'
                          : 'bg-muted/70 text-foreground border border-border/50 rounded-tl-none'
                      }`}
                    >
                      {m.content}
                    </div>
                    
                    <div className={`flex items-center gap-2 px-1 text-[11px] text-muted-foreground/70 ${isUser ? 'justify-end' : 'justify-start'}`}>
                      <span>{m.timestamp}</span>
                      {!isUser && (
                        <button
                          onClick={() => handleCopy(m.id, m.content)}
                          className="opacity-0 group-hover:opacity-100 transition-opacity hover:text-foreground cursor-pointer"
                          title="Copy response"
                        >
                          {copiedId === m.id ? <Check className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3" />}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}

            {isLoading && (
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-red-500/20 to-orange-500/20 text-red-600 border border-red-500/20 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="px-4 py-3 rounded-2xl bg-muted/70 border border-border/50 rounded-tl-none flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">Consulting causal models & drafting answer</span>
                  <span className="flex gap-1 items-center ml-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-delay:-0.3s]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-delay:-0.15s]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" />
                  </span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <div className="px-6 py-2.5 border-t border-border/30 bg-muted/10 overflow-x-auto no-scrollbar flex items-center gap-2">
            <span className="text-[11px] font-medium text-muted-foreground flex items-center gap-1 flex-shrink-0">
              <HelpCircle className="w-3 h-3" /> Suggested:
            </span>
            {SUGGESTED_PROMPTS.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(prompt.text)}
                disabled={isLoading}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs bg-background border border-border/60 hover:border-primary/50 hover:bg-muted/40 transition-all flex-shrink-0 text-foreground disabled:opacity-50 disabled:cursor-not-allowed shadow-xs"
              >
                {prompt.icon}
                <span>{prompt.text}</span>
              </button>
            ))}
          </div>

          <div className="p-4 border-t border-border/40 bg-muted/20 flex items-center gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask any question about your campaign results, segments, or methodology..."
              disabled={isLoading}
              className="h-11 rounded-xl bg-background border-border/60 focus-visible:ring-primary"
            />
            <Button
              onClick={() => handleSend()}
              disabled={!input.trim() || isLoading}
              className="h-11 px-5 rounded-xl gap-2 bg-gradient-to-r from-red-600 to-orange-500 hover:from-red-700 hover:to-orange-600 text-white shadow-md shadow-red-500/20 disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              <span className="hidden sm:inline">Ask</span>
            </Button>
          </div>
        </CardContent>
      )}
    </Card>
  );
};

export default CampaignChat;
