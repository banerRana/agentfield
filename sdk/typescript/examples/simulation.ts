import dotenv from 'dotenv';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Agent } from '../src/agent/Agent.js';
import { AgentRouter } from '../src/router/AgentRouter.js';
import { z } from 'zod';

const __dirname = dirname(fileURLToPath(import.meta.url));
// Load .env from current working directory (e.g., sdk/typescript) first,
// then fall back to the project root when running from dist/.
dotenv.config({ path: resolve(process.cwd(), '.env') });
if (!process.env.OPENAI_API_KEY) {
  dotenv.config({ path: resolve(__dirname, '../../.env') });
}

console.log('Starting simulation example...');

const simulationRouter = new AgentRouter({ prefix: 'simulation' });

const SimulationResultSchema = z.object({
  scenario: z.string(),
  populationSize: z.number(),
  entities: z.array(z.any()),
  decisions: z.array(z.any()),
  insights: z.object({
    keyInsight: z.string(),
    outcomeDistribution: z.record(z.number())
  })
});
type SimulationResult = z.infer<typeof SimulationResultSchema>;

const SimulationInputSchema = z.object({
  scenario: z.string(),
  populationSize: z.number(),
  context: z.array(z.string()),
  parallelBatchSize: z.number().optional(),
  explorationRatio: z.number().optional(),
})
type SimulationInput = z.infer<typeof SimulationInputSchema>;

simulationRouter.reasoner<SimulationInput, SimulationResult>('runSimulation', async (ctx) => {
  const { scenario, populationSize, context = [], parallelBatchSize = 20 } = ctx.input;

  const scenarioAnalysis = await ctx.ai(`Analyze scenario: ${scenario}`);
  const factorGraph = await ctx.ai(`Build factor graph: ${scenarioAnalysis}`);

  await ctx.memory.set('last_scenario', { scenario, factorGraph });

  return {
    scenario,
    populationSize,
    entities: Array.from({ length: parallelBatchSize }).map((_, i) => ({ id: i })),
    decisions: [],
    insights: {
      keyInsight: 'Simulation complete',
      outcomeDistribution: { success: 0.8, failure: 0.2 }
    }
  };
});

simulationRouter.reasoner<{ scenario: string }, any>('decomposeScenario', async (ctx) => {
  return ctx.ai(`Decompose: ${ctx.input.scenario}`);
});

const agent = new Agent({
  nodeId: 'simulation-engine',
  // aiConfig: { model: 'gpt-4o', provider: 'openai', apiKey: process.env.OPENAI_API_KEY },
  aiConfig: {
    provider: 'openai', // OpenRouter is OpenAI-compatible
    model: 'openrouter/deepseek/deepseek-v3.1-terminus',
    apiKey: process.env.OPENROUTER_API_KEY,
    baseUrl: 'https://openrouter.ai/api/v1'
  },
  host: 'localhost',
  devMode: true
});

agent.includeRouter(simulationRouter);

agent.reasoner<{ message: string }, { echo: string }>('echo', async (ctx) => ({
  echo: ctx.input.message
}));

agent
  .serve()
  .then(() => {
    console.log('Simulation agent serving on port 8001');
  })
  .catch((err) => {
    console.error('Failed to start simulation agent', err);
    process.exit(1);
  });
