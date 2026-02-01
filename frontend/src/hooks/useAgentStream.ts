import { useState, useEffect, useCallback, useRef } from 'react';
import { wsService } from '../services/websocket';
import type { AgentEvent } from '../types';

interface AgentStreamStep {
  step: number;
  agent: string;
  data: Record<string, unknown>;
  timestamp: number;
}

export function useAgentStream(projectId: string | null) {
  const [steps, setSteps] = useState<AgentStreamStep[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [currentAgent, setCurrentAgent] = useState<string | null>(null);
  const [finalPost, setFinalPost] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [groundednessScore, setGroundednessScore] = useState<number | null>(null);
  const cleanupRef = useRef<(() => void) | null>(null);

  const subscribe = useCallback((runId: string) => {
    setSteps([]);
    setIsRunning(true);
    setFinalPost(null);
    setError(null);
    setGroundednessScore(null);

    wsService.connect();
    wsService.subscribe(runId);

    const handler = (event: AgentEvent) => {
      if (!event.data) return;
      const d = event.data;

      if (d.type === 'agent_step') {
        setCurrentAgent(d.agent || null);
        setSteps((prev) => [
          ...prev,
          {
            step: d.step || prev.length + 1,
            agent: d.agent || 'unknown',
            data: d as unknown as Record<string, unknown>,
            timestamp: Date.now(),
          },
        ]);
      }

      if (d.type === 'evaluation_complete') {
        setGroundednessScore(d.groundedness_score ?? null);
      }

      if (d.type === 'workflow_complete') {
        setIsRunning(false);
        setCurrentAgent(null);
        setFinalPost(d.final_post || null);
        setGroundednessScore(d.groundedness_score ?? null);
      }

      if (d.type === 'workflow_error') {
        setIsRunning(false);
        setCurrentAgent(null);
        setError(d.error || 'Unknown error occurred');
      }
    };

    const unsub = wsService.on(`run:${runId}`, handler);
    cleanupRef.current = () => {
      unsub();
      wsService.unsubscribe(runId);
    };
  }, []);

  const reset = useCallback(() => {
    cleanupRef.current?.();
    setSteps([]);
    setIsRunning(false);
    setCurrentAgent(null);
    setFinalPost(null);
    setError(null);
    setGroundednessScore(null);
  }, []);

  useEffect(() => {
    return () => {
      cleanupRef.current?.();
    };
  }, []);

  return { steps, isRunning, currentAgent, finalPost, error, groundednessScore, subscribe, reset };
}
