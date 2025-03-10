import { LanguageModelV1 } from 'ai';
import { openai } from '@ai-sdk/openai';
import { anthropic } from '@ai-sdk/anthropic';
import type { Participant } from '../../../types/types';

/**
 * Parses a language model from a string
 * @param model - The language model to parse
 * @returns The parsed language model
 */
export function parseLanguageModel(model: string): LanguageModelV1 {
    const parts = model.split(':');
    const provider = parts[0];
    const modelName = parts[1];
    
    if (provider === 'openai') {
        return openai(modelName);
    } else if (provider === 'anthropic') {
        return anthropic(modelName);
    } else {
        throw new Error(`Unsupported language model provider: ${provider}`);
    }
}
